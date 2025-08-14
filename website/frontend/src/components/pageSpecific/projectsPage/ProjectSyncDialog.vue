<template>
  <div v-if="visible" class="project-sync-dialog-backdrop">
    <div class="project-sync-dialog-modal">
      <h2 class="project-sync-dialog-title">
        {{ t('projectsPage.syncDialog.title') }}
      </h2>
      <div class="project-sync-dialog-content">
        <div v-if="loading" class="project-sync-dialog-loading">
          {{ t('projectsPage.syncDialog.checkingStatus') }}
        </div>
        <div v-else>
          <!-- MISSING FOLDER/.GIT -->
          <template v-if="syncState === 'missing'">
            <div class="project-sync-dialog-message">
              <template v-if="missingType === 'missing_folder'">
                {{ t('projectsPage.syncDialog.missingFolder') }}
              </template>
              <template v-else-if="missingType === 'missing_git'">
                {{ t('projectsPage.syncDialog.missingGit') }}
              </template>
              <template v-else-if="missingType === 'missing_elan_files'">
                {{ t('projectsPage.syncDialog.missingElanFiles') }}
              </template>
              <template v-else>
                {{ t('projectsPage.syncDialog.illFormed') }}
              </template>
            </div>
          </template>
          <!-- OUT OF SYNC -->
          <template v-else-if="syncState === 'out_of_sync'">
            <div class="project-sync-dialog-message">
              <strong>{{
                t('projectsPage.syncDialog.detectedChanges')
              }}</strong>
              <div class="project-sync-dialog-changes-table-wrapper">
                <table class="project-sync-dialog-changes-table">
                  <thead>
                    <tr>
                      <th>{{ t('projectsPage.syncDialog.affectedFile') }}</th>
                      <th>{{ t('projectsPage.syncDialog.status') }}</th>
                      <th>{{ t('projectsPage.syncDialog.inspect') }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr
                      v-for="change in sortedSyncChanges"
                      :key="change.filename"
                    >
                      <td class="change-filename" :title="change.filename">
                        {{ change.filename }}
                      </td>
                      <td>
                        <span
                          class="change-status"
                          :class="
                            'status-' +
                            (change.status === 'untracked'
                              ? 'added'
                              : change.status)
                          "
                        >
                          {{
                            change.status === 'untracked'
                              ? t('projectsPage.syncDialog.added')
                              : t('projectsPage.syncDialog.' + change.status)
                          }}
                        </span>
                      </td>
                      <td>
                        <button
                          class="btn btn-inspect"
                          @click="
                            openDiffDialog(change.filename, change.status)
                          "
                        >
                          {{ t('projectsPage.syncDialog.inspect') }}
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </template>
          <!-- ERROR -->
          <template v-else-if="syncState === 'error'">
            <div class="project-sync-dialog-message error">{{ syncError }}</div>
          </template>
        </div>
      </div>
      <div class="project-sync-dialog-actions">
        <template v-if="syncState === 'missing'">
          <button
            class="btn btn-green"
            :disabled="actionLoading"
            @click="restoreFromBackup"
          >
            {{ t('projectsPage.syncDialog.restoreFromBackup') }}
          </button>
          <button
            class="btn btn-red"
            :disabled="actionLoading"
            @click="confirmDelete"
          >
            {{ t('projectsPage.syncDialog.deleteProject') }}
          </button>
          <button
            class="btn btn-grey"
            :disabled="actionLoading"
            @click="closeDialog"
          >
            {{ t('common.cancel') }}
          </button>
        </template>
        <template v-else-if="syncState === 'in_sync'">
          <button class="btn btn-green" @click="closeDialog">
            {{ t('common.confirm') }}
          </button>
        </template>
        <template v-else-if="syncState === 'out_of_sync'">
          <button
            class="btn btn-green"
            :disabled="actionLoading"
            @click="confirmDiscard"
          >
            {{ t('projectsPage.syncDialog.discardLocalChanges') }}
          </button>
          <button
            class="btn btn-yellow"
            :disabled="actionLoading"
            @click="syncToMaster"
          >
            {{ t('projectsPage.syncDialog.syncToMaster') }}
          </button>
          <button
            class="btn btn-red"
            :disabled="actionLoading"
            @click="closeDialog"
          >
            {{ t('common.cancel') }}
          </button>
        </template>
        <template v-else-if="syncState === 'error'">
          <button class="btn btn-grey" @click="closeDialog">
            {{ t('common.cancel') }}
          </button>
        </template>
      </div>
      <!-- UserConfirm for destructive actions -->
      <UserConfirm
        v-model="showConfirm"
        :message="confirmMessage"
        :title="confirmTitle"
        @confirm="handleConfirmed"
        @cancel="showConfirm = false"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import gitService from '@/api/service/gitService';
import UserConfirm from '@/components/common/UserConfirm.vue';
import { useEventMessageStore } from '@stores/eventMessage';

const { t } = useI18n();
const props = defineProps({
  projectName: { type: String, required: true },
  visible: { type: Boolean, required: true },
  isAdmin: { type: Boolean, default: false },
});
const emit = defineEmits([
  'close',
  'sync-completed',
  'update:visible',
  'inspect-diff',
]);

const loading = ref(true);
const actionLoading = ref(false);
const syncState = ref('');
const syncChanges = ref([]);
const syncError = ref('');
const missingType = ref('');

const showConfirm = ref(false);
const confirmMessage = ref('');
const confirmTitle = ref('');
let confirmAction = null;

const eventMessageStore = useEventMessageStore();

const sortedSyncChanges = computed(() => {
  const added = [];
  const deleted = [];
  const modified = [];
  for (const change of syncChanges.value) {
    const status = change.status === 'untracked' ? 'added' : change.status;
    if (status === 'added') {
      added.push(change);
    } else if (status === 'deleted') {
      deleted.push(change);
    } else {
      modified.push(change);
    }
  }
  return [...added, ...deleted, ...modified];
});

function closeDialog() {
  emit('update:visible', false);
  emit('close');
}

async function checkSync() {
  loading.value = true;
  syncState.value = '';
  syncChanges.value = [];
  syncError.value = '';
  missingType.value = '';
  try {
    const status = await gitService.checkSyncStatus(props.projectName);
    if (
      status.status === 'missing_folder' ||
      status.status === 'missing_git' ||
      status.status === 'missing_elan_files'
    ) {
      syncState.value = 'missing';
      missingType.value = status.status;
    } else if (
      status.status === true ||
      status.status === 'in_sync' ||
      (Array.isArray(status.files_status) && status.files_status.length === 0)
    ) {
      eventMessageStore.addMessage(
        'event_messages.sync.already_up_to_date',
        'success'
      );
      closeDialog();
      return;
    } else {
      syncState.value = 'out_of_sync';
      syncChanges.value = status.files_status || [];
    }
  } catch (e) {
    syncState.value = 'error';
    syncError.value =
      e?.response?.data?.detail || t('projectsPage.syncDialog.checkFailed');
  } finally {
    loading.value = false;
  }
}

function openDiffDialog(filename, status) {
  emit('inspect-diff', { filename, status });
}

async function restoreFromBackup() {
  actionLoading.value = true;
  try {
    await gitService.restoreFromBackup(props.projectName);
    emit('sync-completed');
    closeDialog();
  } catch (e) {
    syncState.value = 'error';
    syncError.value =
      e?.response?.data?.detail || t('projectsPage.syncDialog.restoreFailed');
  } finally {
    actionLoading.value = false;
  }
}

function confirmDelete() {
  confirmTitle.value = t('projectsPage.syncDialog.deleteProject');
  confirmMessage.value = t('projectsPage.syncDialog.deleteConfirm');
  confirmAction = deleteProject;
  showConfirm.value = true;
}

async function deleteProject() {
  actionLoading.value = true;
  try {
    await gitService.declineBackup(props.projectName);
    emit('sync-completed');
    closeDialog();
  } catch (e) {
    syncState.value = 'error';
    syncError.value =
      e?.response?.data?.detail || t('projectsPage.syncDialog.deleteFailed');
  } finally {
    actionLoading.value = false;
  }
}

function confirmDiscard() {
  confirmTitle.value = t('projectsPage.syncDialog.discardLocalChanges');
  confirmMessage.value = t('projectsPage.syncDialog.discardConfirm');
  confirmAction = discardLocalChanges;
  showConfirm.value = true;
}

async function discardLocalChanges() {
  actionLoading.value = true;
  try {
    await gitService.discardLocalChanges(props.projectName);
    emit('sync-completed');
    closeDialog();
  } catch (e) {
    syncState.value = 'error';
    syncError.value =
      e?.response?.data?.detail || t('projectsPage.syncDialog.discardFailed');
  } finally {
    actionLoading.value = false;
  }
}

async function syncToMaster() {
  actionLoading.value = true;
  try {
    await gitService.synchronizeProject(props.projectName);
    emit('sync-completed');
    closeDialog();
  } catch (e) {
    syncState.value = 'error';
    syncError.value =
      e?.response?.data?.detail || t('projectsPage.syncDialog.syncFailed');
  } finally {
    actionLoading.value = false;
  }
}

function handleConfirmed() {
  showConfirm.value = false;
  if (confirmAction) confirmAction();
}

watch(
  () => props.visible,
  (v) => {
    if (v) checkSync();
  }
);
</script>

<style scoped>
.project-sync-dialog-backdrop {
  position: fixed;
  z-index: 10000;
  inset: 0;
  background: rgb(0 0 0 / 25%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.project-sync-dialog-modal {
  background: #fff;
  border-radius: 12px;
  padding: 28px 32px 22px;
  max-width: 80vw;
  max-height: 80vh;
  box-shadow: 0 4px 32px #0002;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  overflow: hidden;
  position: relative;
}

.project-sync-dialog-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 18px;
  color: #222;
  text-align: center;
}

.project-sync-dialog-content {
  flex: 1 1 auto;
  margin-bottom: 2rem;
}

.project-sync-dialog-message {
  font-size: 1.08rem;
  margin-bottom: 18px;
  color: #222;
  overflow-wrap: break-word;
}

.project-sync-dialog-message.error {
  color: #d32f2f;
}

.project-sync-dialog-loading {
  color: #888;
  font-size: 1.08rem;
  margin-bottom: 18px;
}

.project-sync-dialog-changes-table-wrapper {
  max-height: 260px;
  min-height: 60px;
  overflow: auto;
  border-radius: 7px;
  border: 1px solid #e0e0e0;
  background: #fafbfc;
  margin-top: 10px;
}

.project-sync-dialog-changes-table {
  width: 100%;
  min-width: 420px;
  border-collapse: collapse;
  font-size: 0.99rem;
}

.project-sync-dialog-changes-table th,
.project-sync-dialog-changes-table td {
  padding: 8px 12px;
  text-align: left;
}

.project-sync-dialog-changes-table th {
  background: #f0f4f8;
  color: #333;
  font-weight: 600;
  border-bottom: 1.5px solid #e0e0e0;
  position: sticky;
  top: 0;
  z-index: 1;
}

.project-sync-dialog-changes-table tr:not(:last-child) td {
  border-bottom: 1px solid #f0f0f0;
}

.change-filename {
  font-family: 'Fira Mono', Consolas, monospace;
  color: #1976d2;
  font-weight: 500;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.change-status {
  font-weight: 600;
  padding: 2px 10px;
  border-radius: 5px;
  font-size: 0.97em;
  display: inline-block;
  text-transform: capitalize;
}

.status-modified {
  background: #fff3cd;
  color: #b8860b;
  border: 1px solid #ffe082;
}

.status-added {
  background: #e8f5e9;
  color: #388e3c;
  border: 1px solid #a5d6a7;
}

.status-deleted {
  background: #ffebee;
  color: #d32f2f;
  border: 1px solid #ffcdd2;
}

.status-renamed {
  background: #e3f2fd;
  color: #1976d2;
  border: 1px solid #90caf9;
}

.project-sync-dialog-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.btn {
  flex: 1 1 0;
  min-width: 0;
  padding: 0.7em 0.5em;
  font-size: 1.04em;
  font-weight: 600;
  border-radius: 7px;
  cursor: pointer;
  transition:
    background 0.18s,
    color 0.18s,
    box-shadow 0.18s;
  box-shadow: 0 1px 4px #0001;
  margin: 0;
  outline: none;
  text-align: center;
  letter-spacing: 0.01em;
  user-select: none;
  border: 1.5px solid transparent;
  background: #f9fafb;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-green {
  background: #e8f5e9;
  color: #388e3c;
  border-color: #388e3c;
}

.btn-green:hover:not(:disabled) {
  background: #c8e6c9;
  color: #256029;
  border-color: #256029;
}

.btn-yellow {
  background: #fffde7;
  color: #b8860b;
  border-color: #ffe082;
}

.btn-yellow:hover:not(:disabled) {
  background: #fff9c4;
  color: #7c5a00;
  border-color: #ffd54f;
}

.btn-red {
  background: #ffebee;
  color: #d32f2f;
  border-color: #d32f2f;
}

.btn-red:hover:not(:disabled) {
  background: #ffcdd2;
  color: #b71c1c;
  border-color: #b71c1c;
}

.btn-grey {
  background: #ececec;
  color: #444;
  border-color: #bdbdbd;
}

.btn-grey:hover:not(:disabled) {
  background: #e0e0e0;
  color: #222;
  border-color: #757575;
}

.btn-inspect {
  background: #f5f5f5;
  color: #1976d2;
  border: 1.5px solid #1976d2;
  border-radius: 5px;
  padding: 0.4em 0.9em;
  font-size: 0.97em;
  font-weight: 500;
  transition:
    background 0.18s,
    color 0.18s,
    border 0.18s;
}

.btn-inspect:hover:not(:disabled) {
  background: #e3f2fd;
  color: #0d47a1;
  border-color: #0d47a1;
}
</style>
