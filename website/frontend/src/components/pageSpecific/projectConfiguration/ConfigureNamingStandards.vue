<template>
  <div class="configure-naming-page">
    <h2 class="configure-naming-title">Configure Naming Standards</h2>
    <div v-if="loading">Loading...</div>
    <div v-else>
      <div v-if="standards.length === 0">
        <em>No standards configured yet.</em>
      </div>
      <div>
        <div
          v-for="std in standards"
          :key="std.id"
          class="configure-naming-accordion"
          style="margin-bottom: 32px"
        >
          <div
            class="configure-naming-accordion-header"
            :class="{ open: openStandardId === std.id }"
            @click="toggleAccordion(std.id)"
          >
            <span class="configure-naming-accordion-title">
              {{ std.name
              }}<span v-if="getFileTypeDisplay(std.project_file_type_id)"
                >:
                <span class="configure-naming-accordion-filetype">{{
                  getFileTypeDisplay(std.project_file_type_id)
                }}</span></span
              >
            </span>
            <span
              class="configure-naming-accordion-chevron"
              :class="{ open: openStandardId === std.id }"
              >&#9660;</span
            >
          </div>
          <transition name="accordion">
            <div
              v-if="openStandardId === std.id"
              class="configure-naming-accordion-body"
            >
              <div
                v-if="std.description"
                class="configure-naming-accordion-desc-box"
              >
                <span class="configure-naming-desc-label">Description:</span>
                <span class="configure-naming-desc-content">{{
                  std.description
                }}</span>
              </div>
              <div class="configure-naming-pattern-example-label">
                Example filename:
              </div>
              <div class="configure-naming-pattern-example-value">
                <code>{{ buildExampleFilename(std) }}</code>
              </div>
              <div class="configure-naming-accordion-pattern">
                <div class="configure-naming-pattern-label">Pattern:</div>
                <div class="configure-naming-pattern-value">
                  {{ std.pattern }}
                </div>
                <div class="configure-naming-pattern-breakdown">
                  <div class="breakdown-title">Pattern Groups:</div>
                  <div class="breakdown-groups">
                    <template
                      v-for="comp in getPatternOrderedComponents(std)"
                      :key="comp.id || comp.name"
                    >
                      <span class="breakdown-group">
                        <span class="breakdown-group-name">{{
                          comp.name
                        }}</span>
                        <span class="breakdown-group-arrow">→</span>
                        <span class="breakdown-group-value">{{
                          buildExampleForRegex(comp.regex)
                        }}</span>
                      </span>
                    </template>
                  </div>
                </div>
              </div>
              <div class="configure-naming-accordion-components">
                <div class="configure-naming-components-title">Components</div>
                <table class="configure-naming-components-table">
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Regex</th>
                      <th>Example</th>
                      <th>Accepted Values</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="component in getPatternOrderedComponents(std)"
                      :key="component.id || component.name"
                    >
                      <td class="configure-naming-component-name">
                        {{ component.name }}
                      </td>
                      <td class="configure-naming-component-regex">
                        {{ component.regex }}
                      </td>
                      <td>{{ buildExampleForRegex(component.regex) }}</td>
                      <td>
                        <span
                          v-if="component.accepted_values && component.accepted_values.length"
                        >
                          {{
                            component.accepted_values
                              .map(val =>
                                typeof val === 'object' && val !== null && 'value' in val
                                  ? val.value
                                  : val
                              )
                              .join(', ')
                          }}
                        </span>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div class="configure-naming-accordion-actions">
                <button
                  class="configure-naming-btn"
                  @click="editStandard(std)"
                >
                  Edit
                </button>
                <button
                  class="configure-naming-btn delete"
                  @click="deleteStandard(std.id)"
                >
                  Delete
                </button>
              </div>
            </div>
          </transition>
        </div>
      </div>
      <button class="configure-naming-add-btn" @click="showAddStandard = true">
        + Add Standard
      </button>
      <div v-if="showAddStandard" class="configure-naming-add-form">
        <div class="configure-naming-add-title">Add Standard</div>
        <form class="configure-naming-add-fields" @submit.prevent="addStandard">
          <!-- Name -->
          <div class="configure-naming-form-row">
            <label for="standard-name">Name</label>
            <input
              id="standard-name"
              v-model="newStandard.name"
              placeholder="Unique standard name"
              required
            />
          </div>
          <!-- Description -->
          <div class="configure-naming-form-row">
            <label for="standard-desc">Description</label>
            <input
              id="standard-desc"
              v-model="newStandard.description"
              placeholder="Description"
            />
          </div>
          <!-- File type -->
          <div class="configure-naming-form-row">
            <label for="standard-filetype">File type</label>
            <select
              id="standard-filetype"
              v-model="newStandard.project_file_type_id"
              required
              @change="onFileTypeChange"
            >
              <option disabled value="">Select file type</option>
              <option v-for="ft in fileTypes" :key="ft.id" :value="ft.id">
                {{ ft.name }} ({{ ft.extension }}){{
                  ft.description ? ' — ' + ft.description : ''
                }}
              </option>
            </select>
          </div>
          <!-- Pattern: prefix + comma pattern -->
          <div class="configure-naming-form-row">
            <label for="pattern-comma-input">Pattern</label>
            <div class="configure-naming-pattern-row">
              <input
                class="configure-naming-prefix-box"
                :title="prefixValue"
                :value="prefixValue"
                readonly
                tabindex="-1"
              />
              <span class="configure-naming-pattern-sep">+</span>
              <input
                id="pattern-comma-input"
                v-model="commaPattern"
                class="configure-naming-pattern-box"
                :title="commaPattern"
                placeholder="Comma pattern (e.g. session,task,_,signer)"
                required
                @input="onCommaPatternInput"
              />
            </div>
          </div>
          <!-- Pattern example-->
          <div class="configure-naming-form-row">
            <div class="configure-naming-example-desc">
              <span class="configure-naming-accepted-separators">
                <b>Accepted separators</b>: {{ knownSeparators.map(s => `"${s}"`).join(', ') }}
              </span>
              <span>
                Example comma pattern for filename <b>CLSFBI1912A_S040_B</b>:
                <code class="configure-naming-example-comma-pattern">{{ exampleCommaPattern }}</code>
              </span>
            </div>
          </div>
          <!-- Example and extraction -->
          <div class="configure-naming-form-row">
            <label for="example-file-input">Example File</label>
            <div class="configure-naming-example-block">
              <input
                id="example-file-input"
                v-model="exampleFilename"
                placeholder="e.g. CLSFBI1912A_S040_B.mp4"
                class="configure-naming-example-input"
              />
              <button
                type="button"
                class="configure-naming-btn primary"
                @click="extractRegexFromExample"
              >
                Extract Regex
              </button>
            </div>
          </div>
          <!-- Components (optional, can be hidden or shown as needed) -->
          <div class="configure-naming-components-section">
            <label class="configure-naming-components-label" for="components-table">Components</label>
            <table
              id="components-table"
              class="configure-naming-components-table configure-naming-components-edit-table"
            >
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Regex</th>
                  <th>Description</th>
                  <th>Accepted Values</th>
                  <th>#</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(comp, idx) in newStandard.components"
                  :key="comp.name"
                  class="configure-naming-component-row"
                >
                  <td>
                    <input
                      v-model="comp.name"
                      placeholder="Component name"
                      :readonly="idx === 0 && comp.name.startsWith('prefix_')"
                      :class="{ 'configure-naming-components-table-prefix-disabled': idx === 0 && comp.name.startsWith('prefix_') }"
                      :tabindex="idx === 0 && comp.name.startsWith('prefix_') ? -1 : 0"
                    />
                  </td>
                  <td>
                    <input
                      v-model="comp.regex"
                      placeholder="Regex"
                      :readonly="idx === 0 && comp.name.startsWith('prefix_')"
                      :class="{ 'configure-naming-components-table-prefix-disabled': idx === 0 && comp.name.startsWith('prefix_') }"
                      :tabindex="idx === 0 && comp.name.startsWith('prefix_') ? -1 : 0"
                    />
                  </td>
                  <td>
                    <input
                      v-model="comp.description"
                      placeholder="Description"
                    />
                  </td>
                  <td>
                    <input
                      v-if="showAcceptedValuesInput(comp)"
                      v-model="comp.accepted_values_str"
                      :placeholder="getAcceptedValuesPlaceholder(comp)"
                      :title="getAcceptedValuesPlaceholder(comp)"
                      @input="onAcceptedValuesInput(comp)"
                    />
                  </td>
                  <td>
                    <span class="configure-naming-component-order"
                      >#{{ comp.order }}</span
                    >
                  </td>
                </tr>
              </tbody>
            </table>
            <div
              v-if="shouldShowAcceptedValuesWarning"
              class="configure-naming-warning"
              style="margin-top: 4px"
            >
              <span>
                <b>Note:</b> You entered [<code>{{ detectedUnusualAcceptedValue }}</code>] as an accepted value. This will be saved as a single value. 
                To save multiple accepted values, separate them with a <b>comma</b> <code>,</code> or <b>semicolon</b> <code>;</code> (e.g. <code>B,A,W</code> or <code>B;A;W</code>).
              </span>
            </div>
            <div
              v-if="regexExtractionError"
              class="configure-naming-error"
              style="margin-top: 4px"
            >
              {{ regexExtractionError }}
            </div>
          </div>
          <div class="configure-naming-form-actions">
            <button
              class="configure-naming-btn add"
              type="submit"
              :disabled="!!regexExtractionError"
            >
              Add
            </button>
            <button
              class="configure-naming-btn"
              type="button"
              @click="resetAddForm"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
    <UserPrompt
      v-model="userPromptVisible"
      :message="userPromptMessage"
      :default-value="userPromptDefault"
      @submit="handleUserPromptSubmit"
      @cancel="handleUserPromptCancel"
    />
  </div>
</template>

<script setup>
import UserPrompt from '@components/common/UserPrompt.vue';
import projectNamingStandardApi from '@/api/service/projectNamingStandard.js';
import { ref, onMounted, watch, computed } from 'vue';
import { useProjectStore } from '@/stores/project';
import { useFileTypeStore } from '@stores/fileType';

const projectStore = useProjectStore();
const projectId = projectStore.currentProject?.project_id;

const loading = ref(true);
const standards = ref([]);
const allComponentNames = ref([]);
const showAddStandard = ref(false);
const newStandard = ref({
  name: '',
  project_file_type_id: '',
  pattern: '',
  description: '',
  components: [],
});

const userPromptVisible = ref(false);
const userPromptMessage = ref('');
const userPromptDefault = ref('');
let userPromptResolve = null;

function showUserPrompt(message, defaultValue = '') {
  userPromptMessage.value = message;
  userPromptDefault.value = defaultValue;
  userPromptVisible.value = true;
  return new Promise((resolve) => {
    userPromptResolve = resolve;
  });
}
function handleUserPromptSubmit(val) {
  userPromptVisible.value = false;
  if (userPromptResolve) userPromptResolve(val);
}
function handleUserPromptCancel() {
  userPromptVisible.value = false;
  if (userPromptResolve) userPromptResolve(null);
}

function showAcceptedValuesInput(comp) {
  if (comp.name.startsWith('prefix_')) return true;
  return comp.type === 'L' || comp.type === 'l' || comp.type === 'D';
}

function onAcceptedValuesInput(comp) {
  regexExtractionError.value = '';
  if (typeof comp.accepted_values_str === 'string') {
    let length = null;
    let isDigitRegex = false;
    if (comp.regex) {
      const match = comp.regex.match(/\\d\{(\d+)\}/);
      if (match) {
        length = parseInt(match[1]);
        isDigitRegex = true;
      }
    }
    let inputParts = comp.accepted_values_str.split(/[,;]/).map(s => s.trim()).filter(Boolean);

    if (isDigitRegex) {
      let normalizedParts = [];
      for (let part of inputParts) {
        if (/^\d+-\d+$/.test(part)) {
          let [start, end] = part.split('-').map(Number);
          if (isNaN(start) || isNaN(end) || start > end) {
            regexExtractionError.value = `Invalid range "${part}" for "${comp.name}".`;
            return;
          }
          // Pad both start and end
          let startStr = start.toString().padStart(length, '0');
          let endStr = end.toString().padStart(length, '0');
          // Check if padded values fit the regex length
          if (startStr.length > length || endStr.length > length) {
            regexExtractionError.value = `Values in range "${part}" exceed ${length} digits for "${comp.name}".`;
            return;
          }
          normalizedParts.push(`${startStr}-${endStr}`);
        } else if (/^\d+$/.test(part)) {
          let numStr = Number(part).toString().padStart(length, '0');
          if (numStr.length > length) {
            regexExtractionError.value = `Value "${part}" exceeds ${length} digits for "${comp.name}".`;
            return;
          }
          normalizedParts.push(numStr);
        } else {
          regexExtractionError.value = `Invalid value "${part}" for "${comp.name}".`;
          return;
        }
      }
      comp.accepted_values = normalizedParts;
      // Optionally, update the input field to show the normalized version:
      comp.accepted_values_str = normalizedParts.join(', ');
      return;
    }

    // For non-digit regexes, expand and validate as before
    let values = [];
    for (let part of inputParts) {
      values.push(part);
    }
    values = [...new Set(values)];

    // Validate length for letter regexes
    if (length !== null) {
      for (const val of values) {
        if (val.length !== length) {
          regexExtractionError.value = `All accepted values for "${comp.name}" must be exactly ${length} characters long.`;
          return;
        }
      }
    }

    // Validate each value against the regex
    if (comp.regex) {
      let regexStr = comp.regex;
      let re;
      try {
        re = new RegExp('^' + regexStr + '$');
      } catch {
        regexExtractionError.value = `Invalid regex for "${comp.name}".`;
        return;
      }
      for (const val of values) {
        if (!re.test(val)) {
          regexExtractionError.value = `Accepted value "${val}" does not match regex "${comp.regex}" for "${comp.name}".`;
          return;
        }
      }
    }

    comp.accepted_values = values;
  } else {
    comp.accepted_values = [];
  }
}

// Remove unused getFileTypeName
function getFileTypeNameRaw(project_file_type_id) {
  const ft = fileTypes.value.find((f) => f.id === project_file_type_id);
  return ft ? ft.name : '';
}

function getFileTypeDisplay(project_file_type_id) {
  const ft = fileTypes.value.find((f) => f.id === project_file_type_id);
  if (!ft) return '';
  return `${ft.name} (${ft.extension})${ft.description ? ' — ' + ft.description : ''}`;
}

const fileTypes = ref([]);
const exampleFilename = ref('');
const regexExtractionError = ref('');
const commaPattern = ref('');
const exampleCommaPattern =
  'session,task,letter1,_,signer_letter,signer_digits,_,camera';
const knownSeparators = ['_', '-', '.', ' '];

async function fetchStandardsAndComponentNames() {
  loading.value = true;
  try {
    const { data } = await projectNamingStandardApi.getProjectNamingStandardsFull(projectId);
    // Flatten standards to a single object with components
    standards.value = Array.isArray(data.standards)
      ? data.standards.map(s => ({
          ...s.standard,
          components: s.components || [],
        }))
      : [];
    allComponentNames.value = Array.isArray(data.component_names) ? data.component_names : [];
    // Ensure accepted_values_str for editing
    for (const std of standards.value) {
      if (std.components) {
        std.components = std.components.map((c) => ({
          ...c,
          accepted_values: c.accepted_values || [],
          accepted_values_str: (c.accepted_values || []).join(', '),
        }));
      }
    }
  } finally {
    loading.value = false;
  }
}

function extractComponentsFromPattern(pattern) {
  // Match all {component_name} in the pattern
  const matches = pattern.matchAll(/\{(\w+)\}/g);
  const components = [];
  let order = 1;
  for (const match of matches) {
    components.push({
      name: match[1],
      regex: '',
      description: '',
      order: order++,
      accepted_values: [],
      accepted_values_str: '',
    });
  }
  return components;
}

function onCommaPatternInput() {
  const fileType = getFileTypeNameRaw(newStandard.value.project_file_type_id);
  if (!commaPattern.value || !fileType) {
    newStandard.value.pattern = '';
    newStandard.value.components = [];
    return;
  }
  const parts = commaPattern.value.split(',').map((p) => p.trim());
  let pattern = `{prefix_${fileType}}`;
  let components = [
    {
      name: `prefix_${fileType}`,
      regex: '',
      description: '',
      order: 1,
      accepted_values: [],
      accepted_values_str: '',
    },
  ];
  let order = 2;
  for (const part of parts) {
    if (knownSeparators.includes(part)) {
      pattern += part;
    } else {
      pattern += `{${part}}`;
      components.push({
        name: part,
        regex: '',
        description: '',
        order: order++,
        accepted_values: [],
        accepted_values_str: '',
      });
    }
  }
  newStandard.value.pattern = pattern;
  newStandard.value.components = components;
}

async function extractRegexFromExample() {
  regexExtractionError.value = '';
  const pattern = newStandard.value.pattern;
  const example = exampleFilename.value;
  if (!pattern || !example) {
    regexExtractionError.value = 'Pattern and example file are required.';
    return;
  }

  // Split pattern and example into blocks using known separators
  const separators = ['_', '-', '.', ' '];
  let sep = separators.find((s) => pattern.includes(s));
  if (!sep) sep = '_'; // fallback

  function splitPatternBlocks(pattern, sep) {
    let blocks = [];
    let current = '';
    let depth = 0;
    for (const c of pattern) {
      if (c === '{') depth++;
      if (c === '}') depth--;
      if (c === sep && depth === 0) {
        blocks.push(current);
        current = '';
      } else {
        current += c;
      }
    }
    if (current) blocks.push(current);
    return blocks;
  }

  function splitTypeGroups(str) {
    if (!str) return [];
    let groups = [];
    let current = str[0];
    let type = getCharType(str[0]);
    for (let i = 1; i < str.length; i++) {
      const t = getCharType(str[i]);
      if (t === type) {
        current += str[i];
      } else {
        groups.push(current);
        current = str[i];
        type = t;
      }
    }
    groups.push(current);
    return groups;
  }
  function getCharType(c) {
    if (/[A-Z]/.test(c)) return 'L';
    if (/[a-z]/.test(c)) return 'l';
    if (/\d/.test(c)) return 'D';
    return 'O'; // Other
  }

  const patternBlocks = splitPatternBlocks(pattern, sep);
  const exampleBlocks = example.split(sep);

  if (patternBlocks.length !== exampleBlocks.length) {
    regexExtractionError.value =
      'Pattern and example do not have the same number of blocks.';
    return;
  }

  const comps = extractComponentsFromPattern(pattern);

  for (let blockIdx = 0; blockIdx < patternBlocks.length; blockIdx++) {
    const patBlock = patternBlocks[blockIdx];
    const exBlock = exampleBlocks[blockIdx];

    // Extract component names in this block
    const blockCompNames = [];
    const matches = patBlock.matchAll(/\{(\w+)\}/g);
    for (const m of matches) blockCompNames.push(m[1]);
    if (blockCompNames.length === 0) continue;

    // Special handling for prefix: always extract all leading same-type chars
    if (blockCompNames[0].startsWith('prefix_')) {
      const comp = comps.find((c) => c.name === blockCompNames[0]);
      let prefix = '';
      for (const char of exBlock) {
        if (/[A-Z]/.test(char)) prefix += char;
        else break;
      }
      assignRegexAndAcceptable(comp, prefix);
      // Remove prefix from exBlock for further processing if more comps in block
      if (blockCompNames.length > 1) {
        await processBlockIterative(
          blockCompNames.slice(1),
          exBlock.slice(prefix.length)
        );
      }
      continue;
    }

    await processBlockIterative(blockCompNames, exBlock);
  }

  // Iterative version of processBlockComponents
  async function processBlockIterative(compNames, str) {
    if (!compNames.length || !str) return;
    let typeGroups = splitTypeGroups(str);
    let compIdx = 0;
    let groupIdx = 0;

    while (compIdx < compNames.length && groupIdx < typeGroups.length) {
      // If number of remaining components > number of remaining type groups,
      // prompt for the length for the current component from the current type group.
      if (compNames.length - compIdx > typeGroups.length - groupIdx) {
        let remaining = typeGroups[groupIdx].length;
        let compsLeft = compNames.length - compIdx;
        let len = await showUserPrompt(
          `Ambiguous block "${typeGroups[groupIdx]}": Please specify the length for component "${compNames[compIdx]}"`,
          Math.floor(remaining / compsLeft)
        );
        len = parseInt(len);
        if (!len || isNaN(len) || len < 1 || len > remaining) {
          regexExtractionError.value = `Invalid length for "${compNames[compIdx]}".`;
          return;
        }
        const val = typeGroups[groupIdx].slice(0, len);
        assignRegexAndAcceptable(
          comps.find((c) => c.name === compNames[compIdx]),
          val
        );

        // Update the type group with the remaining part
        typeGroups[groupIdx] = typeGroups[groupIdx].slice(len);
        if (!typeGroups[groupIdx]) {
          groupIdx++;
        }
        compIdx++;
        continue;
      }

      // If enough type groups left for components, assign directly
      if (compNames.length - compIdx === typeGroups.length - groupIdx) {
        for (; compIdx < compNames.length; compIdx++, groupIdx++) {
          const comp = comps.find((c) => c.name === compNames[compIdx]);
          assignRegexAndAcceptable(comp, typeGroups[groupIdx]);
        }
        return;
      }

      // Otherwise, assign type group to component
      const comp = comps.find((c) => c.name === compNames[compIdx]);
      assignRegexAndAcceptable(comp, typeGroups[groupIdx]);
      compIdx++;
      groupIdx++;
    }
  }

  // Set accepted_values_str for editing
  for (const comp of comps) {
    comp.accepted_values_str = (comp.accepted_values || []).join(', ');
  }

  newStandard.value.components = comps;

  function assignRegexAndAcceptable(comp, val) {
    if (!comp) return;

    // Helper to collapse runs of the same type into {n} notation
    function collapseRegex(str) {
      let out = '';
      let i = 0;
      while (i < str.length) {
        let c = str[i];
        let charClass = '';
        if (/[A-Z]/.test(c)) charClass = '[A-Z]';
        else if (/[a-z]/.test(c)) charClass = '[a-z]';
        else if (/\d/.test(c)) charClass = '\\d';
        else charClass = c.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        let run = 1;
        while (
          i + run < str.length &&
          ((/[A-Z]/.test(c) && /[A-Z]/.test(str[i + run])) ||
            (/[a-z]/.test(c) && /[a-z]/.test(str[i + run])) ||
            (/\d/.test(c) && /\d/.test(str[i + run])) ||
            c === str[i + run])
        ) {
          run++;
        }
        if (
          run > 1 &&
          (charClass === '[A-Z]' ||
            charClass === '[a-z]' ||
            charClass === '\\d')
        ) {
          out += `${charClass}{${run}}`;
        } else {
          out += charClass.repeat(run);
        }
        i += run;
      }
      return out;
    }

    // Assign type
    if (/^[A-Z]+$/.test(val)) comp.type = 'L';
    else if (/^[a-z]+$/.test(val)) comp.type = 'l';
    else if (/^\d+$/.test(val)) comp.type = 'D';
    else comp.type = 'O';

    // Prefix: accept only the full string, regex matches length and case
    if (comp.name.startsWith('prefix_')) {
      comp.regex = collapseRegex(val);
      comp.accepted_values = [val];
      comp.accepted_values_str = val;
      comp.type = 'L'; // Prefix is always uppercase letters in your use case
      return;
    }

    // Letters (case sensitive, length 1 or more)
    if (comp.type === 'L' || comp.type === 'l') {
      comp.regex = collapseRegex(val);
      comp.accepted_values = [val];
      comp.accepted_values_str = val;
      return;
    }

    // Digits
    if (comp.type === 'D') {
      comp.regex = collapseRegex(val);
      comp.accepted_values = [];
      comp.accepted_values_str = '';
      return;
    }

    // Fallback
    comp.regex = '.+';
    comp.accepted_values = [];
    comp.accepted_values_str = '';
  }
}

async function addStandard() {
  if (regexExtractionError.value) return;
  try {
    await projectNamingStandardApi.createStandardWithComponents({
      project_id: projectId,
      name: newStandard.value.name,
      project_file_type_id: newStandard.value.project_file_type_id,
      pattern: newStandard.value.pattern,
      description: newStandard.value.description,
      components: newStandard.value.components.map((c) => ({
        name: c.name,
        regex: c.regex,
        description: c.description,
        order: c.order,
        accepted_values: c.accepted_values,
        project_file_type_id: newStandard.value.project_file_type_id,
      })),
    });
    showAddStandard.value = false;
    newStandard.value = {
      name: '',
      project_file_type_id: '',
      pattern: '',
      description: '',
      components: [],
    };
    commaPattern.value = '';
    exampleFilename.value = '';
    await fetchStandardsAndComponentNames();
  } catch (err) {
    if (err?.response?.status === 409) {
      alert(err?.response?.data?.detail);
    } else {
      alert(
        'Failed to add standard.' +
          (err?.response?.data?.detail ? '\n' + err.response.data.detail : '')
      );
    }
  }
}

async function deleteStandard(id) {
  if (!confirm('Delete this standard?')) return;
  try {
    await projectNamingStandardApi.deleteStandard(id);
    await fetchStandardsAndComponentNames();
  } catch {
    alert('Failed to delete standard.');
  }
}

function editStandard() {
  alert('Edit not implemented in this example.');
}

const fileTypeStore = useFileTypeStore();

onMounted(async () => {
  await fileTypeStore.fetchFileTypes();
  await fetchStandardsAndComponentNames();
});

watch(
  () => newStandard.value.project_file_type_id,
  (newVal, oldVal) => {
    if (newVal !== oldVal) {
      commaPattern.value = '';
      newStandard.value.pattern = '';
      newStandard.value.components = [];
    }
  }
);

watch(
  () => fileTypeStore.fileTypes,
  () => {
    fileTypes.value = [...fileTypeStore.fileTypes];
  },
  { immediate: true }
);

watch(
  () => newStandard.value,
  () => {},
  { deep: true }
);

const openStandardId = ref(null);
function toggleAccordion(id) {
  openStandardId.value = openStandardId.value === id ? null : id;
}

function buildExampleForRegex(regex) {
  // Very basic examples for common regexes
  if (!regex) return '';
  if (/\\d\{\d+\}/.test(regex)) {
    // e.g. \d{3}
    const len = parseInt(regex.match(/\\d\{(\d+)\}/)?.[1] || '1');
    return '1'.repeat(len);
  }
  if (/\[A-Z\]\{\d+\}/.test(regex)) {
    // e.g. [A-Z]{2}
    const len = parseInt(regex.match(/\[A-Z\]\{(\d+)\}/)?.[1] || '1');
    return 'A'.repeat(len);
  }
  if (/\[a-zA-Z\]\{\d+\}/.test(regex)) {
    const len = parseInt(regex.match(/\[a-zA-Z\]\{(\d+)\}/)?.[1] || '1');
    return 'Ab'.repeat(Math.ceil(len / 2)).slice(0, len);
  }
  if (regex === '.+') return 'abc';
  return 'X';
}

/**
 * Returns components in the order they appear in the pattern string.
 * This ensures pattern groups and table rows match the pattern order.
 */
function getPatternOrderedComponents(std) {
  if (!std?.pattern || !Array.isArray(std.components)) return [];
  // Extract component names in order from the pattern
  const names = Array.from(std.pattern.matchAll(/\{(\w+)\}/g)).map(m => m[1]);
  // Map names to actual component objects
  return names
    .map(name => std.components.find(c => c.name === name))
    .filter(Boolean);
}

/**
 * Returns the example filename for a standard, including the file extension.
 */
function buildExampleFilename(std) {
  let filename = std.pattern;
  const orderedComps = getPatternOrderedComponents(std);
  if (!orderedComps.length) return filename;
  for (const comp of orderedComps) {
    filename = filename.replace(
      new RegExp(`\\{${comp.name}\\}`, 'g'),
      buildExampleForRegex(comp.regex)
    );
  }
  // Add extension if available
  const ft = fileTypes.value.find(f => f.id === std.project_file_type_id);
  if (ft && ft.extension) {
    // Ensure extension starts with a dot
    const ext = ft.extension.startsWith('.') ? ft.extension : '.' + ft.extension;
    filename += ext;
  }
  return filename;
}

// Computed prefix value for the pattern
const prefixValue = computed(() => {
  const ft = fileTypes.value.find(
    (f) => f.id === newStandard.value.project_file_type_id
  );
  return ft ? `prefix_${ft.name}` : '';
});

function onFileTypeChange() {
  // Reset pattern and components when file type changes
  commaPattern.value = '';
  newStandard.value.pattern = '';
  newStandard.value.components = [];
}

function resetAddForm() {
  showAddStandard.value = false;
  newStandard.value = {
    name: '',
    project_file_type_id: '',
    pattern: '',
    description: '',
    components: [],
  };
  commaPattern.value = '';
  exampleFilename.value = '';
  regexExtractionError.value = '';
}

// Detect if any accepted_values_str looks like "B A W" (single value, multiple tokens separated by space)
const detectedUnusualAcceptedValue = computed(() => {
  for (const comp of newStandard.value.components) {
    if (
      typeof comp.accepted_values_str === 'string' &&
      comp.accepted_values_str.trim() &&
      // Only one value, but contains spaces (and not commas/semicolons)
      !comp.accepted_values_str.includes(',') &&
      !comp.accepted_values_str.includes(';') &&
      comp.accepted_values_str.trim().split(/\s+/).length > 1
    ) {
      return comp.accepted_values_str.trim();
    }
  }
  return '';
});

const shouldShowAcceptedValuesWarning = computed(() => !!detectedUnusualAcceptedValue.value);

function getAcceptedValuesPlaceholder(comp) {
  if (comp.name.startsWith('prefix_') && comp.regex && /\[A-Z\]\{(\d+)\}/.test(comp.regex)) {
    // Example: [A-Z]{6}
    return 'e.g. CLSFBI or CLSFBI, CLSFAE';
  }
  if (comp.regex && /\\d\{(\d+)\}/.test(comp.regex)) {
    // Example: \d{2}
    return 'e.g. 15, 1-50, 01-50';
  }
  if (comp.regex && /\[A-Z\]\{(\d+)\}/.test(comp.regex)) {
    // Example: [A-Z]{2}
    return 'e.g. AB, AC, BA';
  }
  // Default
  return 'e.g. B or B, A, W';
}
</script>

<style scoped>
.configure-naming-page {
  width: 100%;
  height: 100%;
  font-family: 'Segoe UI', Arial, sans-serif;
  display: flex;
  flex-direction: column;
}

.configure-naming-title {
  font-size: 2.2rem;
  font-weight: 700;
  margin-bottom: 32px;
  color: #2a2a2a;
  padding: 0 0 16px;
}

.configure-naming-accordion {
  margin-bottom: 18px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 4px #0001;
}

.configure-naming-accordion-header {
  padding: 14px 18px;
  font-size: 1.1rem;
  font-weight: 500;
  background: #e9eef5;
  border-radius: 8px 8px 0 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  user-select: none;
  transition: background 0.2s;
}

.configure-naming-accordion-header.open {
  background: #dbe7fa;
}

.configure-naming-accordion-chevron {
  font-size: 1.2rem;
  transition: transform 0.2s;
}

.configure-naming-accordion-chevron.open {
  transform: rotate(180deg);
}

.configure-naming-accordion-body {
  padding: 18px 22px 22px;
  background: #f7fafd;
  border-radius: 0 0 8px 8px;
}

.configure-naming-accordion-desc-box {
  background: #f3f6fa;
  border-left: 4px solid #3b82f6;
  padding: 10px 18px;
  margin-bottom: 14px;
  border-radius: 6px;
  color: #2a2a2a;
  font-size: 1.08rem;
  display: flex;
  gap: 8px;
  align-items: center;
}

.configure-naming-desc-label {
  font-weight: 600;
  color: #2563eb;
}

.configure-naming-desc-content {
  color: #444;
}

.configure-naming-accordion-pattern {
  margin-bottom: 10px;
}

.configure-naming-pattern-label,
.configure-naming-pattern-example-label {
  font-weight: 600;
  color: #444;
}

.configure-naming-pattern-value,
.configure-naming-pattern-example-value {
  margin-bottom: 4px;
  color: #2a2a2a;
}

.configure-naming-pattern-breakdown {
  margin-top: 10px;
  margin-bottom: 10px;
}

.breakdown-title {
  font-weight: 600;
  color: #444;
  margin-bottom: 4px;
}

.breakdown-groups {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.breakdown-group {
  background: #e9eef5;
  border-radius: 5px;
  padding: 4px 10px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.98rem;
}

.breakdown-group-name {
  font-weight: 600;
  color: #2563eb;
}

.breakdown-group-arrow {
  color: #888;
}

.breakdown-group-value {
  color: #222;
  font-family: monospace;
}

.configure-naming-accordion-components {
  margin-bottom: 10px;
}

.configure-naming-components-title {
  font-weight: 600;
  margin-bottom: 6px;
}

.configure-naming-components-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}

.configure-naming-components-table th,
.configure-naming-components-table td {
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
  text-align: left;
}

.configure-naming-components-table th {
  background: #f3f6fa;
  font-weight: 600;
}

.configure-naming-component-order {
  color: #888;
  font-size: 0.95em;
  margin-left: 8px;
}

.configure-naming-accordion-actions {
  margin-top: 12px;
  display: flex;
  gap: 10px;
}

.configure-naming-btn {
  background: #3b82f6;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 7px 18px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.18s;
}

.configure-naming-btn.delete {
  background: #e74c3c;
}

.configure-naming-btn.add {
  background: #10b981;
}

.configure-naming-btn.primary {
  background: #2563eb;
}

.configure-naming-btn:hover {
  filter: brightness(1.08);
}

.configure-naming-add-btn {
  background: #10b981;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 10px 26px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s;
  display: block;
  margin: 2rem auto;
}

.configure-naming-add-btn:hover {
  background: #059669;
}

.configure-naming-add-form {
  margin-top: 32px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px #0002;
  padding: 32px 36px 28px;
  margin-left: auto;
  margin-right: auto;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.configure-naming-add-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #2563eb;
  text-align: center;
  margin-bottom: 2rem;
  letter-spacing: 0.5px;
}

.configure-naming-add-fields {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.configure-naming-form-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.configure-naming-form-row label {
  width: 110px;
  font-weight: 500;
  color: #333;
  flex-shrink: 0;
}

.configure-naming-form-row input,
.configure-naming-form-row select {
  flex: 1;
  padding: 7px 10px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  font-size: 1rem;
  background: #f9fafb;
}

.configure-naming-pattern-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.configure-naming-prefix-box {
  background: #f3f6fa;
  color: #2563eb;
  font-weight: 600;
  border: 1.5px solid #2563eb;
  border-radius: 5px;
  font-size: 1rem;
  max-width: fit-content;
  cursor: not-allowed;
  caret-color: transparent;
}

.configure-naming-pattern-sep {
  color: #888;
  font-size: 1.2em;
  font-weight: 700;
}

.configure-naming-pattern-box {
  flex: 2.5;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  padding: 7px 10px;
  font-size: 1rem;
  background: #fff;
}

.configure-naming-example-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.configure-naming-example-desc {
  color: #888;
  font-size: 0.98em;
  margin-bottom: 2rem;
}

.configure-naming-example-input {
  padding: 7px 10px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  font-size: 1rem;
  background: #fff;
  margin-bottom: 4px;
}

.configure-naming-error {
  color: #e74c3c;
  font-size: 0.98em;
  margin-top: 2px;
  margin-left: 8px;
}

.configure-naming-components-edit-table input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 1rem;
  background: #f9fafb;
  box-sizing: border-box;
}

.configure-naming-components-edit-table td {
  vertical-align: middle;
  padding: 6px 10px;
}

.configure-naming-components-edit-table th,
.configure-naming-components-edit-table td {
  border: 1px solid #e0e0e0;
}

.configure-naming-components-edit-table th {
  background: #f3f6fa;
  font-weight: 600;
  color: #2563eb;
}

.configure-naming-components-edit-table {
  margin-top: 8px;
  margin-bottom: 8px;
  width: 100%;
  border-radius: 6px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 4px #0001;
}

.configure-naming-components-label {
  font-weight: 600;
  color: #444;
  margin-bottom: 6px;
  display: block;
  font-size: 1.08rem;
}

.configure-naming-form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 16px;
}

.configure-naming-components-table-prefix-disabled {
  background: #f3f6fa !important;
  color: #aaa !important;
  cursor: not-allowed !important;
  pointer-events: auto !important;
}

.configure-naming-accepted-separators {
  margin-left: 2rem;
  margin-right: 2.1rem;
}

.configure-naming-example-comma-pattern {
  margin-left: 20rem;
}

@media (width <= 700px) {
  .configure-naming-add-form {
    padding: 18px 6vw;
    max-width: 98vw;
  }

  .configure-naming-form-row label {
    width: 90px;
    font-size: 0.98em;
  }
}
</style>
