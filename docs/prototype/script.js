// Modal Management
function showModal(modalId) {
    document.getElementById(modalId).style.display = 'block';
    document.body.style.overflow = 'hidden';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
    document.body.style.overflow = 'auto';
}

function showUploadModal() {
    showModal('uploadModal');
}

function showConflictResolution() {
    showModal('conflictModal');
}

function showTierManager() {
    alert('Interface de gestion des Tiers - À implémenter');
}

function generateConsolidated() {
    alert('Génération du fichier consolidé - À implémenter');
}

// Upload Zone Functionality
document.addEventListener('DOMContentLoaded', function() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    
    if (uploadZone && fileInput) {
        uploadZone.addEventListener('click', () => fileInput.click());
        
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0 && files[0].name.endsWith('.eaf')) {
                handleFileUpload(files[0]);
            } else {
                alert('Veuillez sélectionner un fichier .eaf valide');
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });
    }
    
    // Close modals when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            closeModal(e.target.id);
        }
    });
});

function handleFileUpload(file) {
    console.log('Fichier sélectionné:', file.name);
    document.getElementById('uploadZone').innerHTML = `
        <p>✅ Fichier sélectionné: ${file.name}</p>
        <p>Taille: ${(file.size / 1024 / 1024).toFixed(2)} MB</p>
    `;
}

// Simulate dynamic data updates
function updateStats() {
    // This would be connected to your backend
    console.log('Mise à jour des statistiques...');
}

// Navigation
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link
            e.target.classList.add('active');
            
            // Here you would typically load the appropriate content
            const section = e.target.getAttribute('href').substring(1);
            console.log(`Navigation vers: ${section}`);
        });
    });
});

// Project Management Functions
function openProject(projectId) {
    // Simulate opening a project/repository
    alert(`Opening project: ${projectId}\nRedirecting to repository dashboard...`);
    // In real implementation, would redirect to project-specific dashboard
    window.location.href = `index.html?project=${projectId}`;
}

function acceptInvitation(invitationId) {
    if (confirm('Accept this collaboration invitation?\n\nThis will:\n- Grant you access to shared datasets\n- Allow data synchronization\n- Add the project to your collaborative projects list')) {
        alert(`Collaboration invitation accepted for ${invitationId}\nSetting up secure data access...`);
        // In real implementation, would handle API call to accept invitation
        // Refresh the page or update the UI to show the new collaborative project
        setTimeout(() => {
            location.reload();
        }, 2000);
    }
}

function reviewInvitation(invitationId) {
    alert(`Opening detailed review for invitation: ${invitationId}\n\nThis would show:\n- Full project details\n- Data sharing agreements\n- Access permissions\n- Contact information`);
    // In real implementation, would open a detailed modal or new page
}

function declineInvitation(invitationId) {
    if (confirm('Decline this collaboration invitation?\n\nThis action cannot be undone.')) {
        alert(`Invitation declined for ${invitationId}\nNotifying the requesting laboratory...`);
        // In real implementation, would handle API call to decline invitation
        // Remove the invitation from the UI
        setTimeout(() => {
            location.reload();
        }, 1500);
    }
}

// Project Creation Functions
function showCreateProjectModal() {
    showModal('createProjectModal');
}

function showJoinProjectModal() {
    showModal('joinProjectModal');
}

// Sync and Export Functions
function syncProject(projectId) {
    alert(`Synchronizing project: ${projectId}\n\nSyncing with external laboratories...\nThis may take a few minutes.`);
    // In real implementation, would handle API call to sync project data
}

function exportProjectData(projectId) {
    alert(`Exporting data for project: ${projectId}\n\nPreparing anonymized dataset for export...\nDownload will begin shortly.`);
    // In real implementation, would handle API call to export data
}

// Enhanced Authentication Check for Projects
function requireLabAuth() {
    const user = checkAuth();
    if (!user) {
        window.location.href = 'login.html';
        return false;
    }
    
    // Update UI with lab-specific information
    updateLabContext(user);
    return true;
}

function updateLabContext(user) {
    // Update instance labels and lab-specific information
    const instanceLabels = document.querySelectorAll('.instance-label');
    instanceLabels.forEach(label => {
        if (user.labName) {
            label.textContent = user.labName;
        }
    });
    
    // Update user display name
    const userDisplays = document.querySelectorAll('.user-menu span');
    userDisplays.forEach(display => {
        if (user.name) {
            display.textContent = user.name;
        }
    });
}

// File Management Functions
function toggleFileList(projectId) {
    const fileList = document.getElementById(`files-${projectId}`);
    const toggleIcon = document.getElementById(`toggle-${projectId}`);
    
    if (fileList.style.display === 'none') {
        fileList.style.display = 'block';
        toggleIcon.textContent = '▲';
        toggleIcon.classList.add('rotated');
    } else {
        fileList.style.display = 'none';
        toggleIcon.textContent = '▼';
        toggleIcon.classList.remove('rotated');
    }
}

function openProjectFiles(projectId) {
    alert(`Opening file manager for project: ${projectId}\n\nThis would show:\n- Complete file listing\n- Advanced filtering options\n- Bulk operations\n- Upload interface`);
    // In real implementation, would navigate to file manager view
}

function openFile(fileName) {
    alert(`Opening ELAN file: ${fileName}\n\nThis would:\n- Launch ELAN editor\n- Load the annotation file\n- Show current tier structure\n- Enable collaborative editing`);
    // In real implementation, would open ELAN file or redirect to editor
}

function resolveConflict(fileName) {
    if (confirm(`Resolve conflicts in ${fileName}?\n\nThis will:\n- Show conflicting annotations side by side\n- Allow you to choose which changes to keep\n- Merge annotations safely\n\nProceed?`)) {
        alert(`Opening conflict resolution for ${fileName}...\nRedirecting to conflict resolution interface.`);
        // In real implementation, would open conflict resolution tool
        window.location.href = `conflicts.html?file=${encodeURIComponent(fileName)}`;
    }
}

function reviewFile(fileName) {
    alert(`Opening review interface for ${fileName}\n\nThis would show:\n- Pending changes\n- Annotation quality checks\n- Reviewer comments\n- Approval workflow`);
    // In real implementation, would open review interface
}

function showAllFiles(projectId) {
    alert(`Opening complete file listing for project: ${projectId}\n\nThis would show:\n- All project files in a table view\n- Advanced sorting and filtering\n- Bulk conflict resolution\n- File history and versions`);
    // In real implementation, would navigate to comprehensive file view
}

function resolveAllConflicts(projectId) {
    if (confirm(`Resolve all conflicts in project: ${projectId}?\n\nThis will open a batch conflict resolution interface.\n\nProceed?`)) {
        alert(`Opening batch conflict resolution for ${projectId}...\nThis will process all conflicting files.`);
        // In real implementation, would open batch conflict resolution
        window.location.href = `conflicts.html?project=${projectId}&mode=batch`;
    }
}

// Enhanced navigation functions
function navigateToConflicts(fileName = null) {
    const url = fileName ? `conflicts.html?file=${encodeURIComponent(fileName)}` : 'conflicts.html';
    window.location.href = url;
}

function navigateToDashboard(projectId = null) {
    const url = projectId ? `index.html?project=${projectId}` : 'index.html';
    window.location.href = url;
}