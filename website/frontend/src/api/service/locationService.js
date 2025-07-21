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
    // Search for the city using Nominatim API
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: `${cityName}, ${countryCode}`,
        countrycodes: countryCode.toLowerCase(),
        limit: 10, // Get more results to filter better
        format: 'json',
        addressdetails: 1 // Get detailed address info for better validation
      },
      headers: {
        'User-Agent': 'ELANORA-App/1.0'
      }
    });

    if (response.data && response.data.length > 0) {
      // Filter results to ensure the city actually belongs to the specified country
      const validResults = response.data.filter(result => {
        const address = result.address;
        if (!address) return false;
        
        // Check if the result is actually in the specified country
        const resultCountryCode = address.country_code?.toUpperCase();
        if (resultCountryCode !== countryCode.toUpperCase()) {
          return false;
        }
        
        // Check if it's actually a city/town/village
        const isCity = address.city || address.town || address.village || address.municipality;
        if (!isCity) return false;
        
        // Check if the city name matches (case insensitive)
        const resultCityName = address.city || address.town || address.village || address.municipality;
        return resultCityName && resultCityName.toLowerCase() === cityName.toLowerCase();
      });

      if (validResults.length > 0) {
        const bestResult = validResults[0];
        const address = bestResult.address;
        const resultCityName = address.city || address.town || address.village || address.municipality;
        
        return {
          success: true,
          data: {
            isValid: true,
            cityName: resultCityName,
            fullName: bestResult.display_name,
            coordinates: {
              lat: parseFloat(bestResult.lat),
              lon: parseFloat(bestResult.lon)
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
 * Validate postal code against city using Nominatim API
 * @param {string} postalCode - The postal code to validate
 * @param {string} cityName - The city name
 * @param {string} countryCode - The country code (ISO 2-letter)
 * @returns {Promise<Object>} Response with validation result
 */
export const validatePostalCodeInCity = async (postalCode, cityName, countryCode) => {
  if (!postalCode || !cityName || !countryCode) {
    return { 
      success: false, 
      error: 'Postal code, city name, and country code are required' 
    };
  }

  try {
    // Search by postal code first
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        postalcode: postalCode,
        countrycodes: countryCode.toLowerCase(),
        limit: 10,
        format: 'json',
        addressdetails: 1
      },
      headers: {
        'User-Agent': 'ELANORA-App/1.0'
      }
    });

    if (response.data && response.data.length > 0) {
      // Check if any result matches our city
      const validResults = response.data.filter(result => {
        const address = result.address;
        if (!address) return false;
        
        const resultCity = address.city || address.town || address.village || address.municipality;
        return resultCity && resultCity.toLowerCase() === cityName.toLowerCase();
      });

      if (validResults.length > 0) {
        return {
          success: true,
          data: {
            isValid: true,
            message: 'Postal code matches the specified city'
          }
        };
      } else {
        // Get the cities that do match this postal code
        const actualCities = response.data
          .map(r => r.address?.city || r.address?.town || r.address?.village || r.address?.municipality)
          .filter(Boolean)
          .slice(0, 3);

        return {
          success: true,
          data: {
            isValid: false,
            message: actualCities.length > 0 
              ? `Postal code belongs to: ${actualCities.join(', ')}`
              : 'Postal code does not match the specified city',
            suggestions: actualCities
          }
        };
      }
    } else {
      return {
        success: true,
        data: {
          isValid: false,
          message: 'Postal code not found'
        }
      };
    }
  } catch (error) {
    console.error('Error validating postal code in city:', error);
    return {
      success: false,
      error: 'Unable to validate postal code'
    };
  }
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
 * Validate street name against city using Nominatim API
 * @param {string} streetName - The street name to validate
 * @param {string} cityName - The city name
 * @param {string} countryCode - The country code (ISO 2-letter)
 * @returns {Promise<Object>} Response with validation result
 */
export const validateStreetInCity = async (streetName, cityName, countryCode) => {
  if (!streetName || !cityName || !countryCode) {
    return { 
      success: false, 
      error: 'Street name, city name, and country code are required' 
    };
  }

  try {
    // Search for the street in the specific city
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: `${streetName}, ${cityName}`,
        countrycodes: countryCode.toLowerCase(),
        limit: 5,
        format: 'json',
        addressdetails: 1
      },
      headers: {
        'User-Agent': 'ELANORA-App/1.0'
      }
    });

    if (response.data && response.data.length > 0) {
      // Check if any result matches our city
      const validResults = response.data.filter(result => {
        const address = result.address;
        if (!address) return false;
        
        const resultCity = address.city || address.town || address.village || address.municipality;
        return resultCity && resultCity.toLowerCase() === cityName.toLowerCase();
      });

      if (validResults.length > 0) {
        return {
          success: true,
          data: {
            isValid: true,
            message: 'Street found in the specified city',
            suggestions: validResults.map(r => r.display_name)
          }
        };
      } else {
        return {
          success: true,
          data: {
            isValid: false,
            message: 'Street not found in the specified city',
            suggestions: response.data.map(r => r.display_name).slice(0, 3)
          }
        };
      }
    } else {
      return {
        success: true,
        data: {
          isValid: false,
          message: 'Street not found'
        }
      };
    }
  } catch (error) {
    console.error('Error validating street in city:', error);
    return {
      success: false,
      error: 'Unable to validate street'
    };
  }
};

/**
 * Validate street number against street and city using Nominatim API
 * @param {string} streetNumber - The street number to validate
 * @param {string} streetName - The street name
 * @param {string} cityName - The city name
 * @param {string} countryCode - The country code (ISO 2-letter)
 * @returns {Promise<Object>} Response with validation result
 */
export const validateStreetNumberInStreet = async (streetNumber, streetName, cityName, countryCode) => {
  if (!streetNumber || !streetName || !cityName || !countryCode) {
    return { 
      success: true, 
      data: { 
        isValid: true, 
        message: 'Street number validation skipped - missing required fields' 
      } 
    };
  }

  try {
    // Search for the complete address including street number
    const fullAddress = `${streetNumber} ${streetName}, ${cityName}`;
    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: fullAddress,
        countrycodes: countryCode.toLowerCase(),
        limit: 10,
        format: 'json',
        addressdetails: 1
      },
      headers: {
        'User-Agent': 'ELANORA-App/1.0'
      }
    });

    if (response.data && response.data.length > 0) {
      // Check if any result matches our complete address
      const validResults = response.data.filter(result => {
        const address = result.address;
        if (!address) return false;
        
        const resultCity = address.city || address.town || address.village || address.municipality;
        const resultStreet = address.road || address.pedestrian || address.footway;
        const resultNumber = address.house_number;
        
        const cityMatches = resultCity && resultCity.toLowerCase() === cityName.toLowerCase();
        const streetMatches = resultStreet && resultStreet.toLowerCase().includes(streetName.toLowerCase());
        const numberMatches = resultNumber && resultNumber === streetNumber;
        
        return cityMatches && streetMatches && numberMatches;
      });

      if (validResults.length > 0) {
        return {
          success: true,
          data: {
            isValid: true,
            message: 'Street number found at this address',
            suggestions: validResults.map(r => r.display_name)
          }
        };
      } else {
        // Check if street exists but number is wrong
        const streetExistsResults = response.data.filter(result => {
          const address = result.address;
          if (!address) return false;
          
          const resultCity = address.city || address.town || address.village || address.municipality;
          const resultStreet = address.road || address.pedestrian || address.footway;
          
          const cityMatches = resultCity && resultCity.toLowerCase() === cityName.toLowerCase();
          const streetMatches = resultStreet && resultStreet.toLowerCase().includes(streetName.toLowerCase());
          
          return cityMatches && streetMatches;
        });

        if (streetExistsResults.length > 0) {
          const existingNumbers = streetExistsResults
            .map(r => r.address?.house_number)
            .filter(Boolean)
            .slice(0, 5);
          
          return {
            success: true,
            data: {
              isValid: false,
              message: existingNumbers.length > 0 
                ? `Street number not found. Existing numbers: ${existingNumbers.join(', ')}`
                : 'Street number not found at this address',
              suggestions: existingNumbers
            }
          };
        } else {
          return {
            success: true,
            data: {
              isValid: false,
              message: 'Street not found for number validation'
            }
          };
        }
      }
    } else {
      return {
        success: true,
        data: {
          isValid: false,
          message: 'Address not found'
        }
      };
    }
  } catch (error) {
    console.error('Error validating street number:', error);
    return {
      success: false,
      error: 'Unable to validate street number'
    };
  }
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
    crossValidation: {
      streetInCity: { isValid: null, message: '', loading: false },
      postalCodeInCity: { isValid: null, message: '', loading: false }
    }
  };

  // Validate city if country and city are provided
  if (address.countryId && address.cityName) {
    const cityValidation = await validateCity(address.cityName, address.countryId);
    if (cityValidation.success) {
      results.city = cityValidation.data;
    }
  }

  // Validate postal code format if country and postal code are provided
  if (address.countryId && address.postalCode) {
    const postalValidation = await validatePostalCode(address.postalCode, address.countryId);
    if (postalValidation.success) {
      results.postalCode = postalValidation.data;
    }
  }

  // Cross-validation: Street in City
  if (address.streetName && address.cityName && address.countryId) {
    const streetInCityValidation = await validateStreetInCity(
      address.streetName, 
      address.cityName, 
      address.countryId
    );
    if (streetInCityValidation.success) {
      results.crossValidation.streetInCity = streetInCityValidation.data;
    }
  }

  // Cross-validation: Postal Code in City
  if (address.postalCode && address.cityName && address.countryId) {
    const postalInCityValidation = await validatePostalCodeInCity(
      address.postalCode, 
      address.cityName, 
      address.countryId
    );
    if (postalInCityValidation.success) {
      results.crossValidation.postalCodeInCity = postalInCityValidation.data;
    }
  }

  return {
    success: true,
    data: results
  };
};

/**
 * Validate complete address with full geocoding verification
 * @param {Object} address - The address object to validate
 * @returns {Promise<Object>} Response with detailed validation and geocoding
 */
export const validateAndGeocodeAddress = async (address) => {
  if (!address.streetName || !address.cityName || !address.countryId) {
    return {
      success: false,
      error: 'Street name, city name, and country code are required for full validation'
    };
  }

  try {
    // Build the full address string
    const fullAddress = [
      address.streetNumber,
      address.streetName,
      address.cityName,
      address.postalCode
    ].filter(Boolean).join(' ');

    const response = await axios.get('https://nominatim.openstreetmap.org/search', {
      params: {
        q: fullAddress,
        countrycodes: address.countryId.toLowerCase(),
        limit: 1,
        format: 'json',
        addressdetails: 1
      },
      headers: {
        'User-Agent': 'ELANORA-App/1.0'
      }
    });

    if (response.data && response.data.length > 0) {
      const result = response.data[0];
      const resultAddress = result.address;
      
      // Extract components from the result
      const resultStreet = resultAddress.road || resultAddress.pedestrian || resultAddress.footway;
      const resultCity = resultAddress.city || resultAddress.town || resultAddress.village || resultAddress.municipality;
      const resultPostalCode = resultAddress.postcode;
      const resultCountry = resultAddress.country_code?.toUpperCase();

      // Check matches
      const validation = {
        isValid: true,
        confidence: 'high',
        coordinates: {
          lat: parseFloat(result.lat),
          lon: parseFloat(result.lon)
        },
        matches: {
          street: resultStreet ? resultStreet.toLowerCase().includes(address.streetName.toLowerCase()) : false,
          city: resultCity ? resultCity.toLowerCase() === address.cityName.toLowerCase() : false,
          postalCode: resultPostalCode ? resultPostalCode === address.postalCode : true, // Don't fail if no postal code in result
          country: resultCountry === address.countryId.toUpperCase()
        },
        standardized: {
          streetName: resultStreet || address.streetName,
          cityName: resultCity || address.cityName,
          postalCode: resultPostalCode || address.postalCode,
          fullAddress: result.display_name
        }
      };

      // Calculate overall validity
      const matchCount = Object.values(validation.matches).filter(Boolean).length;
      const totalChecks = Object.keys(validation.matches).length;
      
      if (matchCount === totalChecks) {
        validation.confidence = 'high';
      } else if (matchCount >= totalChecks * 0.75) {
        validation.confidence = 'medium';
      } else {
        validation.confidence = 'low';
        validation.isValid = false;
      }

      return {
        success: true,
        data: validation
      };
    } else {
      return {
        success: true,
        data: {
          isValid: false,
          confidence: 'none',
          message: 'Address not found'
        }
      };
    }
  } catch (error) {
    console.error('Error validating and geocoding address:', error);
    return {
      success: false,
      error: 'Unable to validate address'
    };
  }
};
