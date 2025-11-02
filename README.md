# ReconX MVP Backend

A secure, production-ready backend for banking reconciliation with role-based access control, file processing, and comprehensive audit logging.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MySQL 8.0+ or MariaDB 10.5+
- pip

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Database Setup
```bash
# Copy configuration template
cp config.env .env

# Edit .env with your MySQL credentials
# IMPORTANT: Change the default passwords in .env for security
# DB_HOST=localhost
# DB_USER=root
# DB_PASSWORD=your_secure_password_here
# DB_NAME=reconx
# SECRET_KEY=your-secret-key-change-in-production
# JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# Run database setup
python setup_database.py
```

### 3. Start the Backend
```bash
# Option 1: Using the startup script (recommended)
python run_server.py

# Option 2: Direct execution (if run_server.py doesn't work)
python app.py
```

**Note:** If you get import errors when running `python app.py`, use the `run_server.py` script instead, which handles the import paths correctly.

The API will be available at `http://localhost:5000`

## 🔑 Core Features

### Authentication & Authorization
- **JWT-based authentication** with configurable expiration
- **Role-based access control (RBAC)**: Admin, Finance Officer, Auditor, Viewer
- **Secure password hashing** using bcrypt
- **Session management** with automatic token validation
- **Rate limiting** to prevent abuse
- **Input validation** and sanitization

### File Processing & Validation
- **Real-time file parsing** for CSV and Excel files
- **Column validation** with flexible column name mapping
- **Data type validation** for dates and amounts
- **File size limits** and security checks
- **Error handling** with detailed feedback

### File Upload & Processing
- **Secure file endpoints** for bank statements and collection reports
- **File validation** (CSV, XLS, XLSX formats)
- **Automatic parsing** and database storage
- **50MB file size limit** (configurable)

### Reconciliation Engine Integration
- **Direct integration** with your `ReconciliationEngine`
- **Strict tolerance rules** (0.00 GHS = MATCHED)
- **Automatic matching** based on date, amount, and description
- **Excel report generation** with multiple sheets
- **Database storage** of all reconciliation results

### Data Storage & Database Schema
- **MySQL database** with proper foreign key relationships
- **Optimized indexes** for fast reconciliation queries
- **Audit trail** for all system activities
- **User management** with role assignments

## 🗄️ Database Schema

### Core Tables
- **`users`** - User accounts with roles and permissions
- **`roles`** - Role definitions and descriptions
- **`bank_statements`** - Uploaded bank transaction data
- **`internal_records`** - Internal ERP/GL transaction data
- **`reconciliation_results`** - Reconciliation outcomes and differences
- **`audit_logs`** - Comprehensive activity logging

### Key Relationships
- Users → Roles (many-to-one)
- Bank Statements → Users (uploaded by)
- Internal Records → Users (uploaded by)
- Reconciliation Results → Bank Statements + Internal Records
- Audit Logs → Users (action performer)

## 🔧 Recent Updates & Fixes

### MVP Readiness Improvements (Latest)
- ✅ **Fixed database schema** - Added missing `reconciliation_runs` table
- ✅ **Implemented real file parsing** - Replaced dummy data with actual CSV/Excel parsing
- ✅ **Fixed API consistency** - Removed duplicate endpoints and standardized responses
- ✅ **Integrated reconciliation engine** - Proper database integration with run tracking
- ✅ **Added comprehensive error handling** - Detailed error messages and validation
- ✅ **Enhanced security** - Rate limiting, input validation, and security middleware
- ✅ **Improved file validation** - Column checking, data type validation, and error feedback

### Key Features Now Working
- **Complete reconciliation workflow** from file upload to report generation
- **Real-time file processing** with proper error handling
- **Database tracking** of all reconciliation runs and results
- **Security enhancements** including rate limiting and input validation
- **Production-ready error handling** with detailed feedback

## 📡 API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### File Management
- `POST /api/upload/bank-statement` - Upload bank statements
- `POST /api/upload/collection-report` - Upload collection reports

### Reconciliation
- `POST /api/reconciliation/start` - Start reconciliation process
- `GET /api/reconciliation/results` - Get reconciliation results
- `GET /api/reconciliation/download/<filename>` - Download reports

### User Management (Admin Only)
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `PUT /api/users/<id>/status` - Update user status

### Audit & Monitoring
- `GET /api/audit/logs` - Get audit logs (Admin/Auditor)
- `GET /api/health` - Health check

## 🔐 Security Features

### Authentication
- JWT tokens with configurable expiration
- Password hashing using bcrypt
- Automatic token validation on protected routes

### Authorization
- Role-based access control (RBAC)
- Route-level permission checks
- Admin-only user management

### Data Protection
- Input validation and sanitization
- Secure file handling
- SQL injection prevention
- XSS protection

### Audit & Compliance
- Comprehensive activity logging
- User action tracking
- IP address recording
- Timestamp preservation

## 🛠️ Configuration

### Environment Variables
```bash
# Flask
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=reconx

# Security
JWT_ACCESS_TOKEN_EXPIRES=8
```

### File Upload Settings
- Maximum file size: 50MB
- Allowed formats: CSV, XLS, XLSX
- Secure filename handling
- Automatic file type validation

## 📊 Reconciliation Workflow

### 1. File Upload
- Users upload bank statements and collection reports
- Files are validated and parsed
- Data is stored in respective database tables

### 2. Reconciliation Process
- Admin/Finance Officer initiates reconciliation
- System pulls data from both tables
- ReconciliationEngine processes with strict tolerance
- Results are saved to database

### 3. Report Generation
- Excel report with multiple sheets
- Matched and unmatched transactions
- Summary statistics
- Downloadable output files

### 4. Audit Trail
- All actions logged with timestamps
- User activity tracking
- File upload records
- Reconciliation run history

## 🧪 Testing

### API Testing
```bash
# Test basic functionality
python test_api.py

# Test specific endpoints
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### Database Testing
```bash
# Test database connection
python setup_database.py

# Verify schema
mysql -u root -p reconx -e "SHOW TABLES;"
```

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Failed
- Verify MySQL is running
- Check credentials in `.env` file
- Ensure database exists: `python setup_database.py`

#### Import Errors
- Install dependencies: `pip install -r requirements.txt`
- Check Python path for ReconciliationEngine

#### File Upload Issues
- Verify file format (CSV, XLS, XLSX)
- Check file size (max 50MB)
- Ensure upload directory exists

#### Authentication Errors
- Verify JWT secret keys in `.env`
- Check token expiration
- Ensure user account is active

### Logs
- Check console output for error messages
- Review audit logs via API endpoint
- Monitor database connection status

## 🔄 Development

### Adding New Features
1. Update database schema if needed
2. Add new API endpoints
3. Implement proper authentication/authorization
4. Add audit logging
5. Update tests

### Database Migrations
- Current schema: `database_schema.sql`
- Setup script: `setup_database.py`
- Future migrations can be added to schema file

### Code Structure
```
api/
├── app.py                 # Main Flask application
├── database.py           # Database managers and utilities
├── database_schema.sql   # Database schema definition
├── setup_database.py     # Database setup script
├── requirements.txt      # Python dependencies
├── config.env           # Configuration template
└── README.md            # This file
```

## 📈 Performance Considerations

### Database Optimization
- Indexes on frequently queried columns
- Foreign key relationships for data integrity
- Efficient query patterns

### File Processing
- Asynchronous file parsing (future enhancement)
- Streaming for large files
- Memory-efficient data handling

### Security
- Rate limiting (future enhancement)
- Request size validation
- Input sanitization

## 🔮 Future Enhancements

### Planned Features
- **Asynchronous processing** for large files
- **Email notifications** for reconciliation completion
- **Advanced reporting** with charts and analytics
- **API rate limiting** and throttling
- **File encryption** for sensitive data
- **Backup and recovery** procedures

### Scalability
- **Load balancing** support
- **Database connection pooling**
- **Caching layer** for frequently accessed data
- **Microservices architecture** consideration

## 📞 Support

### Getting Help
1. Check this README for common solutions
2. Review error logs and console output
3. Verify configuration settings
4. Test database connectivity

### Contributing
- Follow existing code patterns
- Add proper error handling
- Include audit logging
- Update documentation
- Test thoroughly

---

**ReconX MVP Backend** - Secure, scalable, and production-ready banking reconciliation system.
