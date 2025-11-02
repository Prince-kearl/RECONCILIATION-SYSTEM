# ReconX Project Structure

## 🏗️ Overview

This document outlines the refactored ReconX banking reconciliation system structure, designed for security, maintainability, and scalability.

## 📁 Directory Structure

```
/reconx/
├── backend/                          # Backend API and services
│   ├── api/                         # Main Flask application
│   │   ├── app.py                  # Main Flask app with routes
│   │   ├── config.py               # Configuration management
│   │   ├── database.py             # Database managers and utilities
│   │   ├── database_schema.sql     # Database schema definition
│   │   ├── setup_database.py       # Database setup script
│   │   ├── requirements.txt        # Python dependencies
│   │   ├── config.env              # Environment configuration template
│   │   ├── .env                    # Environment variables (not in git)
│   │   ├── utils/                  # Utility modules
│   │   │   ├── __init__.py
│   │   │   ├── logger.py           # Centralized logging system
│   │   │   ├── security.py         # Security utilities and validation
│   │   │   ├── api_responses.py    # Standardized API responses
│   │   │   └── file_processor.py   # File processing utilities
│   │   ├── services/               # Business logic services
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py     # Authentication service
│   │   │   ├── user_service.py     # User management service
│   │   │   ├── file_service.py     # File upload/processing service
│   │   │   ├── reconciliation_service.py # Reconciliation engine service
│   │   │   └── audit_service.py    # Audit logging service
│   │   ├── models/                 # Data models
│   │   │   ├── __init__.py
│   │   │   ├── user.py             # User model
│   │   │   ├── file.py             # File model
│   │   │   └── reconciliation.py   # Reconciliation model
│   │   ├── middleware/             # Flask middleware
│   │   │   ├── __init__.py
│   │   │   ├── auth_middleware.py  # Authentication middleware
│   │   │   ├── rate_limit.py       # Rate limiting middleware
│   │   │   ├── logging_middleware.py # Request logging middleware
│   │   │   └── security_middleware.py # Security headers middleware
│   │   ├── tests/                  # Test suite
│   │   │   ├── __init__.py
│   │   │   ├── test_auth.py        # Authentication tests
│   │   │   ├── test_security.py    # Security tests
│   │   │   ├── test_api.py         # API endpoint tests
│   │   │   ├── test_database.py    # Database tests
│   │   │   ├── test_reconciliation.py # Reconciliation tests
│   │   │   └── conftest.py         # Test configuration
│   │   ├── logs/                   # Application logs (not in git)
│   │   ├── uploads/                # File uploads (not in git)
│   │   ├── outputs/                # Generated reports (not in git)
│   │   └── README.md               # Backend documentation
│   └── reconciliation_system/      # Core reconciliation engine
│       ├── reconciliation_system_production.py
│       ├── test_reconciliation.py
│       └── README.md
├── frontend/                        # Frontend HTML/CSS/JS
│   ├── assets/                     # Static assets
│   │   ├── css/                    # Stylesheets
│   │   │   ├── main.css            # Main styles
│   │   │   ├── components.css      # Component styles
│   │   │   └── utilities.css       # Utility classes
│   │   ├── js/                     # JavaScript modules
│   │   │   ├── utils.js            # Common utilities
│   │   │   ├── api.js              # API client
│   │   │   ├── auth.js             # Authentication handling
│   │   │   ├── forms.js            # Form validation
│   │   │   ├── notifications.js    # Toast notifications
│   │   │   ├── tables.js           # Table management
│   │   │   └── upload.js           # File upload handling
│   │   └── images/                 # Images and icons
│   ├── pages/                      # HTML pages
│   │   ├── login.html              # Login page
│   │   ├── dashboard.html          # Main dashboard
│   │   ├── upload_enhanced.html    # Canonical file upload page (replaces upload.html)
│   │   ├── balancing.html          # Balance checking
│   │   ├── Report.html             # Reports page
│   │   ├── audit.html              # Audit logs
│   │   ├── profile.html            # User profile
│   │   ├── mail.html               # Email notifications
│   │   └── users.html              # User management
│   └── README.md                   # Frontend documentation
├── docs/                           # System documentation
│   ├── api/                        # API documentation
│   │   ├── endpoints.md            # API endpoint reference
│   │   ├── authentication.md       # Authentication guide
│   │   ├── examples.md             # API usage examples
│   │   └── errors.md               # Error code reference
│   ├── deployment/                 # Deployment guides
│   │   ├── development.md          # Development setup
│   │   ├── production.md           # Production deployment
│   │   ├── docker.md               # Docker deployment
│   │   └── troubleshooting.md      # Common issues
│   ├── security/                   # Security documentation
│   │   ├── overview.md             # Security overview
│   │   ├── authentication.md       # Authentication details
│   │   ├── authorization.md        # Authorization details
│   │   └── compliance.md           # Compliance requirements
│   └── user_guides/                # User documentation
│       ├── getting_started.md      # Getting started guide
│       ├── reconciliation.md       # Reconciliation workflow
│       ├── user_management.md      # User management guide
│       └── troubleshooting.md      # User troubleshooting
├── scripts/                        # Utility scripts
│   ├── setup.sh                    # System setup script
│   ├── deploy.sh                   # Deployment script
│   ├── backup.sh                   # Database backup script
│   └── health_check.sh             # System health check
├── docker/                         # Docker configuration
│   ├── Dockerfile                  # Backend Dockerfile
│   ├── docker-compose.yml          # Development environment
│   ├── docker-compose.prod.yml     # Production environment
│   └── nginx/                      # Nginx configuration
├── .gitignore                      # Git ignore rules
├── .env.example                    # Environment template
├── README.md                       # Project overview
└── PROJECT_STRUCTURE.md            # This file
```

## 🔧 Backend Architecture

### Core Components

1. **Flask Application (`app.py`)**
   - Main application entry point
   - Route definitions
   - Error handlers
   - Middleware registration

2. **Configuration Management (`config.py`)**
   - Environment-based configuration
   - Security settings
   - Database configuration
   - Feature flags

3. **Database Layer (`database.py`)**
   - Connection management
   - Query builders
   - Transaction handling
   - Connection pooling

4. **Utility Modules (`utils/`)**
   - **Logger**: Centralized logging with rotation
   - **Security**: Input validation, rate limiting, security helpers
   - **API Responses**: Standardized response formats
   - **File Processor**: File handling and validation

5. **Services (`services/`)**
   - **Auth Service**: JWT authentication, MFA
   - **User Service**: User management, roles, permissions
   - **File Service**: Upload, processing, storage
   - **Reconciliation Service**: Core reconciliation logic
   - **Audit Service**: Comprehensive logging

6. **Middleware (`middleware/`)**
   - **Auth Middleware**: JWT validation, role checking
   - **Rate Limiting**: Request throttling
   - **Logging**: Request/response logging
   - **Security**: Security headers, CORS

### Security Features

- **JWT Authentication**: Secure token-based authentication
- **MFA Support**: Two-factor authentication with TOTP
- **Rate Limiting**: Protection against brute force attacks
- **Input Validation**: XSS and injection prevention
- **File Security**: Malicious file detection
- **Audit Logging**: Comprehensive activity tracking

## 🎨 Frontend Architecture

### Structure

1. **HTML Pages**: Semantic, accessible markup
2. **CSS**: TailwindCSS with custom components
3. **JavaScript**: Modular ES6+ with utilities

### Key Features

- **Responsive Design**: Mobile-first approach
- **Accessibility**: ARIA labels, keyboard navigation
- **Progressive Enhancement**: Works without JavaScript
- **Component Library**: Reusable UI components

### JavaScript Modules

- **Utils**: Common functions and helpers
- **API**: HTTP client with error handling
- **Auth**: Token management and validation
- **Forms**: Form validation and submission
- **Notifications**: Toast and alert system
- **Tables**: Sortable, searchable data tables

## 🗄️ Database Design

### Schema Features

- **Normalized Structure**: Proper relationships and constraints
- **Performance Indexes**: Optimized for common queries
- **Audit Trail**: Comprehensive change tracking
- **Security**: Encrypted sensitive data
- **Scalability**: Designed for large datasets

### Tables

1. **Users & Roles**: RBAC with permissions
2. **Bank Statements**: External transaction data
3. **Internal Records**: Internal transaction data
4. **Reconciliation Results**: Matching outcomes
5. **Audit Logs**: Activity tracking
6. **Sessions**: User session management
7. **MFA Secrets**: Two-factor authentication

## 🧪 Testing Strategy

### Test Types

1. **Unit Tests**: Individual function testing
2. **Integration Tests**: API endpoint testing
3. **Security Tests**: Authentication and authorization
4. **Performance Tests**: Load and stress testing
5. **End-to-End Tests**: Complete workflow testing

### Test Coverage

- **Backend**: 90%+ code coverage
- **Security**: All security features tested
- **API**: All endpoints with valid/invalid inputs
- **Database**: Schema and query testing

## 🚀 Deployment

### Environments

1. **Development**: Local development setup
2. **Staging**: Pre-production testing
3. **Production**: Live system deployment

### Deployment Options

- **Docker**: Containerized deployment
- **Traditional**: Direct server deployment
- **Cloud**: AWS, Azure, GCP support

## 📊 Monitoring & Logging

### Logging Levels

- **DEBUG**: Development debugging
- **INFO**: General information
- **WARNING**: Potential issues
- **ERROR**: Error conditions
- **CRITICAL**: System failures

### Monitoring

- **Health Checks**: System status monitoring
- **Performance Metrics**: Response times, throughput
- **Security Events**: Failed logins, suspicious activity
- **Business Metrics**: Reconciliation success rates

## 🔒 Security Considerations

### Authentication

- **JWT Tokens**: Secure, stateless authentication
- **MFA**: Two-factor authentication support
- **Session Management**: Secure session handling
- **Password Policies**: Strong password requirements

### Authorization

- **Role-Based Access Control**: Granular permissions
- **Resource-Level Security**: Object-level permissions
- **API Security**: Endpoint protection
- **Data Encryption**: Sensitive data protection

### Compliance

- **Audit Trails**: Complete activity logging
- **Data Retention**: Configurable retention policies
- **Privacy Protection**: PII handling compliance
- **Security Standards**: Industry best practices

## 📈 Performance & Scalability

### Optimization

- **Database Indexing**: Query performance optimization
- **Caching**: Redis-based caching layer
- **Connection Pooling**: Database connection management
- **Batch Processing**: Large dataset handling

### Scalability

- **Horizontal Scaling**: Load balancer support
- **Microservices**: Service decomposition
- **Async Processing**: Background job processing
- **CDN Integration**: Static asset delivery

## 🛠️ Development Workflow

### Code Quality

- **Linting**: Code style enforcement
- **Formatting**: Consistent code formatting
- **Type Hints**: Python type annotations
- **Documentation**: Comprehensive docstrings

### Version Control

- **Git Flow**: Feature branch workflow
- **Code Review**: Pull request reviews
- **Automated Testing**: CI/CD pipeline
- **Deployment**: Automated deployment

## 📚 Documentation

### Types

1. **API Documentation**: Endpoint reference
2. **User Guides**: System usage instructions
3. **Developer Docs**: Technical implementation details
4. **Deployment Guides**: Setup and deployment instructions

### Maintenance

- **Auto-Generated**: API documentation from code
- **Version Control**: Documentation with code
- **Regular Updates**: Keep documentation current
- **User Feedback**: Incorporate user suggestions

---

This structure provides a solid foundation for a secure, maintainable, and scalable banking reconciliation system. Each component is designed with security, performance, and user experience in mind.
