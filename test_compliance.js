/ Quick test of the ELAN filename compliance function
import { isElanFilenameCompliant } from './website/frontend/src/utils/elanFilenameCompliance.js';

// Mock naming standard (simplified version)
const mockStandard = {
  pattern: '{corpus}_{session}',
  components: [
    {
      name: 'corpus',
      regex: 'CLSFB\\d{4}[A-Z]?',
      acceptedValues: null
    },
    {
      name: 'session',
      regex: 'S\\d{3}',
      acceptedValues: null
    }
  ]
};

console.log('Testing ELAN filename compliance...');

// These should FAIL
console.log('CLSFB1912_S040.74556:', isElanFilenameCompliant(mockStandard, 'CLSFB1912_S040.74556'));
console.log('CLSFB1912_S040.eafazerazer45465:', isElanFilenameCompliant(mockStandard, 'CLSFB1912_S040.eafazerazer45465'));

// These should PASS
console.log('CLSFB1912_S040:', isElanFilenameCompliant(mockStandard, 'CLSFB1912_S040'));
console.log('CLSFB1912_S040.eaf:', isElanFilenameCompliant(mockStandard, 'CLSFB1912_S040.eaf'));
console.log('CLSFB1912A_S040.eaf:', isElanFilenameCompliant(mockStandard, 'CLSFB1912A_S040.eaf'));
