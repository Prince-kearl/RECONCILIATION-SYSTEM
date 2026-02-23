# Supabase Migration Guide

## Overview
This guide walks you through connecting your ReconX Flask app to Supabase (PostgreSQL) while maintaining compatibility with your existing MySQL setup.

---

## Step-by-Step Setup

### 1. Create Supabase Project (5 minutes)

**Visit:** https://supabase.com/dashboard

```
New Project:
├─ Project Name: reconx-db
├─ Database Password: (save securely!)
├─ Region: (choose closest to you)
└─ Create
```

Once created, your project will show:
- **Project URL:** https://YOUR_PROJECT_REF.supabase.co
- **Database Host:** db.YOUR_PROJECT_REF.supabase.co

---

### 2. Get Your Credentials

**In Supabase Dashboard:**

Navigate to **Settings > Database**

Copy these values:

```
Host: db.YOUR_PROJECT_REF.supabase.co
Port: 5432
Database: postgres
User: postgres
Password: (what you set during creation)
```

Also get from **Settings > API:**
```
Project URL: https://YOUR_PROJECT_REF.supabase.co
Anon Key: eyJhbG...
Service Role Key: eyJhbG...
```

---

### 3. Update Environment Variables

**Edit `.env` file:**

```bash
# DATABASE TYPE (choose one)
DB_TYPE=postgresql          # NEW: Switch to PostgreSQL
# DB_TYPE=mysql            # OLD: Keep MySQL (legacy)

# SUPABASE CONNECTION DETAILS
DB_HOST=db.YOUR_PROJECT_REF.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=YOUR_DATABASE_PASSWORD
DB_SSLMODE=require

# SUPABASE API (Optional - for future features)
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=YOUR_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY=YOUR_SERVICE_ROLE_KEY
```

---

### 4. Install PostgreSQL Driver

```bash
pip install -r requirements.txt
# OR manually:
pip install psycopg2-binary==2.9.9
```

---

### 5. Test Connection

Run the setup script:

```bash
python setup_supabase.py
```

Expected output:
```
✅ PostgreSQL Connection Successful!
✅ SQLAlchemy Connection Successful!
✅ ALL TESTS PASSED - READY FOR INTEGRATION
```

---

### 6. Update Your Flask App

Your `app.py` already imports from `database.py`. Now update the import to use the new Supabase-compatible version:

**Option A: Replace database.py (Recommended)**

```python
# At the top of app.py, change:
from database import db_manager, user_manager, file_manager, reconciliation_manager, audit_manager

# To:
from database_supabase import db_manager, user_manager, file_manager, reconciliation_manager, audit_manager
```

**Option B: Create a wrapper (if you want to keep both)**

Create `database_wrapper.py`:

```python
import os
from dotenv import load_dotenv

load_dotenv()

db_type = os.getenv('DB_TYPE', 'mysql').lower()

if db_type == 'postgresql':
    from database_supabase import db_manager, user_manager, file_manager, reconciliation_manager, audit_manager
else:
    from database import db_manager, user_manager, file_manager, reconciliation_manager, audit_manager

__all__ = ['db_manager', 'user_manager', 'file_manager', 'reconciliation_manager', 'audit_manager']
```

Then in `app.py`:
```python
from database_wrapper import db_manager, user_manager, file_manager, reconciliation_manager, audit_manager
```

---

### 7. Migrate Your Data (If Switching from MySQL)

**If you have existing MySQL data:**

```bash
# Export from MySQL
mysqldump -u root -p reconx > backup.sql

# Convert MySQL syntax to PostgreSQL (if needed)
# Most queries are compatible, but some syntax differs:
# - AUTO_INCREMENT → SERIAL or AUTO_INCREMENT (PostgreSQL 10+)
# - UNSIGNED → No equivalent (use CHECK constraints)
# - DATETIME → TIMESTAMP

# Import to Supabase (via pgAdmin or command line)
psql postgresql://postgres:password@db.YOUR_PROJECT_REF.supabase.co:5432/postgres < backup.sql
```

---

### 8. Test Your API Endpoints

Start your Flask app:

```bash
python app.py
```

Test endpoints:

```bash
# Test auth
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@gcb.com","password":"password"}'

# Test file upload
curl -X POST http://localhost:5000/api/files/upload \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "bank_statement=@test_bank_statement.csv"

# Check dashboard
curl http://localhost:5000/api/dashboard
```

---

## Database Comparison

### MySQL (Current)
```
Host: localhost
Port: 3306
Driver: PyMySQL
SSL: Optional
```

### PostgreSQL (Supabase)
```
Host: db.YOUR_PROJECT_REF.supabase.co
Port: 5432
Driver: psycopg2
SSL: Required (recommended)
```

---

## Compatibility Matrix

| Feature | MySQL | PostgreSQL |
|---------|-------|-----------|
| SQLAlchemy ORM | ✅ | ✅ |
| Existing Models | ✅ | ✅ |
| Flask-SQLAlchemy | ✅ | ✅ |
| JWT Auth | ✅ | ✅ |
| File Upload | ✅ | ✅ |
| Audit Logs | ✅ | ✅ |
| Real-time Updates | ❌ | ✅ (via Supabase) |
| RLS (Row-Level Security) | ❌ | ✅ (PostgreSQL feature) |

---

## Troubleshooting

### "Connection refused" Error
- Check if Supabase project is active
- Verify credentials in `.env`
- Try direct connection: `psql postgresql://user:password@host:5432/postgres`

### "SSL certificate verification failed"
- Supabase requires SSL
- Ensure `DB_SSLMODE=require` in `.env`
- Or allow unverified: `DB_SSLMODE=allow` (not recommended for production)

### "Module not found" Error
- Install missing driver: `pip install psycopg2-binary`
- Check Python version: `python --version` (3.8+)

### Query Errors
- PostgreSQL is case-sensitive for identifiers (use lowercase)
- Adjust data types if migrating from MySQL
- Some SQL syntax differs (AUTO_INCREMENT, DATETIME vs TIMESTAMP)

---

## Switching Back to MySQL

If you need to revert:

```bash
# In .env:
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=reconx
DB_USER=root
DB_PASSWORD=

# Install MySQL driver
pip install PyMySQL

# Restart app
python app.py
```

---

## Next Steps

1. ✅ Create Supabase project
2. ✅ Copy credentials to `.env.supabase`
3. ✅ Run `setup_supabase.py` to test connection
4. ✅ Update `app.py` imports (or use wrapper)
5. ✅ Restart Flask app
6. ✅ Test API endpoints
7. ✅ (Optional) Migrate data from MySQL
8. ✅ (Optional) Set up real-time updates

---

## Support

For issues:
- Check Supabase docs: https://supabase.com/docs
- Check PostgreSQL docs: https://www.postgresql.org/docs/
- Check SQLAlchemy docs: https://docs.sqlalchemy.org/
