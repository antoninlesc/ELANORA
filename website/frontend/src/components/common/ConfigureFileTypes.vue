<template>
  <div class="configure-filetypes-page">
    <h2 class="configure-filetypes-title">Configure File Types</h2>
    <div v-if="isLoading" class="configure-filetypes-loading">Loading...</div>
    <div v-else>
      <div v-if="fileTypes.length === 0" class="configure-filetypes-empty">
        <em>No file types defined yet.</em>
      </div>
      <table v-if="fileTypes.length" class="configure-filetypes-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Extension</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ft in fileTypes" :key="ft.id">
            <td>
              <template v-if="editId === ft.id">
                <input
                  v-model="editFileType.name"
                  class="edit-highlight"
                  autofocus
                  @keydown.enter="saveEdit(ft.id)"
                  @keydown.esc="cancelEdit"
                />
              </template>
              <template v-else>
                {{ ft.name }}
              </template>
            </td>
            <td>
              <template v-if="editId === ft.id">
                <input
                  v-model="editFileType.extension"
                  class="edit-highlight"
                  @keydown.enter="saveEdit(ft.id)"
                  @keydown.esc="cancelEdit"
                />
              </template>
              <template v-else>
                {{ ft.extension }}
              </template>
            </td>
            <td>
              <div class="configure-file-types-actions">
                <template v-if="editId === ft.id">
                  <button
                    class="configure-file-types-action-btn configure-file-types-edit-btn"
                    title="Save"
                    @click="saveEdit(ft.id)"
                  >
                    <font-awesome-icon icon="fa-regular fa-pen-to-square" />
                  </button>
                  <button
                    class="configure-file-types-action-btn configure-file-types-edit-btn"
                    title="Cancel"
                    @click="cancelEdit"
                  >
                    <span style="font-size: 1.1em">✖</span>
                  </button>
                </template>
                <template v-else>
                  <button
                    class="configure-file-types-action-btn configure-file-types-edit-btn"
                    title="Edit"
                    @click="startEdit(ft)"
                  >
                    <font-awesome-icon icon="fa-regular fa-pen-to-square" />
                  </button>
                  <button
                    class="configure-file-types-action-btn configure-file-types-delete-btn"
                    title="Delete"
                    @click="deleteFileType(ft.id)"
                  >
                    <font-awesome-icon icon="trash" />
                  </button>
                </template>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div class="configure-filetypes-add-form">
        <input v-model="newFileType.name" placeholder="File type name" />
        <input v-model="newFileType.extension" placeholder="Extension" />
        <button @click="addFileType">Add</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue';
import { useFileTypeStore } from '@/stores/fileType.js';
import FontAwesomeIcon from '@/plugins/fontawesome';

defineProps({
  fileTypes: { type: Array, default: () => [] },
  isLoading: { type: Boolean, default: false },
});

const fileTypeStore = useFileTypeStore();
const newFileType = ref({ name: '', extension: '' });

const editId = ref(null);
const editFileType = ref({ name: '', extension: '' });

function startEdit(ft) {
  editId.value = ft.id;
  editFileType.value = { name: ft.name, extension: ft.extension };
  nextTick(() => {
    const input = document.querySelector('.edit-highlight');
    if (input) input.focus();
  });
}
function cancelEdit() {
  editId.value = null;
  editFileType.value = { name: '', extension: '' };
}
async function saveEdit(id) {
  await fileTypeStore.updateFileType(id, { ...editFileType.value });
  cancelEdit();
}
async function deleteFileType(id) {
  if (confirm('Delete this file type?')) {
    try {
      await fileTypeStore.deleteFileType(id);
    } catch (e) {
      const detail = e?.response?.data?.detail;
      if (detail && detail.includes('used by a naming standard')) {
        alert(
          'Cannot delete: This file type is used by a naming standard or component. Please delete the related naming standard first.'
        );
      } else {
        alert('Failed to delete file type.');
      }
    }
  }
}
async function addFileType() {
  if (!newFileType.value.name || !newFileType.value.extension) return;
  await fileTypeStore.addFileType({ ...newFileType.value });
  newFileType.value = { name: '', extension: '' };
}
</script>

<style scoped>
.configure-filetypes-page {
  width: 100%;
  min-height: 200px;
  font-family: 'Segoe UI', Arial, sans-serif;
}

.configure-filetypes-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 24px;
  color: #2a2a2a;
}

.configure-filetypes-loading,
.configure-filetypes-empty {
  color: #888;
  font-size: 1.1rem;
  margin-bottom: 18px;
}

.configure-filetypes-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 18px;
  table-layout: fixed;
}

.configure-filetypes-table th,
.configure-filetypes-table td {
  border: 1px solid #e0e0e0;
  padding: 6px 10px;
  text-align: left;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.configure-filetypes-table th:nth-child(1),
.configure-filetypes-table td:nth-child(1) {
  width: 40%;
}

.configure-filetypes-table th:nth-child(2),
.configure-filetypes-table td:nth-child(2) {
  width: 30%;
}

.configure-filetypes-table th:nth-child(3),
.configure-filetypes-table td:nth-child(3) {
  width: 30%;
}

.configure-filetypes-add-form {
  display: flex;
  gap: 10px;
  margin-top: 12px;
}

.configure-filetypes-add-form input {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 5px;
  font-size: 1rem;
}

.configure-filetypes-add-form button {
  background: #10b981;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 7px 18px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.18s;
}

.configure-filetypes-add-form button:hover {
  background: #059669;
}

.configure-file-types-actions {
  display: flex;
  gap: 8px;
}

.configure-file-types-action-btn {
  background: none;
  border: 2px solid;
  font-size: 1.2rem;
  cursor: pointer;
  margin-left: 0;
  border-radius: 6px;
  padding: 0;
  min-width: 38px;
  min-height: 38px;
  width: 38px;
  height: 38px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  transition:
    color 0.2s,
    border-color 0.2s,
    background 0.2s;
}

.configure-file-types-edit-btn {
  border-color: #757575;
  color: #757575;
}

.configure-file-types-edit-btn:hover {
  background: #757575;
  color: #fff;
  border-color: #495057;
}

.configure-file-types-delete-btn {
  border-color: #d32f2f;
  color: #d32f2f;
}

.configure-file-types-delete-btn:hover {
  background: #d32f2f;
  color: #fff;
  border-color: #b71c1c;
}

/* Highlight editable fields */
.edit-highlight {
  border: 2px solid #2563eb !important;
  background: #f0f7ff !important;
  border-radius: 5px;
  outline: none;
  box-shadow: 0 0 0 2px #2563eb33;
  transition:
    border 0.18s,
    box-shadow 0.18s;
  width: 100%;
  box-sizing: border-box;
}
</style>
