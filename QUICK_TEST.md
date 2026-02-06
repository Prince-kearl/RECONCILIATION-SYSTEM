# Quick Test Instructions

## 🚀 Fastest Way to Test the App

### 1. Start the Server (Terminal 1)
```bash
cd /Users/tavido/Desktop/dev+/reconx/api

# Activate virtual environment (if using one)
source venv/bin/activate

# Start server
python3 run_server.py
```

Wait for: `🚀 Starting ReconX Backend Server...`

### 2. Run Tests (Terminal 2)
```bash
cd /Users/tavido/Desktop/dev+/reconx
python comprehensive_test_suite.py
```

### 3. View Results
The test suite will:
- ✅ Show which tests passed
- ❌ Show which tests failed
- ⚠️ Show warnings
- 📊 Provide a summary

## 📋 What Gets Tested

✅ **Authentication** - Login, tokens, authorization  
✅ **File Uploads** - Bank statements & internal records  
✅ **Reconciliation** - Full matching process  
✅ **User Management** - CRUD operations  
✅ **Audit Logs** - Activity tracking  
✅ **Complete Workflows** - End-to-end processes  

## 🔍 Manual Quick Test

If you prefer manual testing:

```bash
# 1. Health check
curl http://localhost:5000/api/health

# 2. Login (get token)
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 3. Use token in subsequent requests
# Replace YOUR_TOKEN with the token from step 2
curl -X GET http://localhost:5000/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 📚 Full Documentation

- **`TESTING_GUIDE.md`** - Complete manual testing guide
- **`TEST_RESULTS_SUMMARY.md`** - Test coverage and results
- **`comprehensive_test_suite.py`** - Automated test script

---

**Ready to test!** 🎯
