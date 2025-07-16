import os
from pathlib import Path
from app.core.centralized_logging import get_logger

logger = get_logger()


def create_project_structure(project_path: Path):
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "elan_files").mkdir(exist_ok=True)
    logger.info(f"Created project structure at {project_path}")


def create_gitignore(project_path: Path):
    gitignore_content = "*\n!.gitignore\n!README.md\n!elan_files/\n!elan_files/*.eaf\n"
    file_path = project_path / ".gitignore"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(gitignore_content)
    logger.info(f"Created .gitignore at {file_path}")


def create_readme(project_path: Path, project_name: str):
    readme_content = f"# {project_name}\n\nThis is the ELAN project '{project_name}'.\n"
    file_path = project_path / "README.md"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(readme_content)
    logger.info(f"Created README.md for project '{project_name}' at {file_path}")


def copy_githooks(project_path: Path, project_name: str):
    central_githooks = project_path.parent / ".githooks"
    hooks_dir = project_path / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0
    for hook_file in central_githooks.iterdir():
        if hook_file.is_file():
            hook_name = hook_file.name
            hook_dest = hooks_dir / hook_name
            with open(hook_file, encoding="utf-8") as f:
                hook_content = f.read()
            hook_content = (
                hook_content.replace("{{REPO_NAME}}", project_name)
                .replace("{{WORK_TREE}}", str(project_path))
                .replace("{{GIT_DIR}}", str(project_path / ".git"))
            )
            with open(hook_dest, "w", encoding="utf-8") as f:
                f.write(hook_content)
            os.chmod(hook_dest, 0o775)
            logger.info(f"Copied git hook '{hook_name}' to {hook_dest}")
            copied_count += 1
    logger.info(f"Copied {copied_count} git hooks to {hooks_dir}")
