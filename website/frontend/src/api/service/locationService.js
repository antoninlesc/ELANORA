import axiosClient from '@/api/apiClient';

/**
 * Service for location-related API calls
 */

/**
 * Get all countries
 * @returns {Promise<Object>} Response with countries data
 */
export const getCountries = async () => {
  try {
    const response = await axiosClient.get('/location/countries');
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error fetching countries:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message
    };
  }
};

/**
 * Get cities by country ID
 * @param {number} countryId - The ID of the country
 * @returns {Promise<Object>} Response with cities data
 */
export const getCitiesByCountry = async (countryId) => {
  try {
    const response = await axiosClient.get(`/location/cities?country_id=${countryId}`);
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error fetching cities:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message
    };
  }
};

/**
 * Get all cities
 * @returns {Promise<Object>} Response with all cities data
 */
export const getAllCities = async () => {
  try {
    const response = await axiosClient.get('/location/cities/all');
    return {
      success: true,
      data: response.data
    };
  } catch (error) {
    console.error('Error fetching all cities:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message
    };
  }
};
