import axiosClient from '@/api/apiClient';
import axios from 'axios';

/**
 * Service for location-related API calls
 */

/**
 * Get all countries from REST Countries API
 * @returns {Promise<Object>} Response with countries data
 */
export const getCountries = async () => {
  try {
    // Use REST Countries API for comprehensive country list
    const response = await axios.get('https://restcountries.com/v3.1/all?fields=name,cca2,cca3');
    
    // Transform the data to match our expected format
    const countries = response.data
      .map(country => ({
        country_id: country.cca2, // Use ISO 2-letter code as ID
        country_code: country.cca3, // 3-letter code
        country_name: country.name.common,
        country_name_official: country.name.official
      }))
      .sort((a, b) => a.country_name.localeCompare(b.country_name));

    return {
      success: true,
      data: countries,
    };
  } catch (error) {
    console.error('Error fetching countries:', error);
    
    // Fallback to internal API if REST Countries fails
    try {
      const fallbackResponse = await axiosClient.get('/location/countries');
      return {
        success: true,
        data: fallbackResponse.data,
      };
    } catch (fallbackError) {
      return {
        success: false,
        error: 'Unable to fetch countries from any source',
      };
    }
  }
};

/**
 * Get cities by country ID
 * @param {number} countryId - The ID of the country
 * @returns {Promise<Object>} Response with cities data
 */
export const getCitiesByCountry = async (countryId) => {
  try {
    const response = await axiosClient.get(
      `/location/cities?country_id=${countryId}`
    );
    return {
      success: true,
      data: response.data,
    };
  } catch (error) {
    console.error('Error fetching cities:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message,
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
      data: response.data,
    };
  } catch (error) {
    console.error('Error fetching all cities:', error);
    return {
      success: false,
      error: error.response?.data?.detail || error.message,
    };
  }
};

/**
 * Validate city name using OpenStreetMap Nominatim API
 * @param {string} cityName - The city name to validate
 * @param {string} countryCode - The country code (ISO 2-letter)
 * @returns {Promise<Object>} Response with validation result
 */
export const validateCity = async (cityName, countryCode) => {
  if (!cityName || !countryCode) {
    return { success: false, error: 'City name and country code are required' };
  }

  try {
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: cityName,
        countrycodes: countryCode.toLowerCase(),
        limit: 1,
        format: 'json',
        featuretype: 'city'
      },
      headers: {
        'User-Agent': 'ELANORA-App/1.0'
      }
    });

    if (response.data && response.data.length > 0) {
      const result = response.data[0];
      return {
        success: true,
        data: {
          isValid: true,
          cityName: result.display_name.split(',')[0],
          fullName: result.display_name,
          coordinates: {
            lat: parseFloat(result.lat),
            lon: parseFloat(result.lon)
          }
        }
      };
    } else {
      return {
        success: true,
        data: {
          isValid: false,
          message: 'City not found in the specified country'
        }
      };
    }
  } catch (error) {
    console.error('Error validating city:', error);
    return {
      success: false,
      error: 'Unable to validate city'
    };
  }
};

/**
 * Validate postal code format and existence
 * @param {string} postalCode - The postal code to validate
 * @param {string} countryCode - The country code (ISO 2-letter)
 * @returns {Promise<Object>} Response with validation result
 */
export const validatePostalCode = async (postalCode, countryCode) => {
  if (!postalCode || !countryCode) {
    return { success: false, error: 'Postal code and country code are required' };
  }

  // Basic postal code format validation by country
  const postalCodePatterns = {
    'US': /^\d{5}(-\d{4})?$/,
    'CA': /^[A-Z]\d[A-Z] \d[A-Z]\d$/,
    'GB': /^[A-Z]{1,2}\d[A-Z\d]? \d[A-Z]{2}$/,
    'FR': /^\d{5}$/,
    'DE': /^\d{5}$/,
    'BE': /^\d{4}$/,
    'NL': /^\d{4} [A-Z]{2}$/,
    'IT': /^\d{5}$/,
    'ES': /^\d{5}$/,
    'PT': /^\d{4}-\d{3}$/,
    'CH': /^\d{4}$/,
    'AT': /^\d{4}$/,
    'SE': /^\d{3} \d{2}$/,
    'NO': /^\d{4}$/,
    'DK': /^\d{4}$/,
    'FI': /^\d{5}$/,
    'PL': /^\d{2}-\d{3}$/,
    'CZ': /^\d{3} \d{2}$/,
    'SK': /^\d{3} \d{2}$/,
    'HU': /^\d{4}$/,
    'RO': /^\d{6}$/,
    'BG': /^\d{4}$/,
    'HR': /^\d{5}$/,
    'SI': /^\d{4}$/,
    'LU': /^\d{4}$/,
    'IE': /^[A-Z]\d{2} [A-Z\d]{4}$/,
    'MT': /^[A-Z]{3} \d{4}$/,
    'CY': /^\d{4}$/,
    'EE': /^\d{5}$/,
    'LV': /^\d{4}$/,
    'LT': /^\d{5}$/,
    'JP': /^\d{3}-\d{4}$/,
    'KR': /^\d{5}$/,
    'CN': /^\d{6}$/,
    'IN': /^\d{6}$/,
    'AU': /^\d{4}$/,
    'NZ': /^\d{4}$/,
    'BR': /^\d{5}-\d{3}$/,
    'MX': /^\d{5}$/,
    'AR': /^\d{4}$/,
    'CL': /^\d{7}$/,
    'CO': /^\d{6}$/,
    'PE': /^\d{5}$/,
    'ZA': /^\d{4}$/,
    'EG': /^\d{5}$/,
    'MA': /^\d{5}$/,
    'TN': /^\d{4}$/,
    'DZ': /^\d{5}$/,
    'RU': /^\d{6}$/,
    'UA': /^\d{5}$/,
    'TR': /^\d{5}$/,
    'IL': /^\d{7}$/,
    'AE': /^\d{5}$/,
    'SA': /^\d{5}$/,
    'QA': /^\d{5}$/,
    'KW': /^\d{5}$/,
    'BH': /^\d{3,4}$/,
    'OM': /^\d{3}$/,
    'TH': /^\d{5}$/,
    'VN': /^\d{6}$/,
    'MY': /^\d{5}$/,
    'SG': /^\d{6}$/,
    'PH': /^\d{4}$/,
    'ID': /^\d{5}$/,
  };

  const pattern = postalCodePatterns[countryCode.toUpperCase()];
  
  if (!pattern) {
    // If no pattern exists for the country, accept any non-empty value
    return {
      success: true,
      data: {
        isValid: postalCode.trim().length > 0,
        message: postalCode.trim().length > 0 ? 'Format not validated for this country' : 'Postal code is required'
      }
    };
  }

  const isValid = pattern.test(postalCode.trim());
  
  return {
    success: true,
    data: {
      isValid,
      message: isValid ? 'Valid postal code format' : 'Invalid postal code format for this country'
    }
  };
};

/**
 * Validate street name (basic validation)
 * @param {string} streetName - The street name to validate
 * @returns {Object} Validation result
 */
export const validateStreetName = (streetName) => {
  if (!streetName || streetName.trim().length === 0) {
    return {
      isValid: false,
      message: 'Street name is required'
    };
  }

  if (streetName.trim().length < 2) {
    return {
      isValid: false,
      message: 'Street name must be at least 2 characters long'
    };
  }

  // Check for suspicious patterns
  if (/^\d+$/.test(streetName.trim())) {
    return {
      isValid: false,
      message: 'Street name cannot be only numbers'
    };
  }

  return {
    isValid: true,
    message: 'Valid street name'
  };
};

/**
 * Validate street number (basic validation)
 * @param {string} streetNumber - The street number to validate
 * @returns {Object} Validation result
 */
export const validateStreetNumber = (streetNumber) => {
  if (!streetNumber || streetNumber.trim().length === 0) {
    return {
      isValid: true, // Optional field
      message: 'Street number is optional'
    };
  }

  // Allow numbers, letters, and common separators (1, 1A, 1-3, 1/2, etc.)
  if (!/^[\d\w\-\/\s]+$/.test(streetNumber.trim())) {
    return {
      isValid: false,
      message: 'Street number contains invalid characters'
    };
  }

  return {
    isValid: true,
    message: 'Valid street number'
  };
};

/**
 * Validate complete address
 * @param {Object} address - The address object to validate
 * @returns {Promise<Object>} Response with validation results
 */
export const validateCompleteAddress = async (address) => {
  const results = {
    country: { isValid: !!address.countryId },
    city: { isValid: false },
    postalCode: { isValid: false },
    streetName: validateStreetName(address.streetName),
    streetNumber: validateStreetNumber(address.streetNumber),
  };

  // Validate city if country and city are provided
  if (address.countryId && address.cityName) {
    const cityValidation = await validateCity(address.cityName, address.countryId);
    if (cityValidation.success) {
      results.city = cityValidation.data;
    }
  }

  // Validate postal code if country and postal code are provided
  if (address.countryId && address.postalCode) {
    const postalValidation = await validatePostalCode(address.postalCode, address.countryId);
    if (postalValidation.success) {
      results.postalCode = postalValidation.data;
    }
  }

  return {
    success: true,
    data: results
  };
};
