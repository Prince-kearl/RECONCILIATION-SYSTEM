# How to Start the ReconX Server

## Quick Start

### Option 1: Using Virtual Environment (Recommended)

```bash
cd /Users/tavido/Desktop/dev+/reconx/api

# Activate virtual environment
source venv/bin/activate

# Start server
python3 run_server.py
```

### Option 2: Direct (if dependencies are installed globally)

```bash
cd /Users/tavido/Desktop/dev+/reconx/api
python3 run_server.py
```

**Note:** Use `python3` (not `python`) on macOS.

### First Time Setup

If you haven't set up the virtual environment yet:

```bash
cd /Users/tavido/Desktop/dev+/reconx/api

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
python3 run_server.py
```

## Server Status

Once started, you should see:
```
🚀 Starting ReconX Backend Server...
📡 API will be available at: http://localhost:5000
🔍 Health check: http://localhost:5000/api/health
```

## Verify Server is Running

In another terminal, test the health endpoint:

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

## Troubleshooting

### "python: command not found"
- Use `python3` instead of `python` on macOS
- Verify Python 3 is installed: `python3 --version`

### Port Already in Use
If port 5000 is already in use:
```bash
# Find process using port 5000
lsof -ti:5000

# Kill the process (replace PID with actual process ID)
kill -9 PID
```

### Import Errors
Make sure you're in the correct directory:
```bash
cd /Users/tavido/Desktop/dev+/reconx/api
```

### Database Connection Issues
1. Ensure MySQL is running
2. Check database credentials in `.env` file
3. Verify database exists: `python3 setup_database.py`

## Running in Background

To run the server in the background:

```bash
cd /Users/tavido/Desktop/dev+/reconx/api
nohup python3 run_server.py > server.log 2>&1 &
```

View logs:
```bash
tail -f server.log
```

Stop the server:
```bash
pkill -f "python3 run_server.py"
```

---

**Ready to test!** Once the server is running, use `comprehensive_test_suite.py` to test all endpoints.
