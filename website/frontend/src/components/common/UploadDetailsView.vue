<template>
  <div class="upload-details">
    <div class="details-section">
      <h3>Upload Information</h3>
      <div class="details-grid">
        <div class="detail-item">
          <label>Branch:</label>
          <span>{{ upload.branch_name }}</span>
        </div>
        <div class="detail-item">
          <label>Original Branch:</label>
          <span>{{ upload.original_branch }}</span>
        </div>
        <div class="detail-item">
          <label>Upload Type:</label>
          <span>{{ formatUploadType(upload.upload_type) }}</span>
        </div>
        <div class="detail-item">
          <label>Status:</label>
          <span class="status-badge" :class="getStatusClass(upload.merge_status)">
            {{ formatStatus(upload.merge_status) }}
          </span>
        </div>
        <div class="detail-item">
          <label>Uploaded:</label>
          <span>{{ formatDate(upload.uploaded_at) }}</span>
        </div>
        <div class="detail-item">
          <label>Uploaded By:</label>
          <span>User {{ upload.uploaded_by }}</span>
        </div>
        <div v-if="upload.tested_at" class="detail-item">
          <label>Last Tested:</label>
          <span>{{ formatDate(upload.tested_at) }}</span>
        </div>
      </div>
    </div>

    <div class="details-section">
      <h3>File Changes</h3>
      <div class="file-changes">
        <div v-if="upload.files?.new?.length > 0" class="file-group">
          <h4 class="file-group-title new">
            <span class="file-icon">+</span>
            New Files ({{ upload.files.new.length }})
          </h4>
          <ul class="file-list">
            <li v-for="file in upload.files.new" :key="file" class="file-item new">
              {{ file }}
            </li>
          </ul>
        </div>

        <div v-if="upload.files?.modified?.length > 0" class="file-group">
          <h4 class="file-group-title modified">
            <span class="file-icon">~</span>
            Modified Files ({{ upload.files.modified.length }})
          </h4>
          <ul class="file-list">
            <li v-for="file in upload.files.modified" :key="file" class="file-item modified">
              {{ file }}
            </li>
          </ul>
        </div>

        <div v-if="upload.files?.deleted?.length > 0" class="file-group">
          <h4 class="file-group-title deleted">
            <span class="file-icon">-</span>
            Deleted Files ({{ upload.files.deleted.length }})
          </h4>
          <ul class="file-list">
            <li v-for="file in upload.files.deleted" :key="file" class="file-item deleted">
              {{ file }}
            </li>
          </ul>
        </div>
      </div>
    </div>

    <div v-if="upload.conflicted_files?.length > 0" class="details-section">
      <h3>Conflicts</h3>
      <div class="conflicts-info">
        <p class="conflict-summary">
          {{ upload.conflicted_files.length }} files have merge conflicts that need resolution.
        </p>
        <ul class="conflict-files">
          <li v-for="file in upload.conflicted_files" :key="file" class="conflict-file">
            <span class="conflict-icon">⚠️</span>
            {{ file }}
          </li>
        </ul>
      </div>
    </div>

    <div v-if="upload.git_details" class="details-section">
      <h3>Technical Details</h3>
      <div class="tech-details">
        <pre>{{ JSON.stringify(upload.git_details, null, 2) }}</pre>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  upload: {
    type: Object,
    required: true
  }
});

function formatUploadType(type) {
  const types = {
    'pending_upload': 'New Files Only',
    'upload_with_modifications': 'With Modifications',
    'upload_with_deletions': 'With Deletions'
  };
  return types[type] || type;
}

function formatStatus(status) {
  const statuses = {
    'ready_to_merge': 'Ready to Merge',
    'needs_resolution': 'Needs Resolution',
    'error': 'Error',
    'pending_admin_approval': 'Pending Review'
  };
  return statuses[status] || status;
}

function getStatusClass(status) {
  const classes = {
    'ready_to_merge': 'ready',
    'needs_resolution': 'conflicts', 
    'error': 'error',
    'pending_admin_approval': 'pending'
  };
  return classes[status] || 'pending';
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  return new Date(dateString).toLocaleString();
}
</script>

<style scoped>
.upload-details {
  padding: 20px 0;
}

.details-section {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.details-section:last-child {
  border-bottom: none;
}

.details-section h3 {
  margin: 0 0 15px 0;
  color: #2c3e50;
  font-size: 1.2rem;
}

.details-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.detail-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-item label {
  font-weight: 600;
  color: #666;
  font-size: 0.9rem;
}

.detail-item span {
  color: #2c3e50;
}

.status-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  text-transform: uppercase;
  width: fit-content;
}

.status-badge.ready {
  background: #e8f5e8;
  color: #2e7d32;
}

.status-badge.conflicts {
  background: #fff3e0;
  color: #f57c00;
}

.status-badge.error {
  background: #ffebee;
  color: #d32f2f;
}

.status-badge.pending {
  background: #e3f2fd;
  color: #1976d2;
}

.file-group {
  margin-bottom: 20px;
}

.file-group-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 10px 0;
  font-size: 1rem;
  font-weight: 600;
}

.file-icon {
  font-weight: bold;
  font-size: 1.2rem;
}

.file-group-title.new {
  color: #2e7d32;
}

.file-group-title.modified {
  color: #f57c00;
}

.file-group-title.deleted {
  color: #d32f2f;
}

.file-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.file-item {
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}

.file-item.new {
  background: #e8f5e8;
  border-left: 3px solid #2e7d32;
}

.file-item.modified {
  background: #fff3e0;
  border-left: 3px solid #f57c00;
}

.file-item.deleted {
  background: #ffebee;
  border-left: 3px solid #d32f2f;
}

.conflicts-info {
  background: #fff3e0;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #f57c00;
}

.conflict-summary {
  margin: 0 0 15px 0;
  font-weight: 500;
  color: #f57c00;
}

.conflict-files {
  list-style: none;
  padding: 0;
  margin: 0;
}

.conflict-file {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  margin-bottom: 4px;
  font-family: monospace;
  font-size: 0.9rem;
}

.conflict-icon {
  font-size: 1rem;
}

.tech-details {
  background: #f8f9fa;
  border-radius: 8px;
  overflow-x: auto;
}

.tech-details pre {
  padding: 15px;
  margin: 0;
  font-size: 0.8rem;
  color: #666;
  white-space: pre-wrap;
}
</style>