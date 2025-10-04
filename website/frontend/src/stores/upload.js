import { defineStore } from 'pinia';
import { ref, watch, computed } from 'vue';

const STORAGE_KEY = 'uploadState';

function loadFromLocalStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : {};
  } catch (error) {
    console.error('Failed to load upload state from localStorage:', error);
    return {};
  }
}

function saveToLocalStorage(state) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch (error) {
    console.error('Failed to save upload state to localStorage:', error);
  }
}

export const useUploadStore = defineStore('upload', () => {
  const currentStep = ref(1); // 1: Upload, 2: Processing, 3: Assignment, 4: Confirm
  const selectedProject = ref(''); // Project ID as string
  const selectedFiles = ref([]);
  const extractedTiers = ref([]); // From backend
  const tierAssignments = ref({}); // e.g., { tierId: sectionId or 'new' }
  const newSectionNames = ref({}); // e.g., { 'tierName': 'Section Name' }
  const sessionId = ref(null); // From backend
  const description = ref('');
  const isProcessing = ref(false);
  const existingSections = ref([]); // Existing sections for assignment

  // Load initial state
  const initialState = loadFromLocalStorage();
  if (initialState.currentStep) currentStep.value = initialState.currentStep;
  if (initialState.selectedProject)
    selectedProject.value = initialState.selectedProject;
  if (initialState.extractedTiers)
    extractedTiers.value = initialState.extractedTiers;
  if (initialState.tierAssignments)
    tierAssignments.value = initialState.tierAssignments;
  if (initialState.sessionId) sessionId.value = initialState.sessionId;
  if (initialState.newSectionNames)
    newSectionNames.value = initialState.newSectionNames;
  if (initialState.existingSections)
    existingSections.value = initialState.existingSections;

  // Watch for changes and save
  watch(
    () => currentStep.value,
    (newStep, oldStep) => {
      console.log('[DEBUG] Upload store step changed:', { newStep, oldStep });
    }
  );

  watch(
    [
      currentStep,
      selectedProject,
      extractedTiers,
      tierAssignments,
      newSectionNames,
      sessionId,
      description,
      existingSections,
    ],
    () => {
      saveToLocalStorage({
        currentStep: currentStep.value,
        selectedProject: selectedProject.value,
        extractedTiers: extractedTiers.value,
        tierAssignments: tierAssignments.value,
        newSectionNames: newSectionNames.value,
        sessionId: sessionId.value,
        description: description.value,
        existingSections: existingSections.value,
      });
    },
    { deep: true }
  );

  const isStepValid = computed(() => {
    switch (currentStep.value) {
      case 1:
        return selectedFiles.value.length > 0 && selectedProject.value;
      case 2:
        return extractedTiers.value.length > 0;
      case 3:
        return Object.keys(tierAssignments.value).length > 0;
      case 4:
        return true; // Description is optional
      default:
        return false;
    }
  });

  function nextStep() {
    if (isStepValid.value) currentStep.value++;
  }

  function prevStep() {
    if (currentStep.value > 1) currentStep.value--;
  }

  function reset() {
    console.log('[DEBUG] Upload store reset called');
    currentStep.value = 1;
    selectedProject.value = '';
    selectedFiles.value = [];
    extractedTiers.value = [];
    tierAssignments.value = {};
    newSectionNames.value = {};
    sessionId.value = null;
    description.value = '';
    isProcessing.value = false;
    existingSections.value = [];
    localStorage.removeItem(STORAGE_KEY);
  }

  return {
    currentStep,
    selectedProject,
    selectedFiles,
    extractedTiers,
    tierAssignments,
    newSectionNames,
    sessionId,
    description,
    isProcessing,
    existingSections,
    isStepValid,
    nextStep,
    prevStep,
    reset,
  };
});
