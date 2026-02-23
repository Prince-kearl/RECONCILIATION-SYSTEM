# ReconX MySQL to Supabase PostgreSQL Migration Guide

## Overview
This guide walks you through migrating your ReconX banking reconciliation system from MySQL to Supabase PostgreSQL. The migration includes:
- ✅ Complete database schema conversion (MySQL → PostgreSQL)
- ✅ Enum types setup
- ✅ Automatic updated_at triggers
- ✅ Indexes and performance optimizations
- ✅ Default roles and admin user
- ✅ Row-level security (RLS) policies
- ✅ Database views and stored functions
- ✅ Data migration scripts

## Prerequisites
- Supabase account with project created (vlwdzlrphofhevfllrgp.supabase.co)
- Access to Supabase Dashboard SQL Editor
- No sensitive data currently in MySQL (migration is schema-only initially)

## Step 1: Access Supabase SQL Editor

1. Go to [https://app.supabase.com](https://app.supabase.com)
2. Select your project: **reconx-db**
3. In the left sidebar, click **SQL Editor**
4. Click **New Query** button (or + icon)

## Step 2: Import the PostgreSQL Schema

### Option A: Quick Import (Recommended)

1. In the SQL Editor, open a new query
2. Copy the entire contents of `database_schema_postgresql.sql`
3. Paste into the SQL Editor
4. Click **▶ Run** button (top right)
5. You should see: `Statement executed successfully`

### Option B: Manual Execution (If Step-by-Step Preferred)

If the full schema fails, execute in this order:

**Query 1: Enable Extensions**
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```
✅ Run

**Query 2: Create ENUM Types**
```sql
CREATE TYPE role_name AS ENUM ('admin', 'finance_officer', 'auditor', 'viewer');
CREATE TYPE user_status AS ENUM ('active', 'inactive', 'locked', 'pending_verification');
-- ... (copy all other ENUM creations from database_schema_postgresql.sql)
```
✅ Run

**Query 3: Create Trigger Function**
```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```
✅ Run

**Query 4: Create All Tables**
Copy the remaining CREATE TABLE and index statements.
✅ Run

**Query 5: Insert Default Roles and Admin**
```sql
-- Insert default roles
INSERT INTO roles (role_name, description, permissions) VALUES
-- ... (copy all INSERT statements)
```
✅ Run

## Step 3: Verify Schema Import

In a new SQL query, run:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;
```

**Expected output (11 tables):**
```
audit_logs
bank_statements
file_uploads
internal_records
mfa_secrets
reconciliation_results
reconciliation_runs
roles
user_sessions
users
health_check
```

## Step 4: Verify Default Data

```sql
-- Check roles inserted
SELECT * FROM roles;

-- Check admin user created
SELECT user_id, username, email, role_id FROM users WHERE username = 'admin';
```

**Expected admin user:**
- user_id: 1
- username: admin
- email: admin@reconx.com
- role_id: 1 (admin)

## Step 5: Test API Connection with New Schema

Update your `test_supabase_api.py` and verify tables are queryable:

```python
from supabase_client import select_from_table

# Test roles table
roles = select_from_table('roles')
print(f"✅ Roles table: {len(roles)} rows")

# Test users table (admin user)
users = select_from_table('users')
print(f"✅ Users table: {len(users)} rows")

# Test audit_logs table (empty initially)
audit = select_from_table('audit_logs')
print(f"✅ Audit logs table: {len(audit)} rows")
```

## Step 6: Update Flask App to Use HTTP API

Update your `app.py` to use the Supabase HTTP API client instead of legacy MySQL:

### Example: Login Endpoint Migration

**OLD (MySQL):**
```python
@auth.post('/login')
def login():
    from database import user_manager
    user = user_manager.get_user_by_username(request.json['username'])
    # ... rest of logic
```

**NEW (Supabase HTTP API):**
```python
@auth.post('/login')
def login():
    from supabase_client import select_from_table
    results = select_from_table('users', columns=['*'], username=request.json['username'])
    user = results[0] if results else None
    # ... rest of logic
```

See [Supabase HTTP API Setup](./SUPABASE_SETUP.md) for full migration details.

## Step 7: Data Migration from MySQL (Optional)

If you have existing production data in MySQL:

### Export MySQL Data
```bash
# Export specific table
mysqldump -h localhost -u root -p reconx users > users_export.sql

# Export entire database
mysqldump -h localhost -u root -p reconx > full_export.sql
```

### Convert SQL Syntax
Some SQL operations need conversion:
- `AUTO_INCREMENT` → `SERIAL` (already done in schema)
- `ON UPDATE CURRENT_TIMESTAMP` → Use triggers (already done)
- ENUM values → Type casting (already done)

### Import Data into Supabase
You can:
1. Use pgAdmin (if installed locally)
2. Use Supabase CSV import feature
3. Write Python migration script using supabase_client

## Step 8: Enable Row-Level Security (RLS)

Your schema includes Row-Level Security (RLS) for sensitive tables. To enable:

```sql
-- View RLS status
SELECT tablename, rowsecurity FROM pg_tables WHERE tablename IN ('users', 'audit_logs', 'reconciliation_results');

-- RLS policies are already created in the schema
-- To enable enforcement, run:
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_results ENABLE ROW LEVEL SECURITY;
```

## Common Errors & Solutions

### Error: "Extension uuid-ossp already exists"
**Solution:** This is normal if running the schema multiple times. Safe to ignore.

### Error: "Relation 'x' already exists"
**Solution:** Drop and recreate. The schema file includes DROP TABLE IF EXISTS. Make sure to run the entire schema at once.

### Error: "Type 'user_status' already exists"
**Solution:** Drop enum types first:
```sql
DROP TYPE IF EXISTS user_status CASCADE;
DROP TYPE IF EXISTS role_name CASCADE;
-- ... etc for all types
```

## Next Steps

1. **Test all API endpoints** - Run your Flask app and test login, file upload, reconciliation endpoints
2. **Migrate existing data** - If you have production MySQL data, export and import
3. **Set up Supabase Auth** (optional) - Replace custom JWT with Supabase Auth
4. **Configure Supabase Storage** (optional) - Replace local file uploads with Supabase Storage
5. **Set up backups** - Supabase automatically backs up daily; configure retention in project settings

## Schema Overview

### Core Tables
- **roles** - Authorization roles with JSONB permissions
- **users** - User accounts with password hashing, MFA, session management
- **user_sessions** - Active user sessions
- **mfa_secrets** - Multi-factor authentication keys
- **file_uploads** - Uploaded file tracking

### Reconciliation Tables
- **bank_statements** - Bank transaction records
- **internal_records** - Internal GL/finance records
- **reconciliation_runs** - Reconciliation job runs
- **reconciliation_results** - Matching results per transaction

### Audit & Logging
- **audit_logs** - Complete audit trail of all user actions
- **health_check** - API health monitoring table

### Indexes & Performance
- 40+ indexes on critical query paths
- Composite indexes for common query patterns
- GIN indexes for full-text search
- Automatically maintained updated_at timestamps

## Support Resources

- [Supabase PostgreSQL Documentation](https://supabase.com/docs/guides/database/postgresql)
- [PostgREST API Documentation](https://postgrest.org/en/stable)
- [HTTP API Client Implementation](./supabase_client.py)
- [Flask Integration Setup](./SUPABASE_SETUP.md)

## Troubleshooting

For issues with schema import or data migration:

1. Check **SQL Editor** → **Logs** tab for error details
2. Verify all ENUM types were created: `SELECT * FROM pg_type WHERE typname LIKE '%status%' OR typname LIKE '%type%';`
3. Verify all tables exist: `\dt public.*` (if using psql)
4. Test HTTP API connection: `python test_supabase_api.py`

---

**Status:** ✅ Schema ready for production ReconX deployment
**Last Updated:** 2026-02-23
**Maintainer:** ReconX DevOps
