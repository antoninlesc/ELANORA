# ELANORA - ELAN Collaboration Platform

## Overview

ELANORA is a comprehensive web-based platform designed for collaborative annotation and analysis of ELAN files, specifically tailored for sign language research teams. The platform facilitates real-time collaboration, automated conflict detection, and standardized annotation workflows across multiple institutions.

## Prototype Features

This prototype demonstrates the complete user flow and interface design for the ELANORA platform, including:

### 🔐 Authentication & Access Management
- **Multi-modal Login**: Email/password, institutional SSO, and invitation links
- **Role-based Access**: Different permission levels for administrators, researchers, and contributors
- **Institution Management**: Support for multiple university/research institution instances

### 📊 Project Management
- **Project Dashboard**: Overview of all accessible projects with progress tracking
- **Multi-project Support**: Participate in multiple research projects simultaneously
- **Activity Tracking**: Real-time updates on file changes, conflicts, and collaborations

### 📁 File Management & Upload
- **Drag & Drop Upload**: Intuitive file upload with ELAN (.eaf) validation
- **Project Assignment**: Automatic categorization and assignment to specific projects
- **Version Control**: Track changes and maintain file history

### 🏗️ Advanced Tier Management
- **Hierarchical Tier View**: Tree structure visualization of annotation tiers
- **Group Organization**: Organize tiers by type (Fluency, Prosody, Discourse Markers, etc.)
- **Real-time Status**: Visual indicators for conflicts, validation status, and progress
- **Timeline Visualization**: Interactive timeline showing annotation overlaps and relationships

### ⚠️ Intelligent Conflict Resolution
- **Automated Detection**: AI-powered conflict identification between contributors
- **Priority Classification**: Critical, medium, and low priority conflict categorization
- **Side-by-side Comparison**: Visual comparison of conflicting annotations
- **AI Suggestions**: Machine learning-powered merge suggestions
- **Collaborative Discussion**: Built-in commenting system for conflict resolution
- **Manual Merge Tools**: Advanced editor for custom conflict resolution

### 📤 Flexible Export & Preview
- **Multiple Formats**: Export to ELAN (.eaf), CSV, JSON, and plain text
- **Selective Export**: Choose specific files, tiers, and time ranges
- **Live Preview**: Real-time preview of export structure and content
- **Batch Processing**: Queue multiple exports with progress tracking
- **Custom Configuration**: Save and reuse export configurations

## User Stories Implemented

### Authentication Flow
- ✅ Institutional administrator setup and user invitation
- ✅ Multi-method user authentication (email, SSO, invitation links)
- ✅ Password reset and account management
- ✅ Role-based project access control

### Research Workflow
- ✅ Project dashboard with statistics and progress tracking
- ✅ File upload with drag & drop and validation
- ✅ Tier visualization and management
- ✅ Conflict detection and resolution workflow
- ✅ Collaborative commenting and discussion
- ✅ Export generation with multiple format options

### Quality Assurance
- ✅ Annotation standardization and validation
- ✅ Progress tracking and completion metrics
- ✅ Conflict resolution history and audit trail
- ✅ Export queue management and download tracking

## Technical Architecture

### Frontend Structure
```
docs/prototype/
├── welcome.html          # Landing page
├── login.html           # Authentication interface
├── projects.html        # Project overview and management
├── index.html          # Main dashboard (project-specific)
├── tiers.html          # Tier management and visualization
├── conflicts.html      # Conflict resolution interface
├── export.html         # Export configuration and preview
├── styles.css          # Main stylesheet
├── auth.css           # Authentication-specific styles
├── script.js          # Core JavaScript functionality
└── auth.js            # Authentication and session management
```

### Key Design Principles
- **Responsive Design**: Fully responsive interface supporting desktop, tablet, and mobile devices
- **Accessibility**: WCAG-compliant design with keyboard navigation and screen reader support
- **Performance**: Optimized for large datasets with efficient rendering and caching
- **Scalability**: Modular architecture supporting multi-institutional deployment

## Getting Started

### Prerequisites
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Local web server (optional, for full functionality)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/elanora.git
   cd elanora
   ```

2. Navigate to the prototype:
   ```bash
   cd docs/prototype
   ```

3. Open in browser:
   - **Simple**: Open `welcome.html` directly in your browser
   - **Full functionality**: Serve via local web server:
     ```bash
     # Python 3
     python -m http.server 8000
     
     # Python 2
     python -m SimpleHTTPServer 8000
     
     # Node.js
     npx serve .
     ```

### Demo Flow
1. **Start**: Open `welcome.html` for project introduction
2. **Authentication**: Click "Get Started" to access login page
3. **Projects**: View all accessible research projects
4. **Dashboard**: Enter specific project workspace
5. **Tier Management**: Explore annotation organization
6. **Conflicts**: Experience conflict resolution workflow
7. **Export**: Configure and preview file exports

## User Interface Highlights

### 🎨 Design System
- **Color Palette**: Professional blue (#1a73e8) with semantic status colors
- **Typography**: System fonts for optimal readability and performance
- **Components**: Consistent button styles, form elements, and interactive components
- **Icons**: Emoji-based icons for universal accessibility and quick recognition

### 📱 Responsive Features
- **Mobile-first**: Optimized for touch interfaces and small screens
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Adaptive Layouts**: Grid systems that adjust to screen size and content

### ♿ Accessibility Features
- **Keyboard Navigation**: Full functionality via keyboard shortcuts
- **Screen Reader Support**: Semantic HTML with ARIA labels
- **High Contrast**: Sufficient color contrast ratios for visual accessibility
- **Focus Management**: Clear focus indicators and logical tab order

## Development Roadmap

### Phase 1: Core Platform (Current Prototype)
- ✅ User authentication and project management
- ✅ File upload and basic tier management
- ✅ Conflict detection and resolution interface
- ✅ Export functionality with multiple formats

### Phase 2: Advanced Features
- [ ] Real-time collaborative editing
- [ ] Advanced AI-powered conflict resolution
- [ ] Integration with institutional SSO systems
- [ ] RESTful API for external integrations

### Phase 3: Enterprise Features
- [ ] Advanced analytics and reporting
- [ ] Automated backup and disaster recovery
- [ ] Multi-language interface support
- [ ] Advanced role and permission management

## Contributing

We welcome contributions from the research community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details on:
- Code style and standards
- Testing requirements
- Pull request process
- Issue reporting guidelines

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Research Citations

If you use ELANORA in your research, please cite:

```bibtex
@software{elanora2024,
  title={ELANORA: A Collaborative Platform for ELAN Annotation Analysis},
  author={[Your Research Team]},
  year={2024},
  url={https://github.com/your-org/elanora}
}
```

## Contact & Support

- **Research Team**: [contact@your-institution.edu]
- **Technical Support**: [support@elanora.org]
- **Documentation**: [https://docs.elanora.org]
- **Community Forum**: [https://community.elanora.org]

---

**Built with ❤️ for the sign language research community**