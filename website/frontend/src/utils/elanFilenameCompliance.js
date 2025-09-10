/**
 * ELAN-specific filename compliance checker
 * This handles the .eaf extension properly, unlike the generic isFilenameCompliant function
 * which removes any extension and might incorrectly process filenames with dots
 */

/**
 * Check if an ELAN filename complies with the given naming standard
 * @param {Object} standard - The naming standard to check against
 * @param {string} filename - The filename to check (may include .eaf extension)
 * @returns {boolean} true if compliant, false otherwise
 */
export function isElanFilenameCompliant(standard, filename) {
  if (!standard?.pattern || !Array.isArray(standard?.components)) {
    return false; // Require valid standard
  }

  if (!filename || !filename.trim()) {
    return false;
  }

  // Only remove .eaf extension specifically
  let filenameForCompliance = filename.trim();
  if (filenameForCompliance.toLowerCase().endsWith('.eaf')) {
    filenameForCompliance = filenameForCompliance.slice(0, -4);
  }

  console.log('ELAN compliance check for:', filenameForCompliance, 'with standard:', standard);

  // Process components
  const components = standard.components.map((c) => {
    let acceptedValues = [];
    if (Array.isArray(c.acceptedValues)) {
      acceptedValues = c.acceptedValues;
    } else if (Array.isArray(c.accepted_values)) {
      acceptedValues = c.accepted_values;
    } else if (typeof c.accepted_values_str === 'string') {
      acceptedValues = c.accepted_values_str.split(',').map(s => s.trim()).filter(Boolean);
    }

    return {
      ...c,
      name: c.name,
      regex: c.regex ?? c.pattern ?? null,
      acceptedValues,
      fixedValue: c.fixedValue ?? c.fixed_value ?? c.value ?? null,
      numericRange: c.numericRange ?? c.numeric_range ?? (c.numericRangeValue ?? null),
    };
  });

  // Build regex pattern
  let pattern = standard.pattern;
  for (const comp of components) {
    const compRegex = comp.regex || '.+';
    pattern = pattern.replace(new RegExp(`\\{${comp.name}\\}`, 'g'), `(${compRegex})`);
  }

  // Test pattern
  let topRx;
  try {
    topRx = new RegExp(`^${pattern}$`, 'u');
  } catch (error) {
    console.log('Invalid regex pattern:', error);
    return false;
  }

  const match = topRx.exec(filenameForCompliance);
  console.log('Pattern match result:', match);
  
  if (!match) {
    console.log('Filename does not match pattern');
    return false;
  }

  // Validate each component
  for (const [i, comp] of components.entries()) {
    const value = match[i + 1];
    
    // Check fixed value
    if (comp.fixedValue != null && String(comp.fixedValue) !== String(value)) {
      console.log(`Component ${comp.name} failed fixed value check: expected ${comp.fixedValue}, got ${value}`);
      return false;
    }

    // Check accepted values
    if (Array.isArray(comp.acceptedValues) && comp.acceptedValues.length > 0) {
      const valueMatches = comp.acceptedValues.some(av => {
        if (av == null) return false;
        
        // Check regex patterns
        if (typeof av === 'string' && /^\/.*\/[gimsuy]*$/.test(av)) {
          try {
            const parts = /^\/(.*)\/([gimsuy]*)$/.exec(av);
            const r = new RegExp(parts[1], parts[2]);
            return r.test(value);
          } catch {
            return false;
          }
        }
        
        // Check ranges (e.g., "001-999")
        if (typeof av === 'string' && /^\d+-\d+$/.test(av.trim())) {
          const [minStr, maxStr] = av.trim().split('-');
          const min = Number(minStr);
          const max = Number(maxStr);
          const num = Number(value);
          if (!isNaN(num) && value.length === minStr.length) {
            return num >= min && num <= max;
          }
        }
        
        // Direct string match
        return String(av) === value;
      });
      
      if (!valueMatches) {
        console.log(`Component ${comp.name} failed accepted values check: ${value} not in`, comp.acceptedValues);
        return false;
      }
    }

    // Check numeric range (object format)
    if (comp.numericRange && typeof comp.numericRange === 'object') {
      const num = Number(value);
      if (isNaN(num)) {
        console.log(`Component ${comp.name} failed numeric range check: ${value} is not a number`);
        return false;
      }
      
      if (typeof comp.numericRange.width === 'number' && String(value).length !== comp.numericRange.width) {
        console.log(`Component ${comp.name} failed width check: expected ${comp.numericRange.width}, got ${String(value).length}`);
        return false;
      }
      
      if (typeof comp.numericRange.min === 'number' && num < comp.numericRange.min) {
        console.log(`Component ${comp.name} below minimum: ${num} < ${comp.numericRange.min}`);
        return false;
      }
      
      if (typeof comp.numericRange.max === 'number' && num > comp.numericRange.max) {
        console.log(`Component ${comp.name} above maximum: ${num} > ${comp.numericRange.max}`);
        return false;
      }
    }

    // Check regex pattern
    if (comp.regex) {
      try {
        const regex = new RegExp(comp.regex, 'u');
        if (!regex.test(value)) {
          console.log(`Component ${comp.name} failed regex check: ${value} does not match ${comp.regex}`);
          return false;
        }
      } catch (error) {
        console.log(`Component ${comp.name} invalid regex:`, error);
        return false;
      }
    }
  }

  console.log('ELAN compliance check passed');
  return true;
}
