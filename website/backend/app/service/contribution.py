"""Contribution Service - Handle collaborative ELAN file contributions."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
import git
from git import Repo

from app.core.centralized_logging import get_logger
from app.core.config import ELAN_PROJECTS_BASE_PATH
from app.service.elan import ElanService
from app.service.elan_merge import ElanMergeService
from app.service.elan_generator import ElanXmlGenerator
from app.utils.elan_processor import ElanFileCoordinator

logger = get_logger()


class ContributionError(Exception):
    """Custom exception for contribution workflow errors."""

    pass


class ContributionService:
    """Service for handling collaborative ELAN file contributions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.elan_service = ElanService(db)
        self.merge_service = ElanMergeService()
        self.xml_generator = ElanXmlGenerator()

    async def process_contribution_from_upload_session(
        self,
        session_id: str,
        contributor_username: str,
        tier_assignments: List[Dict[str, Any]],
        description: str,
    ) -> Dict[str, Any]:
        """Process contribution from completed upload session.

        This is called after the user confirms their upload in the frontend.

        Args:
            session_id: Upload session ID with staged data
            contributor_username: Username of contributor
            tier_assignments: List of tier assignment dicts from frontend
            description: Contribution description

        Returns:
            Dict with contribution results and branch information
        """
        logger.info(
            f"Processing contribution from session {session_id} by {contributor_username}"
        )

        try:
            # Step 1: Get upload session data
            session_data = await self._get_upload_session_data(session_id)

            # Step 2: Transform tier assignments to proper format
            tier_section_mappings = self._transform_tier_assignments(tier_assignments)

            # Step 3: Create contribution branch with smart naming
            branch_info = await self._create_contribution_branch(
                session_data["project_id"],
                session_data["target_filename"],
                contributor_username,
                tier_section_mappings,
                description,
            )

            # Step 4: Extract complete contributor data from staged files
            contributor_data = await self._extract_contributor_data_from_session(
                session_id
            )

            # Step 5: Get master data from database
            master_data = await self.elan_service.get_master_file_data_for_merge(
                session_data["target_filename"], session_data["project_id"]
            )

            if not master_data:
                raise ContributionError(
                    f"Master file {session_data['target_filename']} not found in project"
                )

            # Step 6: Perform preliminary merge
            merge_result = await self.merge_service.perform_preliminary_merge(
                contributor_data,
                master_data,
                contributor_username,
                tier_section_mappings,
            )

            # Step 7: Generate ELAN XML from merged data
            merged_xml = self.xml_generator.generate_elan_xml(
                merge_result["merged_data"]
            )

            # Step 8: Commit preliminary merge to contribution branch
            commit_info = await self._commit_preliminary_merge(
                session_data["project_id"],
                branch_info["branch_name"],
                session_data["target_filename"],
                merged_xml,
                merge_result,
                description,
            )

            # Step 9: Cleanup upload session (move from staged to contribution branch)
            await self._finalize_contribution_session(
                session_id, branch_info["branch_name"]
            )

            logger.info(
                f"Contribution processed successfully: {branch_info['branch_name']}"
            )

            return {
                "success": True,
                "branch_name": branch_info["branch_name"],
                "contribution_id": branch_info["contribution_id"],
                "commit_hash": commit_info["commit_hash"],
                "conflicts_detected": len(merge_result["conflicts"]) > 0,
                "conflicts": merge_result["conflicts"],
                "merge_summary": {
                    "tiers_added": len(merge_result["tiers_added"]),
                    "tiers_preserved": len(merge_result["tiers_preserved"]),
                    "conflicts": len(merge_result["conflicts"]),
                },
                "requires_admin_review": len(merge_result["conflicts"]) > 0,
            }

        except Exception as e:
            logger.error(f"Contribution processing failed: {e}")
            # TODO: Cleanup any created branches/commits on failure
            raise ContributionError(f"Contribution processing failed: {str(e)}")

    async def _get_upload_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get upload session data and determine target filename."""
        # This should get data from the upload session
        # For now, we'll simulate the expected structure
        # In reality, this would query the upload_session table

        from app.crud.upload_session import get_upload_session_by_id

        session = await get_upload_session_by_id(self.db, session_id)

        if not session:
            raise ContributionError(f"Upload session {session_id} not found")

        # Get the first file from the session to determine target filename
        # This is a simplification - in reality you might handle multiple files
        from app.crud.tier import get_tiers_by_session_id

        tiers = await get_tiers_by_session_id(self.db, session_id)

        if not tiers:
            raise ContributionError(f"No tiers found in session {session_id}")

        # Use the first tier's filename as target (assuming single file contribution)
        target_filename = f"{tiers[0].tier_name}.eaf"  # This is simplified

        return {
            "project_id": session.project_id,
            "target_filename": target_filename,
            "session": session,
            "tiers": tiers,
        }

    def _transform_tier_assignments(
        self, tier_assignments: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """Transform frontend tier assignments to section mappings."""
        tier_section_mappings = {}

        for assignment in tier_assignments:
            tier_name = assignment.get("tier_name") or assignment.get("tier_id")
            section_name = assignment.get("section_name")

            if tier_name and section_name:
                # For now, we'll use section_name as section_id
                # In reality, you'd look up the actual section_id
                tier_section_mappings[tier_name] = (
                    hash(section_name) % 1000
                )  # Simple hash for demo

        return tier_section_mappings

    async def _create_contribution_branch(
        self,
        project_id: int,
        filename: str,
        contributor_username: str,
        tier_section_assignments: Dict[str, int],
        description: str,
    ) -> Dict[str, Any]:
        """Create contribution branch with smart naming using GitPython.

        Branch naming convention:
        contrib/{contributor_username}/{timestamp}/{contribution_id}/{filename_no_ext}
        """
        contribution_id = str(uuid4())[:8]  # Short unique ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_no_ext = Path(filename).stem

        branch_name = f"contrib/{contributor_username}/{timestamp}/{contribution_id}/{filename_no_ext}"

        # Create metadata for the branch
        contribution_metadata = {
            "contribution_id": contribution_id,
            "contributor_username": contributor_username,
            "target_filename": filename,
            "project_id": project_id,
            "created_at": datetime.now().isoformat(),
            "tier_section_assignments": tier_section_assignments,
            "status": "pending_merge",
            "description": description,
        }

        # Get project path
        project_path = Path(ELAN_PROJECTS_BASE_PATH) / str(project_id)

        try:
            # Initialize Git repository if it doesn't exist
            try:
                repo = Repo(str(project_path))
            except git.InvalidGitRepositoryError:
                repo = Repo.init(str(project_path))
                logger.info(f"Initialized Git repository at {project_path}")

            # Create branch from master
            try:
                # Ensure we're on master
                master_branch = repo.heads.master
                master_branch.checkout()
            except:
                # Create master branch if it doesn't exist
                master_branch = repo.create_head("master")
                master_branch.checkout()

            # Create new contribution branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()

            # Add contribution metadata file
            metadata_file = project_path / ".contribution_metadata.json"
            with open(metadata_file, "w") as f:
                json.dump(contribution_metadata, f, indent=2)

            # Add and commit metadata file
            repo.index.add([str(metadata_file)])
            repo.index.commit(
                f"Initialize contribution branch for {filename} by {contributor_username}"
            )

            logger.info(f"Created contribution branch: {branch_name}")

            return {
                "branch_name": branch_name,
                "contribution_id": contribution_id,
                "metadata": contribution_metadata,
            }

        except Exception as e:
            logger.error(f"Failed to create contribution branch: {e}")
            raise ContributionError(f"Failed to create contribution branch: {str(e)}")

    async def _extract_contributor_data_from_session(
        self, session_id: str
    ) -> Dict[str, Any]:
        """Extract contributor data from upload session."""
        # This would get the staged files from the upload session
        # and use ElanFileCoordinator to extract complete data

        # For now, we'll create a mock structure
        # In reality, this would process the actual uploaded files

        contributor_data = {
            "metadata": {
                "author": "contributor",
                "date": datetime.now().isoformat(),
                "format": "3.0",
                "version": "3.0",
            },
            "time_slots": {},
            "media": [],
            "tiers": [],
            "linguistic_types": [],
            "properties": [],
        }

        # Get tiers from session
        from app.crud.tier import get_tiers_by_session_id

        session_tiers = await get_tiers_by_session_id(self.db, session_id)

        # Transform staged tiers to contributor format
        for tier in session_tiers:
            tier_data = {
                "tier_id": tier.tier_name,
                "annotations": [],
                "linguistic_type_ref": "default-lt",
            }
            contributor_data["tiers"].append(tier_data)

        logger.info(
            f"Extracted contributor data: {len(contributor_data['tiers'])} tiers"
        )
        return contributor_data

    async def _commit_preliminary_merge(
        self,
        project_id: int,
        branch_name: str,
        filename: str,
        merged_xml: str,
        merge_result: Dict[str, Any],
        description: str,
    ) -> Dict[str, Any]:
        """Commit the preliminary merge result to the contribution branch using GitPython."""
        project_path = Path(ELAN_PROJECTS_BASE_PATH) / str(project_id)

        try:
            repo = Repo(str(project_path))

            # Ensure we're on the right branch
            contrib_branch = repo.heads[branch_name]
            contrib_branch.checkout()

            # Write merged ELAN file
            elan_file_path = project_path / filename
            with open(elan_file_path, "w", encoding="utf-8") as f:
                f.write(merged_xml)

            # Create merge summary file for admin review
            merge_summary_path = (
                project_path / f".merge_summary_{Path(filename).stem}.json"
            )
            merge_summary = {
                "preliminary_merge_completed": datetime.now().isoformat(),
                "conflicts_detected": len(merge_result["conflicts"]),
                "conflicts": merge_result["conflicts"],
                "tiers_added": merge_result["tiers_added"],
                "tiers_preserved": merge_result["tiers_preserved"],
                "merge_statistics": merge_result.get("statistics", {}),
                "requires_admin_review": len(merge_result["conflicts"]) > 0,
                "description": description,
            }

            with open(merge_summary_path, "w") as f:
                json.dump(merge_summary, f, indent=2)

            # Add files to Git
            repo.index.add([str(elan_file_path), str(merge_summary_path)])

            # Create commit message
            commit_message = f"Preliminary merge: {filename}\n\n"
            commit_message += f"Description: {description}\n\n"
            commit_message += f"- Tiers added: {len(merge_result['tiers_added'])}\n"
            commit_message += (
                f"- Tiers preserved: {len(merge_result['tiers_preserved'])}\n"
            )
            commit_message += (
                f"- Conflicts detected: {len(merge_result['conflicts'])}\n"
            )

            if merge_result["conflicts"]:
                commit_message += "\nConflicts require admin review:\n"
                for conflict in merge_result["conflicts"]:
                    commit_message += f"- {conflict['tier_name']}: {conflict['type']}\n"

            # Commit the changes
            commit = repo.index.commit(commit_message)

            logger.info(
                f"Committed preliminary merge to {branch_name}: {commit.hexsha}"
            )

            return {
                "commit_hash": commit.hexsha,
                "merge_summary_file": str(merge_summary_path),
                "elan_file": str(elan_file_path),
            }

        except Exception as e:
            logger.error(f"Failed to commit preliminary merge: {e}")
            raise ContributionError(f"Failed to commit preliminary merge: {str(e)}")

    async def _finalize_contribution_session(
        self, session_id: str, branch_name: str
    ) -> None:
        """Clean up upload session after successful contribution creation."""
        try:
            # Update session status to indicate it's been converted to contribution
            from app.crud.upload_session import update_upload_session

            await update_upload_session(
                self.db,
                session_id,
                {
                    "status": "converted_to_contribution",
                    "contribution_branch": branch_name,
                },
            )

            # We keep the staged data for now in case we need to reference it
            # In production, you might want to clean it up after some time

            await self.db.commit()
            logger.info(f"Finalized contribution session {session_id} -> {branch_name}")

        except Exception as e:
            logger.error(f"Failed to finalize contribution session: {e}")
            # Don't raise here as the main contribution process succeeded

    @staticmethod
    def parse_contribution_branch_name(branch_name: str) -> Optional[Dict[str, Any]]:
        """Parse contribution branch name to extract metadata.

        Branch format: contrib/{username}/{timestamp}/{contribution_id}/{filename}
        """
        try:
            parts = branch_name.split("/")
            if len(parts) != 5 or parts[0] != "contrib":
                return None

            return {
                "contributor_username": parts[1],
                "timestamp": parts[2],
                "contribution_id": parts[3],
                "filename_stem": parts[4],
                "is_contribution_branch": True,
            }
        except Exception:
            return None

    async def list_pending_contributions(self, project_id: int) -> List[Dict[str, Any]]:
        """List all pending contributions for a project."""
        project_path = Path(ELAN_PROJECTS_BASE_PATH) / str(project_id)

        try:
            repo = Repo(str(project_path))
            contributions = []

            # Get all branches that match contribution pattern
            for branch in repo.heads:
                branch_info = self.parse_contribution_branch_name(branch.name)
                if branch_info:
                    # Switch to branch and get metadata
                    try:
                        branch.checkout()
                        metadata_file = project_path / ".contribution_metadata.json"

                        if metadata_file.exists():
                            with open(metadata_file) as f:
                                metadata = json.load(f)
                            branch_info.update(metadata)

                        contributions.append(branch_info)
                    except Exception as e:
                        logger.warning(
                            f"Could not read metadata for branch {branch.name}: {e}"
                        )
                        contributions.append(branch_info)

            # Switch back to master
            try:
                repo.heads.master.checkout()
            except:
                pass

            return sorted(
                contributions, key=lambda x: x.get("created_at", ""), reverse=True
            )

        except Exception as e:
            logger.error(f"Failed to list pending contributions: {e}")
            return []
