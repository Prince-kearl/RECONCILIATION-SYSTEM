# ReconX Testing Guide

## Quick Start Testing

### Prerequisites
1. **Database Setup**: Ensure MySQL is running and database is initialized
2. **Dependencies**: Install all Python dependencies
3. **Server Running**: Start the Flask server

### Step 1: Start the Server

```bash
cd /Users/tavido/Desktop/dev+/reconx/api
python run_server.py
```

The server should start on `http://localhost:5000`

### Step 2: Run Comprehensive Tests

In a new terminal:

```bash
cd /Users/tavido/Desktop/dev+/reconx
python comprehensive_test_suite.py
```

## Manual Testing Checklist

### ✅ Authentication & Authorization

#### Test Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

**Expected**: Returns JWT token and user info

#### Test Invalid Login
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"wrong"}'
```

**Expected**: Returns 401 Unauthorized

#### Test Get Current User
```bash
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected**: Returns current user information

---

### ✅ File Upload

#### Upload Bank Statement
```bash
curl -X POST http://localhost:5000/api/files/upload/bank-statement \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@test_bank_statement.csv"
```

**Expected**: Returns success with records count

#### Upload Internal Record
```bash
curl -X POST http://localhost:5000/api/files/upload/internal-record \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@test_internal_record.csv"
```

**Expected**: Returns success with records count

#### Get File Status Summary
```bash
curl -X GET http://localhost:5000/api/files/status/summary \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected**: Returns file status summary

---

### ✅ Reconciliation

#### Start Reconciliation
```bash
curl -X POST http://localhost:5000/api/reconciliation/start \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"tolerance": 0.00}'
```

**Expected**: Returns reconciliation results with run_id

#### Get Reconciliation Results
```bash
curl -X GET http://localhost:5000/api/reconciliation/results \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected**: Returns list of reconciliation results

#### Download Report
```bash
curl -X GET "http://localhost:5000/api/reconciliation/download/reconciliation_RECON_YYYYMMDD_HHMMSS.xlsx" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -o report.xlsx
```

**Expected**: Downloads Excel report file

---

### ✅ User Management (Admin Only)

#### List Users
```bash
curl -X GET http://localhost:5000/api/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected**: Returns list of all users

#### Create User
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "Test123!",
    "full_name": "Test User",
    "role": "viewer"
  }'
```

**Expected**: Returns success with user_id

---

### ✅ Audit Logs

#### Get Audit Logs
```bash
curl -X GET http://localhost:5000/api/audit/logs \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected**: Returns audit log entries

---

### ✅ Health Check

#### Health Check
```bash
curl -X GET http://localhost:5000/api/health
```

**Expected**: Returns server status

---

## Test Data Files

### Sample Bank Statement (test_bank_statement.csv)
```csv
date,amount,description,bank_ref
2026-01-01,1000.00,Payment from Customer A,REF001
2026-01-02,500.00,Payment from Customer B,REF002
2026-01-03,750.00,Payment from Customer C,REF003
2026-01-04,1200.00,Payment from Customer D,REF004
2026-01-05,300.00,Payment from Customer E,REF005
```

### Sample Internal Record (test_internal_record.csv)
```csv
date,amount,narration,reference
2026-01-01,1000.00,Payment from Customer A,REF001
2026-01-02,500.00,Payment from Customer B,REF002
2026-01-03,750.00,Payment from Customer C,REF003
2026-01-04,1200.00,Payment from Customer D,REF004
```

---

## Complete Workflow Test

1. **Login** → Get JWT token
2. **Upload Bank Statement** → Verify success
3. **Upload Internal Record** → Verify success
4. **Start Reconciliation** → Verify completion
5. **Get Results** → Verify data
6. **Download Report** → Verify file download

---

## Expected Test Results

### ✅ Should Pass
- Health check
- Login with valid credentials
- Login rejection with invalid credentials
- File uploads (CSV, Excel)
- File status summary
- Reconciliation process
- Results retrieval
- User listing (if admin)
- Audit logs (if admin/auditor)

### ⚠️ May Warn (Not Critical)
- User creation (requires admin role)
- Some endpoints may return 403 if user lacks permissions

### ❌ Should Fail (Security Tests)
- Unauthorized access without token
- Invalid file types
- Missing required fields

---

## Troubleshooting

### Server Not Starting
- Check if port 5000 is available
- Verify database connection
- Check environment variables

### Authentication Failing
- Verify admin user exists: `python api/setup_database.py`
- Check password: default is `admin123`

### File Upload Failing
- Verify file format (CSV or Excel)
- Check file size (max 50MB)
- Ensure required columns exist

### Reconciliation Failing
- Ensure both bank statement and internal records are uploaded
- Check data format matches expected schema
- Verify database connection

---

## Test Coverage

### Endpoints Tested
- ✅ `/api/health` - Health check
- ✅ `/api/auth/login` - Login
- ✅ `/api/auth/me` - Current user
- ✅ `/api/files/upload/bank-statement` - Upload bank statement
- ✅ `/api/files/upload/internal-record` - Upload internal record
- ✅ `/api/files/status/summary` - File status
- ✅ `/api/files/uploads` - List files
- ✅ `/api/reconciliation/start` - Start reconciliation
- ✅ `/api/reconciliation/results` - Get results
- ✅ `/api/reconciliation/download/<filename>` - Download report
- ✅ `/api/users` - User management
- ✅ `/api/audit/logs` - Audit logs

### Workflows Tested
- ✅ Complete reconciliation workflow
- ✅ File upload workflow
- ✅ Authentication workflow
- ✅ Error handling

---

## Running Tests in CI/CD

```bash
# Install dependencies
pip install -r api/requirements.txt
pip install requests pandas

# Start server in background
cd api && python run_server.py &
SERVER_PID=$!

# Wait for server to start
sleep 5

# Run tests
cd .. && python comprehensive_test_suite.py

# Stop server
kill $SERVER_PID
```

---

**Last Updated**: 2026-02-04
