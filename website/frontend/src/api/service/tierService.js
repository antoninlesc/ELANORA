import axios from 'axios';

export async function fetchProjectTiers(projectName) {
  const response = await axios.get(
    `/api/v1/tier/${encodeURIComponent(projectName)}`
  );
  return response.data;
}
