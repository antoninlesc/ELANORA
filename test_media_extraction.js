// Test script to verify media-based filename extraction
import { extractComponentsFromMedia, generateSuggestedFilename } from './website/frontend/src/utils/filenameFromMediaFile.js';

// Your sample data
const testFile = {
  "name": "Annotation_S040.eaf",
  "media_filenames": ["CLSFBI1912A_S040_B.mp4"],
  "elan_id": 706
};

// Media standard (location 3 - elanMedia)
const mediaStandard = {
  pattern: "{prefix_ELAN Media}{session}{task}{question_answer}_{signer_letter}{signer_digits}_{camera_angle}",
  components: [
    { name: "prefix_ELAN Media", regex: "\\p{L}{6}", order: 1 },
    { name: "session", regex: "\\p{N}{2}", order: 2 },
    { name: "task", regex: "\\p{N}{2}", order: 3 },
    { name: "question_answer", regex: "\\p{L}{1}", order: 4 },
    { name: "signer_letter", regex: "\\p{L}{1}", order: 5 },
    { name: "signer_digits", regex: "\\p{N}{3}", order: 6 },
    { name: "camera_angle", regex: "\\p{L}{1}", order: 7 }
  ]
};

// Project files standard (location 1 - projectFiles)
const projectStandard = {
  pattern: "{prefix_ELAN Files}{session}{task}_{signer_letter}{signer_digits}",
  components: [
    { name: "prefix_ELAN Files", regex: "\\p{L}{5}", order: 1 },
    { name: "session", regex: "\\p{N}{2}", order: 2 },
    { name: "task", regex: "\\p{N}{2}", order: 3 },
    { name: "signer_letter", regex: "\\p{L}{1}", order: 4 },
    { name: "signer_digits", regex: "\\p{N}{3}", order: 5 }
  ]
};

console.log("Testing media extraction...");
console.log("Media file:", testFile.media_filenames[0]);

// Extract components from media
const extractedComponents = extractComponentsFromMedia(testFile.media_filenames, mediaStandard);
console.log("Extracted components:", extractedComponents);

// Expected output:
// {
//   prefix_ELAN Media: "CLSFBI",
//   session: "19", 
//   task: "12",
//   question_answer: "A",
//   signer_letter: "S",
//   signer_digits: "040",
//   camera_angle: "B"
// }

// Generate suggested filename
const suggestedName = generateSuggestedFilename(extractedComponents, projectStandard);
console.log("Suggested ELAN filename:", suggestedName);

// Expected output: "CLSFB1912_S040.eaf"
