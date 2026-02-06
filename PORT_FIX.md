# Port 5000 Conflict - Fixed

## Problem
Port 5000 is used by macOS AirPlay Receiver (ControlCenter), causing:
```
Address already in use
Port 5000 is in use by another program
```

## Solution Applied
Updated `run_server.py` to:
1. **Use port 5001 by default** (avoids AirPlay conflict)
2. **Auto-detect available port** if 5001 is also in use
3. **Allow port override** via `FLASK_PORT` environment variable

## How to Start Server

### Option 1: Use Default Port 5001 (Recommended)
```bash
cd /Users/tavido/Desktop/dev+/reconx/api
source venv/bin/activate
python3 run_server.py
```

Server will start on: **http://localhost:5001**

### Option 2: Use Custom Port
```bash
export FLASK_PORT=8000
python3 run_server.py
```

### Option 3: Free Up Port 5000 (Not Recommended)
If you really want to use port 5000:

1. **Disable AirPlay Receiver:**
   - System Preferences → General → AirDrop & Handoff
   - Turn off "AirPlay Receiver"

2. **Or kill the process:**
   ```bash
   kill 688  # Replace with actual PID from lsof -ti:5000
   ```

## Update Test Suite

If you change the port, update the test suite:
```bash
# Edit comprehensive_test_suite.py
BASE_URL = "http://localhost:5001"  # Change from 5000 to 5001
```

Or set environment variable:
```bash
export RECONX_API_PORT=5001
python3 comprehensive_test_suite.py
```

## Quick Test

Once server is running on port 5001:
```bash
curl http://localhost:5001/api/health
```

---

**Status**: ✅ Fixed  
**Default Port**: 5001 (avoids macOS AirPlay conflict)
