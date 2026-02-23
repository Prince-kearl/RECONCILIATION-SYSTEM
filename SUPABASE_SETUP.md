# Supabase Integration Guide for ReconX

## Quick Start (5-10 minutes)

### 1. Create a Supabase Account & Project

1. Go to https://supabase.com/dashboard
2. Click **New Project**
3. Fill in:
   - **Project Name:** `reconx-db`
   - **Database Password:** (create a strong password and save it!)
   - **Region:** Select your closest region
4. Click **Create new project** (takes 1-2 minutes)

### 2. Get Your Credentials

Once your project is created:

**Path:** Settings → Database (left sidebar)

You'll see your connection details. Fill in `.env.supabase`:

```bash
# Copy from Supabase > Settings > Database
DB_HOST=db.YOUR_PROJECT_REF.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=YOUR_DATABASE_PASSWORD_HERE
DB_SSLMODE=require

# Optional: Copy from Supabase > Settings > API
SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Install PostgreSQL Driver

```bash
pip install -r requirements.txt
# This will install psycopg2-binary (PostgreSQL driver)
```

### 4. Test the Connection

```bash
python setup_supabase.py
```

You should see:
```
✅ PostgreSQL Connection Successful!
✅ SQLAlchemy Connection Successful!
✅ ALL TESTS PASSED - READY FOR INTEGRATION
```

### 5. Update Flask App Configuration

**Edit your `app.py`:**

Add at the top (after imports):
```python
from dotenv import load_dotenv
import os

load_dotenv()

# Use new Supabase-compatible database
from config_supabase import config
```

Then update Flask config:
```python
app.config.from_object(config)
```

### 6. Restart Your App

```bash
python app.py
```

Your Flask app is now connected to Supabase!

---

## File Reference

| File | Purpose |
|------|---------|
| `.env.supabase` | Template for Supabase credentials |
| `database_supabase.py` | New database module (supports both MySQL & PostgreSQL) |
| `config_supabase.py` | Flask configuration (auto-detects MySQL vs PostgreSQL) |
| `setup_supabase.py` | Connection testing script |
| `SUPABASE_MIGRATION_GUIDE.md` | Detailed migration guide |

---

## Switch Between MySQL & PostgreSQL

### Use PostgreSQL (Supabase)
```bash
# In your .env file:
DB_TYPE=postgresql
```

### Use MySQL (Legacy)
```bash
# In your .env file:
DB_TYPE=mysql
```

The app will automatically use the correct driver!

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Flask App (app.py)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
        ┌───────▼────────┐        ┌────────▼──────────┐
        │config_supabase │        │database_supabase  │
        │  (routes to)   │        │  (handles both)   │
        └────────────────┘        └────────┬──────────┘
                │                          │
        ┌───────┴──────────────────────────┴──────────┐
        │                                              │
    ┌───▼────────┐                         ┌──────────▼────┐
    │ PostgreSQL │ (DB_TYPE=postgresql)    │     MySQL    │
    │ (Supabase) │                         │ (legacy)     │
    └────────────┘                         └──────────────┘
```

---

## What Works Seamlessly

✅ All Flask routes (no changes needed)
✅ Authentication (JWT stays the same)
✅ File uploads (just swap databases)
✅ Audit logs and reconciliation
✅ All existing API endpoints

---

## Supabase + Existing Features

Your current stack:
- API authentication ✅ (works as-is)
- File upload processing ✅ (works as-is)
- Reconciliation engine ✅ (works as-is)
- Dashboard data ✅ (works as-is)

New capabilities with Supabase:
- 🚀 Real-time subscriptions (live dashboard updates)
- 🔐 Row-Level Security (RLS) for fine-grained access control
- 📁 Cloud file storage (Supabase Storage)
- 🔑 Managed authentication (Supabase Auth)
- 📊 Vector search for smart reconciliation

---

## Troubleshooting

### Connection Test Fails

**Error:** `"Connection refused"` or `"No route to host"`

**Solution:**
1. Verify Supabase project is active (dashboard shows green status)
2. Double-check credentials in `.env.supabase`
3. Ensure you copied the HOST correctly (includes `db.` prefix)

**Test manually:**
```bash
psql postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT_REF.supabase.co:5432/postgres
```

### "psycopg2 not found" Error

**Solution:**
```bash
pip install psycopg2-binary
```

### SSL Verification Fails

**Solution:**
In `.env.supabase`, try:
```bash
DB_SSLMODE=allow  # (not recommended, use 'require' for production)
```

---

## Next Steps

1. ✅ Set up Supabase account and project
2. ✅ Copy credentials to `.env.supabase`
3. ✅ Run `setup_supabase.py` to verify connection
4. ✅ Update `app.py` configuration
5. ✅ Test API endpoints with new database
6. ✅ (Optional) Migrate existing MySQL data to PostgreSQL
7. ✅ (Optional) Enable real-time features
8. ✅ Deploy to production

---

## For Production Deployment

1. **Use environment variables** (not `.env` file)
   - Set `DB_HOST`, `DB_USER`, `DB_PASSWORD` in your deployment platform
   
2. **Enable Supabase backups**
   - Supabase automatically backs up your database
   
3. **Set up monitoring**
   - Supabase Dashboard > Monitoring
   
4. **Use connection pooling**
   - Already handled in `config_supabase.py`

5. **Secure your JWT keys**
   ```python
   # In production:
   SECRET_KEY = os.getenv('SECRET_KEY')  # Set in environment
   JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')  # Set in environment
   ```

---

## Useful Resources

- **Supabase Docs:** https://supabase.com/docs
- **PostgreSQL Docs:** https://www.postgresql.org/docs/
- **SQLAlchemy + PostgreSQL:** https://docs.sqlalchemy.org/en/20/dialects/postgresql.html
- **psycopg2 Docs:** https://www.psycopg.org/

---

## Questions?

If you encounter any issues:

1. Check the `setup_supabase.py` output for specific error messages
2. Review `SUPABASE_MIGRATION_GUIDE.md` for detailed troubleshooting
3. Test the connection directly with `psql` command
4. Check Supabase dashboard logs for database errors

---

**Status:** ✅ Ready to integrate
**Estimated Setup Time:** 10-15 minutes
**Downtime Required:** ~5 minutes (to restart app)
