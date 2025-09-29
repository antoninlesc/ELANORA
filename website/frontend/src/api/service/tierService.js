import axiosInstance from '@/api/apiClient';

export async function fetchProjectTiers(projectName) {
  const response = await axiosInstance.get(
    `/tier/${encodeURIComponent(projectName)}`
  );
  return response.data;
}

export async function fetchSectionsAndGroups(projectId) {
  const response = await axiosInstance.get(`/tier/${projectId}/sections`);
  return response.data;
}

export async function createSection(
  projectId,
  name,
  isStaged = false,
  sessionId = null
) {
  const data = {
    project_id: projectId,
    name,
    is_staged: isStaged,
  };
  if (sessionId) {
    data.session_id = sessionId;
  }
  return axiosInstance.post('/tier/sections/create', data);
}

export async function renameSection(sectionId, newName, isStaged = false) {
  return axiosInstance.post('/tier/sections/rename', {
    section_id: sectionId,
    new_name: newName,
    is_staged: isStaged,
  });
}

export async function deleteSection(sectionId, isStaged = false) {
  return axiosInstance.post('/tier/sections/delete', {
    section_id: sectionId,
    is_staged: isStaged,
  });
}

export async function moveTierGroup(
  tierGroupId,
  sectionId,
  projectId,
  tierId,
  tierName,
  isStaged = false
) {
  return axiosInstance.post('/tier/tier_group/move', {
    tier_group_id: tierGroupId,
    section_id: sectionId,
    project_id: projectId,
    tier_id: tierId,
    tier_name: tierName,
    is_staged: isStaged,
  });
}

export const tierService = {
  fetchProjectTiers,
  fetchSectionsAndGroups,
  createSection,
  renameSection,
  deleteSection,
  moveTierGroup,
};

export default tierService;
