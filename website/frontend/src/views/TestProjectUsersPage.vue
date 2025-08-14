<template>
  <div class="test-page">
    <div class="container">
      <div class="page-header">
        <h1>Test - Gestion des utilisateurs de projet</h1>
        <p>
          Cette page permet de tester le composant de gestion des utilisateurs
          d'un projet.
        </p>
      </div>

      <div class="test-controls">
        <div class="form-group">
          <label for="project-name">Nom du projet :</label>
          <input
            id="project-name"
            v-model="testProjectName"
            type="text"
            placeholder="Entrez le nom du projet"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="project-id">ID du projet :</label>
          <input
            id="project-id"
            v-model="testProjectId"
            type="number"
            placeholder="Entrez l'ID du projet"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label>
            <input
              v-model="canManageUsers"
              type="checkbox"
              class="form-checkbox"
            />
            Autoriser la gestion des utilisateurs
          </label>
        </div>
        <div class="actions">
          <button class="refresh-button" @click="refreshComponent">
            🔄 Actualiser le composant
          </button>
        </div>
      </div>

      <!-- Instructions -->
      <div class="instructions">
        <h3>Instructions de test :</h3>
        <ol>
          <li>Entrez le nom et l'ID d'un projet existant</li>
          <li>
            Le composant affichera automatiquement les utilisateurs associés au
            projet
          </li>
          <li>
            Vous pouvez modifier les permissions en utilisant le menu déroulant
          </li>
          <li>Utilisez le bouton "+" pour ajouter un nouvel utilisateur</li>
          <li>Utilisez le bouton "✗" pour retirer un utilisateur du projet</li>
          <li>
            Décochez "Autoriser la gestion des utilisateurs" pour voir le mode
            lecture seule
          </li>
        </ol>
      </div>

      <!-- Component Test Area -->
      <div class="component-test-area">
        <div v-if="!testProjectName || !testProjectId" class="placeholder">
          <h3>
            Veuillez saisir un nom et un ID de projet pour tester le composant
          </h3>
          <p>
            Le composant apparaîtra ici une fois que vous aurez fourni les
            informations nécessaires.
          </p>
        </div>

        <ProjectUsersManager
          v-else
          :key="componentKey"
          :project-id="testProjectId"
          :project-name="testProjectName"
          :can-manage-users="canManageUsers"
        />
      </div>

      <!-- Debug Information -->
      <div class="debug-info">
        <h3>Informations de débogage :</h3>
        <div class="debug-content">
          <p>
            <strong>Nom du projet :</strong>
            {{ testProjectName || 'Non défini' }}
          </p>
          <p>
            <strong>ID du projet :</strong> {{ testProjectId || 'Non défini' }}
          </p>
          <p>
            <strong>Gestion autorisée :</strong>
            {{ canManageUsers ? 'Oui' : 'Non' }}
          </p>
          <p><strong>Clé du composant :</strong> {{ componentKey }}</p>
        </div>
      </div>

      <!-- API Endpoints Information -->
      <div class="api-info">
        <h3>Points d'accès API utilisés :</h3>
        <ul>
          <li>
            <code
              >GET
              /api/v1/project-associations/projects/{project_name}/users</code
            >
            - Lister les utilisateurs
          </li>
          <li>
            <code
              >POST
              /api/v1/project-associations/projects/{project_name}/users</code
            >
            - Ajouter un utilisateur
          </li>
          <li>
            <code
              >PUT
              /api/v1/project-associations/projects/{project_name}/users/{user_id}</code
            >
            - Modifier les permissions
          </li>
          <li>
            <code
              >DELETE
              /api/v1/project-associations/projects/{project_name}/users/{user_id}</code
            >
            - Retirer un utilisateur
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import ProjectUsersManager from '@/components/ProjectUsersManager.vue';

// Test data
const testProjectName = ref('');
const testProjectId = ref(null);
const canManageUsers = ref(true);
const componentKey = ref(0);

// Methods
function refreshComponent() {
  componentKey.value += 1;
}
</script>

<style scoped>
.test-page {
  min-height: 100vh;
  background-color: #f7fafc;
  padding: 20px 0;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
}

.page-header h1 {
  margin: 0 0 8px;
  color: #2d3748;
  font-size: 2rem;
}

.page-header p {
  margin: 0;
  color: #718096;
  font-size: 1.125rem;
}

.test-controls {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
  margin-bottom: 24px;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 4px;
  color: #2d3748;
  font-weight: 500;
}

.form-input {
  width: 100%;
  max-width: 300px;
  padding: 8px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-input:focus {
  outline: none;
  border-color: #3182ce;
  box-shadow: 0 0 0 3px rgb(49 130 206 / 10%);
}

.form-checkbox {
  margin-right: 8px;
}

.actions {
  margin-top: 20px;
}

.refresh-button {
  background-color: #3182ce;
  color: white;
  border: none;
  padding: 10px 16px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.refresh-button:hover {
  background-color: #2c5282;
}

.instructions {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
  margin-bottom: 24px;
}

.instructions h3 {
  margin: 0 0 16px;
  color: #2d3748;
}

.instructions ol {
  margin: 0;
  padding-left: 20px;
  color: #4a5568;
}

.instructions li {
  margin-bottom: 8px;
}

.component-test-area {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
  margin-bottom: 24px;
  min-height: 400px;
}

.placeholder {
  text-align: center;
  color: #718096;
  padding: 60px 20px;
}

.placeholder h3 {
  margin: 0 0 12px;
  font-size: 1.25rem;
}

.placeholder p {
  margin: 0;
}

.debug-info {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
  margin-bottom: 24px;
}

.debug-info h3 {
  margin: 0 0 16px;
  color: #2d3748;
}

.debug-content p {
  margin: 0 0 8px;
  color: #4a5568;
}

.api-info {
  background: white;
  padding: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgb(0 0 0 / 10%);
}

.api-info h3 {
  margin: 0 0 16px;
  color: #2d3748;
}

.api-info ul {
  margin: 0;
  padding-left: 20px;
  color: #4a5568;
}

.api-info li {
  margin-bottom: 8px;
}

.api-info code {
  background-color: #edf2f7;
  padding: 2px 6px;
  border-radius: 3px;
  font-family: Monaco, Menlo, 'Ubuntu Mono', monospace;
  font-size: 0.875rem;
}
</style>
