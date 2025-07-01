// Demo mode configuration
const DEMO_MODE = true; // Set to false for production

// Demo user session for testing
const DEMO_USER = {
    email: 'demo@lsfb.be',
    name: 'Demo User',
    loginTime: Date.now(),
    labId: 'lsfb',
    labName: 'LSFB Lab'
};

// Authentication JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize lab configuration on login page
    if (window.location.pathname.includes('login.html')) {
        initializeLabLogin();
    } else if (!window.location.pathname.includes('welcome.html')) {
        // For other pages, initialize authentication
        initPageAuth();
    }
    
    const loginForm = document.getElementById('loginForm');
    
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;
            const remember = document.getElementById('remember').checked;
            
            // Simulate authentication
            if (email && password) {
                const currentLab = getCurrentLabConfig();
                
                // Store session info with lab context
                const userSession = {
                    email: email,
                    name: extractNameFromEmail(email),
                    loginTime: Date.now(),
                    labId: currentLab.id,
                    labName: currentLab.name
                };
                
                if (remember) {
                    localStorage.setItem('elanora_user', JSON.stringify(userSession));
                } else {
                    sessionStorage.setItem('elanora_user', JSON.stringify(userSession));
                }
                
                // Redirect to projects or dashboard
                window.location.href = 'projects.html';
            } else {
                alert('Please enter valid credentials');
            }
        });
    }
    
    // Handle SSO button
    const ssoButton = document.querySelector('#ssoButton');
    if (ssoButton) {
        ssoButton.addEventListener('click', function() {
            const currentLab = getCurrentLabConfig();
            // Simulate SSO authentication
            alert(`Redirecting to ${currentLab.ssoProvider}...`);
            // In real implementation, this would redirect to SSO provider
        });
    }
    
    // Update the page title on load
    updatePageTitle();
});

// Initialize lab-specific login page
function initializeLabLogin() {
    const urlParams = new URLSearchParams(window.location.search);
    const labId = urlParams.get('lab') || 'lsfb'; // Default to LSFB
    
    const labConfig = getLabConfig(labId);
    
    // Update UI elements
    const instanceBadge = document.getElementById('instanceBadge');
    const instanceDesc = document.getElementById('instanceDesc');
    const ssoText = document.getElementById('ssoText');
    const labTitle = document.getElementById('labTitle');
    const labDescription = document.getElementById('labDescription');
    const statProjects = document.getElementById('statProjects');
    const statResearchers = document.getElementById('statResearchers');
    const statFiles = document.getElementById('statFiles');
    
    if (instanceBadge) instanceBadge.textContent = `${labConfig.name} Instance`;
    if (instanceDesc) instanceDesc.textContent = `Sign in to access ${labConfig.name} research projects`;
    if (ssoText) ssoText.textContent = `Sign in with ${labConfig.ssoProvider}`;
    if (labTitle) labTitle.textContent = `🏛️ ${labConfig.name}`;
    if (labDescription) labDescription.textContent = labConfig.fullName;
    if (statProjects) statProjects.textContent = labConfig.stats.totalRepositories;
    if (statResearchers) statResearchers.textContent = labConfig.stats.totalResearchers;
    if (statFiles) statFiles.textContent = labConfig.stats.totalFiles;
    
    // Apply lab-specific styling
    document.body.classList.add(`lab-${labId}`);
}

function extractNameFromEmail(email) {
    const name = email.split('@')[0];
    return name.split('.').map(part => 
        part.charAt(0).toUpperCase() + part.slice(1)
    ).join(' ');
}

// Check authentication status
function checkAuth() {
    // In demo mode, return demo user if no real user exists
    if (DEMO_MODE) {
        const user = localStorage.getItem('elanora_user') || sessionStorage.getItem('elanora_user');
        return user ? JSON.parse(user) : DEMO_USER;
    }
    
    const user = localStorage.getItem('elanora_user') || sessionStorage.getItem('elanora_user');
    return user ? JSON.parse(user) : null;
}

// Logout function
function logout() {
    localStorage.removeItem('elanora_user');
    sessionStorage.removeItem('elanora_user');
    window.location.href = 'login.html';
}

// Auto-redirect if not authenticated (for protected pages)
function requireAuth() {
    if (!checkAuth()) {
        window.location.href = 'login.html';
    }
}

// Request access to lab instance
function requestAccess() {
    const email = document.getElementById('email').value;
    if (!email) {
        alert('Please enter your email address first');
        document.getElementById('email').focus();
        return;
    }
    
    const currentLab = getCurrentLabConfig();
    alert(`Access request sent to ${currentLab.name} administrators for ${email}. You will receive an email when your access is approved.`);
}

// Get current lab configuration based on URL or session
function getCurrentLabConfig() {
    const urlParams = new URLSearchParams(window.location.search);
    const labId = urlParams.get('lab') || 'lsfb'; // Default to LSFB
    return getLabConfig(labId);
}

// Get lab configuration by ID (in real implementation, this would come from server)
function getLabConfig(labId = 'lsfb') {
    const configs = {
        'lsfb': {
            id: 'lsfb',
            name: 'LSFB Lab',
            fullName: 'Laboratoire de Langue des Signes de Belgique francophone',
            ssoProvider: 'LSFB SSO',
            repositories: [
                {
                    id: 'lsfb-corpus',
                    name: 'LSFB Corpus',
                    description: 'Main corpus for Belgian French Sign Language research',
                    type: 'featured'
                },
                {
                    id: 'frape',
                    name: 'FRAPé',
                    description: 'French-language research on constructed actions',
                    type: 'active'
                }
            ],
            stats: {
                totalRepositories: 2,
                totalResearchers: 8,
                totalFiles: 47,
                totalConflicts: 7
            }
        },
        'lsfx': {
            id: 'lsfx',
            name: 'LSFX Lab',
            fullName: 'Extended Sign Language Research Laboratory',
            ssoProvider: 'LSFX SSO',
            repositories: [
                {
                    id: 'cross-modal',
                    name: 'Cross-Modal Analysis',
                    description: 'Multi-modal sign language analysis project',
                    type: 'featured'
                },
                {
                    id: 'gesture-corpus',
                    name: 'Gesture Corpus',
                    description: 'Comparative gesture and sign language corpus',
                    type: 'collaborative'
                }
            ],
            stats: {
                totalRepositories: 2,
                totalResearchers: 5,
                totalFiles: 23,
                totalConflicts: 3
            }
        }
    };
    
    return configs[labId] || configs['lsfb'];
}

// Update page content based on current lab
function updatePageLabContext() {
    const user = checkAuth();
    if (!user || !user.labName) {
        return;
    }
    
    // Update page title
    updatePageTitle();
    
    // Update page-specific elements
    const labProjectsTitle = document.getElementById('labProjectsTitle');
    if (labProjectsTitle) {
        labProjectsTitle.textContent = `${user.labName} Research Projects`;
    }
    
    // Update instance labels
    const instanceLabel = document.getElementById('instanceLabel');
    if (instanceLabel) {
        instanceLabel.textContent = user.labName;
    }
    
    // Update user display name
    const userDisplays = document.querySelectorAll('.user-menu span');
    userDisplays.forEach(display => {
        if (user.name) {
            display.textContent = user.name;
        }
    });
    
    // Apply lab-specific styling to body
    document.body.classList.add(`lab-${user.labId}`);
}

// Check if current page requires authentication
function isProtectedPage() {
    const protectedPages = ['projects.html', 'index.html', 'conflicts.html', 'tiers.html', 'export.html'];
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    return protectedPages.includes(currentPage);
}

// Initialize authentication for the current page
function initPageAuth() {
    const user = checkAuth();
    
    if (isProtectedPage() && !user && !DEMO_MODE) {
        // Redirect to welcome page if not authenticated (unless in demo mode)
        window.location.href = 'welcome.html';
        return false;
    }
    
    if (user) {
        updatePageLabContext();
    }
    
    return true;
}

// Update page title based on current page and lab
function updatePageTitle() {
    const user = checkAuth();
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    const pageTitles = {
        'projects.html': 'Projects',
        'index.html': 'Dashboard', 
        'conflicts.html': 'Conflicts',
        'tiers.html': 'Tier Management',
        'export.html': 'Export',
        'login.html': 'Login',
        'welcome.html': 'Welcome'
    };
    
    const pageTitle = pageTitles[currentPage] || 'ELANORA';
    const labPrefix = user && user.labName ? `${user.labName} - ` : '';
    
    document.title = `${labPrefix}${pageTitle} - ELANORA`;
}
