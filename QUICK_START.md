# 🚀 Quick Start Guide

## Start the Server

```bash
cd /Users/tavido/Desktop/dev+/reconx/api
source venv/bin/activate
python3 run_server.py
```

**Server will start on:** http://localhost:5001

> **Note:** Port 5001 is used by default to avoid conflict with macOS AirPlay Receiver on port 5000.

## Verify Server is Running

In another terminal:
```bash
curl http://localhost:5001/api/health
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

```bash
cd /Users/tavido/Desktop/dev+/reconx
python3 comprehensive_test_suite.py
```

The test suite automatically uses port 5001.

## Quick API Test

### 1. Login
```bash
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

### 2. Use the token from response
```bash
# Replace YOUR_TOKEN with the token from login
curl -X GET http://localhost:5001/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Troubleshooting

### Port Already in Use
If port 5001 is also in use, the server will automatically find the next available port (5002, 5003, etc.)

### Change Port Manually
```bash
export FLASK_PORT=8000
python3 run_server.py
```

### Database Connection Issues
1. Ensure MySQL is running
2. Check `.env` file has correct credentials
3. Run: `python3 setup_database.py`

---

**Ready to go!** 🎉
