# Project Architecture Documentation

This document provides an overview of the application architecture, explaining the key components, their interactions, and the CI/CD pipeline used for development and deployment.

## System Architecture

The application follows a modern microservices architecture with clear separation between client-side and server-side components.

```mermaid
flowchart LR
    %% Node definitions with icons and styling
    Client(["fa:fa-user Client Browser"])
    Frontend(["fab:fa-react Frontend<br>Vite + React + TypeScript"])
    Backend(["fa:fa-rocket Backend<br>FastAPI"])
    DB[("fa:fa-database PostgreSQL")]
    DocStore[/"fa:fa-file Documents Storage"/]
    
    %% Connections with styling
    Client <---> Frontend
    Frontend <---> Backend
    Backend <---> DB
    Backend <---> DocStore
    
    %% Subgraphs with styling
    subgraph ClientSide["fa:fa-desktop Client Side"]
        style ClientSide fill:#d4f1f9,stroke:#0077b6,stroke-width:2px,color:black
        Client
        Frontend
    end
    
    subgraph ServerSide["fa:fa-server Server Side"]
        style ServerSide fill:#ffebcd,stroke:#e76f51,stroke-width:2px,color:black
        Backend
        DB
        DocStore
    end
    
    %% Node styling
    style Client fill:#90e0ef,stroke:#0077b6,stroke-width:2px,color:black
    style Frontend fill:#90e0ef,stroke:#0077b6,stroke-width:2px,color:black
    style Backend fill:#ffd166,stroke:#e76f51,stroke-width:2px,color:black
    style DB fill:#ffd166,stroke:#e76f51,stroke-width:2px,color:black
    style DocStore fill:#ffd166,stroke:#e76f51,stroke-width:2px,color:black
```

### Client-Side Components

The client-side consists of:
- **Client Browser**: End-user access point to the application
- **Frontend**: Built with Vite, React, and TypeScript, providing a responsive and interactive user interface

### Server-Side Components

The server-side consists of:
- **Backend**: FastAPI application handling business logic and API requests
- **PostgreSQL Database**: Persistent storage for structured data
- **Document Storage**: File system storage for document files

## Backend Architecture

The backend follows a layered architecture with clear separation of concerns.

```mermaid
flowchart LR
    %% Define Client and API
    Client("fa:fa-laptop Client") --> API("fa:fa-server FastAPI App")
    
    %% Define Backend with styling
    subgraph Backend["fa:fa-cogs Backend Architecture"]
        style Backend fill:#f5f5ff,stroke:#6366f1,stroke-width:2px,color:black
        
        %% Define routers with icons
        API --> UserRoutes("fa:fa-users User Routes")
        API --> DocumentRoutes("fa:fa-file-text Document Routes")
        
        %% Define services with icons
        UserRoutes --> UserService("fa:fa-user-circle User Endpoints")
        UserRoutes --> AuthService("fa:fa-key Authentication Endpoint")
        DocumentRoutes --> DocumentService("fa:fa-file-pdf Document Endpoints")
        DocumentRoutes --> PreviewService("fa:fa-image Preview Endpoints")
        
        %% Define data layer with icons
        UserService --> AuthManager("fa:fa-database Auth Manager")
        AuthService --> AuthManager
        DocumentService --> DocumentManager("fa:fa-cogs Document Manager")
        PreviewService --> PreviewManager("fa:fa-cogs Preview Manager")
        
        %% Define storage with icons
        AuthManager --> DB[("fa:fa-hdd-o PostgreSQL Database")]
        
        DocumentManager --> FileStorage("fa:fa-folder File Storage")
        PreviewManager --> FileStorage
        DocumentManager --> DB
        PreviewManager --> DB
    end
    
    %% Styling for components
    style Client fill:#d1fae5,stroke:#059669,stroke-width:2px,color:black
    style API fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:black
    style UserRoutes fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:black
    style DocumentRoutes fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:black
    style UserService fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px,color:black
    style AuthService fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px,color:black
    style DocumentService fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px,color:black
    style PreviewService fill:#ede9fe,stroke:#8b5cf6,stroke-width:2px,color:black
    style AuthManager fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:black
    style DocumentManager fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:black
    style PreviewManager fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:black
    style DB fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:black
    style FileStorage fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:black
```

### Backend Components

- **FastAPI App**: Main entry point handling HTTP requests
- **Routers**: Route requests to appropriate services
  - **Users Router**: Handles user registration, authentication, and management
  - **Documents Router**: Handles document operations
- **Services**: Implement business logic
  - **User Service**: User management functionality
  - **Auth Service**: Authentication and authorization
  - **Document Service**: Document operations (upload, download, etc.)
  - **Preview Service**: Document preview generation
- **Data Layer**: Abstraction for database operations
- **Storage**:
  - **Database**: Stores application data
  - **File Storage**: Manages document files

## Frontend Architecture

The frontend is built with React and TypeScript, following a component-based architecture.

```mermaid
flowchart LR
    subgraph AppSetup ["fa:fa-cogs Application Setup"]
        style AppSetup fill:#f3e5f5,stroke:#ab47bc,stroke-width:2px,color:black
        App["fab:fa-react App"]:::setup --> ThemeProvider["fa:fa-palette ThemeProvider"]:::setup
        ThemeProvider --> AuthProvider["fa:fa-shield-alt AuthProvider (useAuth)"]:::setup
        AuthProvider --> Router["fa:fa-route React Router"]:::setup
    end

    subgraph Routing ["fa:fa-project-diagram Routing"]
        style Routing fill:#e3f2fd,stroke:#42a5f5,stroke-width:2px,color:black
        Router --> PublicRoutes["fa:fa-unlock Public Routes"]:::routing
        Router --> ProtectedRouteWrapper["fa:fa-lock Protected Route"]:::routing
    end

    subgraph PublicPages ["fa:fa-file Public Pages"]
        style PublicPages fill:#e8f5e9,stroke:#66bb6a,stroke-width:2px,color:black
        LoginPage["fa:fa-sign-in-alt Login Page"]:::page
        RegisterPage["fa:fa-user-plus Register Page"]:::page
    end
    PublicRoutes --> LoginPage
    PublicRoutes --> RegisterPage

    subgraph ProtectedArea ["fa:fa-shield-check Protected Area (Dashboard)"]
        style ProtectedArea fill:#fffde7,stroke:#ffee58,stroke-width:2px,color:black
        DashboardPage["fa:fa-tachometer-alt Dashboard Page"]:::page
        TopBar["fa:fa-search TopBar"]:::component
        CorpusList["fa:fa-list CorpusList"]:::component
        CorpusDetail["fa:fa-file-alt CorpusDetail"]:::component
        DocumentPreview["fa:fa-image DocumentPreview"]:::component
        UpdateDocumentModal["fa:fa-edit UpdateDocumentModal"]:::component
        Pagination["fa:fa-ellipsis-h Pagination"]:::component
    end

    ProtectedRouteWrapper --> DashboardPage

    DashboardPage --> TopBar
    DashboardPage -- Route / --> CorpusList

    CorpusList --> Pagination
    CorpusList --> DocumentPreview
    CorpusDetail --> DocumentPreview

    subgraph ServicesAndHooks ["fa:fa-plug Services & Hooks"]
        style ServicesAndHooks fill:#ffebee,stroke:#ef5350,stroke-width:2px,color:black
        ApiService["fa:fa-server API Service (fetchWithAuth)"]:::service
        useAuthHook["fa:fa-key useAuth Hook"]:::service
    end

    subgraph Backend ["fa:fa-database Backend"]
         style Backend fill:#e0f2f1,stroke:#26a69a,stroke-width:2px,color:black
         BackendAPI["fa:fa-cloud Backend API"]:::backend
    end

    %% Data Flow
    AuthProvider --> useAuthHook

    %% Components using Auth Hook
    useAuthHook --> DashboardPage
    useAuthHook --> CorpusDetail
    useAuthHook --> DocumentPreview
    useAuthHook --> UpdateDocumentModal

    %% Components using API Service
    DashboardPage --> ApiService
    DashboardPage -- Route /corpus/:id --> CorpusDetail
    CorpusDetail --> ApiService
    UpdateDocumentModal --> ApiService
    DocumentPreview --> ApiService
    CorpusDetail --> UpdateDocumentModal
    ApiService --> BackendAPI

    %% Styling Classes
    classDef page fill:#d1e7dd,stroke:#198754,color:#000;
    classDef component fill:#cfe2ff,stroke:#0d6efd,color:#000;
    classDef service fill:#f8d7da,stroke:#dc3545,color:#000;
    classDef setup fill:#e2d9f3,stroke:#6f42c1,color:#000;
    classDef backend fill:#d2f4ea,stroke:#17a2b8,color:#000;
    classDef routing fill:#fff3cd,stroke:#856404,color:#000;
```

### Frontend Components

- **App**: Root component
- **Router**: Handles navigation between pages
- **Routes**:
  - **Public Routes**: Accessible without authentication (login, registration)
  - **Protected Route**: Requires authentication (dashboard)
- **Pages**:
  - **Login**: User login interface
  - **Register**: User registration interface
  - **Dashboard**: Main interface showing document list
  - **Corpus detail**: Document viewing and management
- **Components**:
  - **TopBar**: Navigation and search bar
  - **CorpusList**: Displays list of documents
  - **CorpusDetail**: Detailed view of a selected document
  - **Pagination**: Handles pagination of document lists
  - **DocumentPreview**: Previews document content
  - **UpdateDocumentModal**: Modal for updating document details
- **Hooks**:
  - **useAuth**: Handles authentication with backend
  - **API Service**: Handles API requests to the backend
- **Backend API**: FastAPI endpoints for user and document management

## CI/CD Pipeline

The project uses GitLab CI/CD for continuous integration and deployment, ensuring code quality and automating the build process.

```mermaid
flowchart LR
    %% Source code
    Source["fa:fa-code Source Code"]
    
    %% Stage: Lint
    subgraph LintStage["fa:fa-search-plus Lint Stage"]
        style LintStage fill:#e0f7fa,stroke:#0277bd,stroke-width:2px,color:black
        LintB["fab:fa-python Backend Linting<br><i>flake8, black</i>"]
        LintF["fab:fa-js Frontend Linting<br><i>eslint</i>"]
    end
    
    %% Stage: Test
    subgraph TestStage["fa:fa-vial Test Stage"]
        style TestStage fill:#e1f5fe,stroke:#0288d1,stroke-width:2px,color:black
        TestB["fa:fa-flask Backend Tests<br><i>pytest</i>"]
        TestF["fa:fa-check-square Frontend Tests<br><i>jest</i>"]
    end
    
    %% Stage: Build
    subgraph BuildStage["fa:fa-hammer Build Stage"]
        style BuildStage fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px,color:black
        DockerBuildB["fab:fa-docker Docker Build Backend<br><i>multi-platform</i>"]
        DockerBuildF["fab:fa-docker Docker Build Frontend<br><i>multi-platform</i>"]
    end
    
    %% Registries
    subgraph Registries["fa:fa-cloud Registry"]
        style Registries fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px,color:black
        GitlabRegistry["fab:fa-gitlab GitLab Registry"]
        DockerHubRegistry["fab:fa-docker DockerHub"]
    end
    
    %% Deployment (which happens after CI/CD)
    subgraph Deployment["fa:fa-rocket Deployment"]
        style Deployment fill:#fff3e0,stroke:#ef6c00,stroke-width:2px,color:black
        BackendContainer["fa:fa-server Backend Container"]
        FrontendContainer["fa:fa-desktop Frontend Container"]
        PostgreContainer["fa:fa-database PostgreSQL Container"]
    end
    
    %% Volumes
    DBVolume["fa:fa-database Database Volume"]
    DocumentsVolume["fa:fa-folder Documents Volume"]
    
    %% Connections
    Source --> LintB
    Source --> LintF
    
    LintB --> TestB
    LintF --> TestF
    
    TestB --> DockerBuildB
    TestF --> DockerBuildF
    
    DockerBuildB --> GitlabRegistry
    DockerBuildB --> DockerHubRegistry
    DockerBuildF --> GitlabRegistry
    DockerBuildF --> DockerHubRegistry
    
    GitlabRegistry --> BackendContainer
    GitlabRegistry --> FrontendContainer
    DockerHubRegistry --> BackendContainer
    DockerHubRegistry --> FrontendContainer
    DockerHubRegistry --> PostgreContainer
    
    BackendContainer --> DocumentsVolume
    PostgreContainer --> DBVolume
    
    %% Node styling
    style Source fill:#e3f2fd,stroke:#1976d2,stroke-width:2px,color:black
    
    style LintB fill:#e0f7fa,stroke:#0277bd,stroke-width:1px,color:black
    style LintF fill:#e0f7fa,stroke:#0277bd,stroke-width:1px,color:black
    
    style TestB fill:#e1f5fe,stroke:#0288d1,stroke-width:1px,color:black
    style TestF fill:#e1f5fe,stroke:#0288d1,stroke-width:1px,color:black
    
    style DockerBuildB fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px,color:black
    style DockerBuildF fill:#e8f5e9,stroke:#2e7d32,stroke-width:1px,color:black
    
    style GitlabRegistry fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:black
    style DockerHubRegistry fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1px,color:black
    
    style BackendContainer fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:black
    style FrontendContainer fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:black
    style PostgreContainer fill:#fff3e0,stroke:#ef6c00,stroke-width:1px,color:black
    
    style DBVolume fill:#fce4ec,stroke:#c2185b,stroke-width:1px,color:black
    style DocumentsVolume fill:#fce4ec,stroke:#c2185b,stroke-width:1px,color:black
```

### CI/CD Pipeline Components

1. **Lint Stage**:
   - Backend: Uses flake8 and black for code style checking
   - Frontend: Uses ESLint for JavaScript/TypeScript linting

2. **Test Stage**:
   - Backend: Uses pytest for unit and integration tests with coverage reporting
   - Frontend: Uses Jest for component and unit testing

3. **Build Stage**:
   - Multi-platform Docker builds (amd64, arm64)
   - Pushes images to both GitLab Registry and DockerHub

4. **Deployment**:
   - Containerized deployment using Docker Compose
   - Three main containers: Frontend, Backend, and PostgreSQL
   - Additional container for pgAdmin (database management)
   - Persistent volumes for database and document storage

## Deployment Architecture

The application is deployed using Docker containers orchestrated with Docker Compose:

- **Frontend Container**: NGINX serving the React application (port 3000)
- **Backend Container**: FastAPI application (port 8000)
- **PostgreSQL Container**: Database (port 5432, not exposed)
- **PGAdmin Container**: Database management interface (port 5050)

### Persistent Storage

- **Document Storage**: Docker volume mounted to the backend container
- **Database Storage**: Docker volume for PostgreSQL data persistence

## Environment Configuration

The application uses environment variables for configuration:

- Database connection parameters
- Storage paths for documents
- External tool paths (Tesseract for OCR, LibreOffice for document conversion)

## Security Considerations

- PostgreSQL credentials are managed via environment variables
- API endpoints are protected with authentication
- Database is not directly exposed to external network
- Document storage is isolated within Docker volumes

This architecture provides a scalable, maintainable solution with clear separation of concerns, modern development practices, and a robust CI/CD pipeline.