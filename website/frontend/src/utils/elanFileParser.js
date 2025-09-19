/**
 * Client-side ELAN file parser for extracting media information
 * This allows the frontend to parse ELAN files and extract media descriptors
 * for filename validation and rename suggestions
 */

// Cache for parsed ELAN files to avoid re-processing
const elanFileCache = new Map();

/**
 * Parse ELAN file content and extract media descriptors
 * @param {string} elanFileContent - The content of the ELAN file as a string
 * @returns {Array} Array of media descriptor objects
 */
export function extractMediaDescriptorsFromElan(elanFileContent) {
  if (!elanFileContent || typeof elanFileContent !== 'string') {
    console.warn('elanFileParser: Invalid ELAN file content provided');
    return [];
  }

  console.log(
    'elanFileParser: Parsing XML content, length:',
    elanFileContent.length
  );

  try {
    // Use a more efficient approach for large files
    // Instead of parsing the entire DOM, use regex to find MEDIA_DESCRIPTOR elements
    const mediaDescriptors = [];
    // Updated regex to handle self-closing tags: <MEDIA_DESCRIPTOR ... /> or <MEDIA_DESCRIPTOR>...</MEDIA_DESCRIPTOR>
    const mediaDescriptorRegex = /<MEDIA_DESCRIPTOR([^>]*)\/?>/gs;
    const attributeRegex = /(\w+)="([^"]*)"/g;

    let match;
    while ((match = mediaDescriptorRegex.exec(elanFileContent)) !== null) {
      const descriptorAttributes = match[1];
      const attributes = {};

      let attrMatch;
      while ((attrMatch = attributeRegex.exec(descriptorAttributes)) !== null) {
        attributes[attrMatch[1]] = attrMatch[2];
      }

      console.log(
        `elanFileParser: Processing MEDIA_DESCRIPTOR with URL: ${attributes.MEDIA_URL || 'none'}, MIME: ${attributes.MIME_TYPE || 'none'}`
      );

      const mediaInfoItem = {
        media_url: attributes.MEDIA_URL,
        mime_type: attributes.MIME_TYPE,
        relative_media_url: attributes.RELATIVE_MEDIA_URL,
      };

      // Only add if we have at least one URL
      if (mediaInfoItem.media_url || mediaInfoItem.relative_media_url) {
        mediaDescriptors.push(mediaInfoItem);
        console.log(`elanFileParser: Added media descriptor:`, mediaInfoItem);
      }
    }

    console.log(
      `elanFileParser: Found ${mediaDescriptors.length} media descriptors using regex parsing`
    );
    return mediaDescriptors;
  } catch (error) {
    console.error(
      'elanFileParser: Error parsing ELAN file with regex, falling back to DOM parsing:',
      error
    );

    // Fallback to DOM parsing for complex cases
    try {
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(elanFileContent, 'text/xml');

      const parserError = xmlDoc.querySelector('parsererror');
      if (parserError) {
        console.error(
          'elanFileParser: XML parsing error:',
          parserError.textContent
        );
        return [];
      }

      const mediaDescriptors = xmlDoc.querySelectorAll('MEDIA_DESCRIPTOR');
      console.log(
        'elanFileParser: Found',
        mediaDescriptors.length,
        'MEDIA_DESCRIPTOR elements (fallback)'
      );

      const mediaInfo = [];
      mediaDescriptors.forEach((descriptor) => {
        const mediaInfoItem = {
          media_url: descriptor.getAttribute('MEDIA_URL'),
          mime_type: descriptor.getAttribute('MIME_TYPE'),
          relative_media_url: descriptor.getAttribute('RELATIVE_MEDIA_URL'),
        };

        if (mediaInfoItem.media_url || mediaInfoItem.relative_media_url) {
          mediaInfo.push(mediaInfoItem);
        }
      });

      return mediaInfo;
    } catch (fallbackError) {
      console.error(
        'elanFileParser: Fallback DOM parsing also failed:',
        fallbackError
      );
      return [];
    }
  }
}

/**
 * Extract media filenames from media descriptors
 * @param {Array} mediaDescriptors - Array of media descriptor objects
 * @returns {Array} Array of media filenames
 */
export function extractMediaFilenames(mediaDescriptors) {
  if (!Array.isArray(mediaDescriptors)) {
    return [];
  }

  const filenames = [];

  mediaDescriptors.forEach((descriptor) => {
    let filename = null;

    // Try relative_media_url first, then media_url
    if (descriptor.relative_media_url) {
      filename = getFilenameFromUrl(descriptor.relative_media_url);
    } else if (descriptor.media_url) {
      // Handle file:// URLs
      if (descriptor.media_url.startsWith('file:///')) {
        const pathPart = descriptor.media_url.substring(8); // Remove 'file:///'
        filename = getFilenameFromUrl(pathPart);
      } else {
        filename = getFilenameFromUrl(descriptor.media_url);
      }
    }

    if (filename && !filenames.includes(filename)) {
      filenames.push(filename);
    }
  });

  return filenames;
}

/**
 * Extract filename from URL or path
 * @param {string} url - URL or file path
 * @returns {string|null} Filename or null if not found
 */
function getFilenameFromUrl(url) {
  if (!url) return null;

  try {
    // Remove query parameters and fragments
    const cleanUrl = url.split('?')[0].split('#')[0];

    // Get the last part after the last slash
    const parts = cleanUrl.split('/');
    const filename = parts[parts.length - 1];

    return filename || null;
  } catch (error) {
    console.error('Error extracting filename from URL:', error);
    return null;
  }
}

/**
 * Read ELAN file content from File object
 * @param {File} file - The ELAN file to read
 * @returns {Promise<string>} Promise that resolves to file content as string
 */
export function readElanFileContent(file) {
  return new Promise((resolve, reject) => {
    if (!file) {
      reject(new Error('No file provided'));
      return;
    }

    // Check if it's an ELAN file
    if (!file.name.toLowerCase().endsWith('.eaf')) {
      reject(new Error('File is not an ELAN file (.eaf)'));
      return;
    }

    const reader = new FileReader();

    reader.onload = (event) => {
      try {
        const content = event.target.result;
        resolve(content);
      } catch (error) {
        reject(new Error(`Error reading file content: ${error.message}`));
      }
    };

    reader.onerror = () => {
      reject(new Error('Error reading file'));
    };

    reader.readAsText(file);
  });
}

/**
 * Clear the ELAN file cache (useful for memory management)
 */
export function clearElanFileCache() {
  elanFileCache.clear();
  console.log('elanFileParser: Cache cleared');
}

/**
 * Get cache size for debugging
 */
export function getCacheSize() {
  return elanFileCache.size;
}

/**
 * Process ELAN file and extract media information
 * @param {File} file - The ELAN file to process
 * @returns {Promise<Object>} Promise that resolves to object with media info
 */
export async function processElanFileForMedia(file) {
  console.log(
    'elanFileParser: Processing file:',
    file.name,
    'size:',
    file.size
  );

  // Check cache first
  const cacheKey = `${file.name}-${file.size}-${file.lastModified}`;
  if (elanFileCache.has(cacheKey)) {
    console.log('elanFileParser: Using cached result for:', file.name);
    return elanFileCache.get(cacheKey);
  }

  try {
    console.log('elanFileParser: Reading file content...');
    const content = await readElanFileContent(file);
    console.log('elanFileParser: File content length:', content.length);

    console.log('elanFileParser: Extracting media descriptors...');
    const mediaDescriptors = extractMediaDescriptorsFromElan(content);
    console.log('elanFileParser: Found media descriptors:', mediaDescriptors);

    const mediaFilenames = extractMediaFilenames(mediaDescriptors);
    console.log('elanFileParser: Extracted media filenames:', mediaFilenames);

    const result = {
      filename: file.name,
      mediaDescriptors,
      mediaFilenames,
      hasMedia: mediaFilenames.length > 0,
    };

    // Cache the result
    elanFileCache.set(cacheKey, result);
    console.log('elanFileParser: Final result:', result);
    return result;
  } catch (error) {
    console.error('elanFileParser: Error processing file:', error);
    const errorResult = {
      filename: file.name,
      mediaDescriptors: [],
      mediaFilenames: [],
      hasMedia: false,
      error: error.message,
    };

    // Cache error results too to avoid repeated failures
    const cacheKey = `${file.name}-${file.size}-${file.lastModified}`;
    elanFileCache.set(cacheKey, errorResult);

    return errorResult;
  }
}
