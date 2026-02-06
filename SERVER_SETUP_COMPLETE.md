# ✅ Server Setup Complete

## What Was Done

1. ✅ Created virtual environment in `api/venv/`
2. ✅ Installed all dependencies from `requirements.txt`
3. ✅ Updated documentation to use `python3` instead of `python`
4. ✅ Added virtual environment instructions

## How to Start the Server

### Step 1: Navigate to API Directory
```bash
cd /Users/tavido/Desktop/dev+/reconx/api
```

### Step 2: Activate Virtual Environment
```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 3: Start the Server
```bash
python3 run_server.py
```

## Expected Output

When the server starts successfully, you should see:
```
🚀 Starting ReconX Backend Server...
📡 API will be available at: http://localhost:5000
🔍 Health check: http://localhost:5000/api/health
📚 API documentation: See README.md for endpoint details
============================================================
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

## Verify Server is Running

Open a new terminal and run:
```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "version": "1.0.0"
}
```

## Run Tests

Once the server is running, in another terminal:
```bash
cd /Users/tavido/Desktop/dev+/reconx
python3 comprehensive_test_suite.py
```

## Troubleshooting

### Server Won't Start

1. **Check database connection:**
   - Ensure MySQL is running
   - Verify `.env` file has correct database credentials
   - Run `python3 setup_database.py` to initialize database

2. **Check for port conflicts:**
   ```bash
   lsof -ti:5000
   ```
   If a process is using port 5000, kill it:
   ```bash
   kill -9 $(lsof -ti:5000)
   ```

3. **Check virtual environment:**
   ```bash
   cd /Users/tavido/Desktop/dev+/reconx/api
   source venv/bin/activate
   python3 --version  # Should show Python 3.x
   pip list  # Should show installed packages
   ```

### Import Errors

If you see import errors:
```bash
cd /Users/tavido/Desktop/dev+/reconx/api
source venv/bin/activate
pip install -r requirements.txt
```

### Database Errors

If you see database connection errors:
1. Check MySQL is running: `brew services list` (on macOS)
2. Verify database exists: `mysql -u root -p -e "SHOW DATABASES;"`
3. Check `.env` file in `api/` directory has correct credentials

## Quick Reference

| Command | Description |
|--------|-------------|
| `source venv/bin/activate` | Activate virtual environment |
| `python3 run_server.py` | Start the server |
| `curl http://localhost:5000/api/health` | Check server health |
| `python3 comprehensive_test_suite.py` | Run all tests |

## Next Steps

1. ✅ Server is set up and ready
2. ⏭️ Start the server using commands above
3. ⏭️ Run the test suite to verify everything works
4. ⏭️ Begin using the API endpoints

---

**Status**: ✅ Setup Complete  
**Ready to Start**: Yes  
**Dependencies**: ✅ Installed  
**Virtual Environment**: ✅ Created
