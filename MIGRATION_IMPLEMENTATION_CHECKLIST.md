# MySQL to Supabase Migration - Implementation Checklist

## Pre-Migration (Today)
- [ ] Review all migration documentation
  - [ ] Read MIGRATION_GUIDE.md
  - [ ] Review SCHEMA_MIGRATION_QUICKREF.md
  - [ ] Understand DATABASE_SCHEMA_DOCS.md structure
  - [ ] Check migrate_to_supabase.py script

- [ ] Backup current MySQL database (if production data exists)
  ```bash
  mysqldump -h localhost -u root -p reconx > mysql_backup_$(date +%Y%m%d).sql
  ```

- [ ] Document any custom schema modifications (if any)
  ```bash
  # Compare your current schema with provided database_schema_postgresql.sql
  ```

---

## Step 1: Import PostgreSQL Schema to Supabase (5 minutes)

### 1.1 Access Supabase SQL Editor
- [ ] Go to https://app.supabase.com
- [ ] Select project: **reconx-db** (vlwdzlrphofhevfllrgp.supabase.co)
- [ ] Left sidebar → **SQL Editor**
- [ ] Click **+ New Query** or click menu → New

### 1.2 Import Schema
- [ ] Copy entire contents of `database_schema_postgresql.sql` file
- [ ] Paste into SQL Editor query window
- [ ] Click **▶ Run** button (top right)
- [ ] Wait for "Statement executed successfully" message
  - ⏱️ Should complete in 10-30 seconds

### 1.3 Verify Success
In Supabase left sidebar:
- [ ] Expand **Tables** section
- [ ] Verify all 11 tables appear:
  - [ ] audit_logs
  - [ ] bank_statements
  - [ ] file_uploads
  - [ ] health_check
  - [ ] internal_records
  - [ ] mfa_secrets
  - [ ] reconciliation_results
  - [ ] reconciliation_runs
  - [ ] roles
  - [ ] user_sessions
  - [ ] users

---

## Step 2: Verify Default Data (2 minutes)

### 2.1 Check Roles Inserted
Open new SQL query:
```sql
SELECT * FROM roles;
```
- [ ] Admin role exists
- [ ] Finance Officer role exists
- [ ] Auditor role exists
- [ ] Viewer role exists
- [ ] All have permissions JSON populated

### 2.2 Verify Admin User
Open new SQL query:
```sql
SELECT user_id, username, email, role_id, status FROM users WHERE username = 'admin';
```
- [ ] Should return 1 row
- [ ] username: admin
- [ ] email: admin@reconx.com
- [ ] role_id: 1
- [ ] status: active

### 2.3 Check Health Table
```sql
SELECT * FROM health_check LIMIT 1;
```
- [ ] Should return 1 row with test message

---

## Step 3: Test HTTP API Connection (1 minute)

### 3.1 Activate Python Environment
```bash
cd /Users/tavido/Desktop/GCB\ reconx
source venv/bin/activate
```

### 3.2 Run API Test
```bash
python test_supabase_api.py
```

### 3.3 Verify Output
- [ ] Should see: `Status code: 200`
- [ ] Should see: `✅ HTTP API Connection Successful!`
- [ ] Should print health_check table data
- [ ] No errors in output

---

## Step 4: Migrate Existing Data (Optional, if you have MySQL data)

### 4.1 Verify MySQL Backup
- [ ] MySQL server is running locally on port 3306
- [ ] Database `reconx` exists and has data
- [ ] Credentials in .env.supabase are correct

### 4.2 Run Migration Script
```bash
python migrate_to_supabase.py
```

### 4.3 Review Migration Output
- [ ] Script connects to MySQL successfully
- [ ] Confirms Supabase target URL
- [ ] Shows table-by-table migration progress
- [ ] Displays row counts for each table
- [ ] No errors reported

### 4.4 Verify Migration Counts
When prompted:
```
🔍 Verify migration by checking row counts? (yes/no): 
```
- [ ] Type `yes`
- [ ] Script verifies row counts match
- [ ] All tables show expected record counts

---

## Step 5: Update Flask App Configuration

### 5.1 Verify HTTP Client
- [ ] [supabase_client.py](./supabase_client.py) exists
- [ ] Contains SupabaseClient class
- [ ] Has select(), insert(), update(), delete() methods
- [ ] Uses Bearer token authentication

### 5.2 Verify .env.supabase
```bash
cat .env.supabase | grep -E "SUPABASE|SECRET_KEY"
```
- [ ] SUPABASE_URL is set
- [ ] SUPABASE_SERVICE_ROLE_KEY is set
- [ ] SECRET_KEY is set (64 hex chars)
- [ ] JWT_SECRET_KEY is set (64 hex chars)

### 5.3 Test Environment Variables
```bash
python -c "
import os
from dotenv import load_dotenv
load_dotenv('.env.supabase')
print('✅ SUPABASE_URL:', os.getenv('SUPABASE_URL'))
print('✅ SERVICE_ROLE_KEY:', os.getenv('SUPABASE_SERVICE_ROLE_KEY')[:20] + '...')
"
```
- [ ] Should print both values (first 20 chars of key hidden)

---

## Step 6: Test Flask App with Supabase Backend

### 6.1 Start Flask Server
```bash
python app.py
```
- [ ] Server starts without errors
- [ ] Should see: `Running on http://localhost:5000`
- [ ] No database connection errors

### 6.2 Test Basic Endpoints
In another terminal:
```bash
# Test health check
curl -s http://localhost:5000/api/health | jq .

# Test dashboard (may require auth)
curl -s http://localhost:5000/api/dashboard | jq .

# Test roles endpoint
curl -s http://localhost:5000/api/roles | jq .
```
- [ ] No 500 errors
- [ ] Responses return JSON (not HTML error page)
- [ ] Status codes are 200 or 401 (for auth endpoints)

### 6.3 Test Login Endpoint
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```
- [ ] Should return user info and session token
- [ ] No database connection errors
- [ ] Status 200 or 401 (if wrong password)

---

## Step 7: Browser Testing

### 7.1 Open Dashboard
- [ ] Go to http://localhost:5000/dashboard.html
- [ ] Page loads without errors
- [ ] CSS/styling renders correctly
- [ ] No JavaScript console errors (F12)

### 7.2 Test Login Page
- [ ] Go to http://localhost:5000/login.html
- [ ] Enter username: `admin`
- [ ] Enter password: `admin123`
- [ ] Click "Sign In"
- [ ] Should redirect to dashboard
- [ ] Dashboard displays user data from Supabase

### 7.3 Test Key Features
- [ ] File upload page loads
- [ ] Upload a test CSV file
- [ ] File appears in records (check database)
- [ ] Reconciliation tab loads
- [ ] Can view reconciliation history
- [ ] Audit log shows activities

---

## Step 8: Comprehensive Testing

### 8.1 Run Test Suite
```bash
python comprehensive_test_suite.py
```
- [ ] All tests pass (or note failures)
- [ ] Database operations work
- [ ] File upload works
- [ ] User management works
- [ ] Reconciliation works

### 8.2 Check Audit Logs
```bash
curl -s http://localhost:5000/api/audit-logs | jq . | head -20
```
- [ ] Audit logs show all operations
- [ ] Recent activities logged
- [ ] No errors in logging

### 8.3 Performance Check
```bash
# Dashboard should load in <2 seconds
time curl -s http://localhost:5000/api/dashboard > /dev/null
```
- [ ] Response time acceptable (<2s)
- [ ] No timeout errors

---

## Step 9: Git Commit Migration Files

### 9.1 Verify All Files Created
```bash
ls -la | grep -E "database_schema_postgresql|MIGRATION_GUIDE|migrate_to_supabase|DATABASE_SCHEMA_DOCS|SCHEMA_MIGRATION_QUICKREF"
```
- [ ] database_schema_postgresql.sql exists
- [ ] MIGRATION_GUIDE.md exists
- [ ] migrate_to_supabase.py exists
- [ ] DATABASE_SCHEMA_DOCS.md exists
- [ ] SCHEMA_MIGRATION_QUICKREF.md exists

### 9.2 Commit to Git
```bash
git add database_schema_postgresql.sql
git add MIGRATION_GUIDE.md
git add migrate_to_supabase.py
git add DATABASE_SCHEMA_DOCS.md
git add SCHEMA_MIGRATION_QUICKREF.md
git commit -m "Add MySQL to Supabase PostgreSQL schema migration

- Created PostgreSQL-compatible schema (database_schema_postgresql.sql)
- Added comprehensive migration guide and quick reference
- Created migration utility script (migrate_to_supabase.py)
- Included detailed database schema documentation
- All 11 tables, triggers, views, and functions ready
- Compatible with Supabase HTTP API (PostgREST)"

git push origin main
```
- [ ] Commit successful
- [ ] Files pushed to GitHub
- [ ] Can see files in GitHub repository

---

## Step 10: Documentation & Handoff

### 10.1 Review Documentation
- [ ] MIGRATION_GUIDE.md covers all steps ✅
- [ ] SCHEMA_MIGRATION_QUICKREF.md has quick commands ✅
- [ ] DATABASE_SCHEMA_DOCS.md explains all tables ✅
- [ ] Code comments in supabase_client.py are clear ✅

### 10.2 Document Issues (if any)
- [ ] Any DNS issues resolved? Document how
- [ ] Any import errors? Document solution
- [ ] Performance issues? Document limits
- [ ] Add to TROUBLESHOOTING section

### 10.3 Final Verification
```bash
# Count tables
curl -s -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
 "https://vlwdzlrphofhevfllrgp.supabase.co/rest/v1/?select=count=exact" \
 -H "apikey: $SUPABASE_PUBLISHABLE_KEY" | jq .

# Should show 11 tables in database
```
- [ ] 11 tables present
- [ ] Admin user can log in
- [ ] API endpoints responding
- [ ] Dashboard rendering

---

## Post-Migration Tasks (Optional Enhancements)

### Security
- [ ] Change admin password from default
- [ ] Enable MFA for admin account
- [ ] Configure IP whitelisting (if applicable)
- [ ] Review RLS policies for production

### Performance
- [ ] Run ANALYZE on all tables for query optimization
- [ ] Monitor slow queries in Supabase console
- [ ] Adjust indexes based on query patterns
- [ ] Set up connection pooling (PgBouncer)

### Backup & Recovery
- [ ] Configure Supabase automated backups
- [ ] Set backup retention to 7+ days
- [ ] Test backup restoration process
- [ ] Document disaster recovery procedure

### Monitoring
- [ ] Set up Supabase alerts for high CPU
- [ ] Monitor storage usage growth
- [ ] Track API rate limit usage
- [ ] Set up email notifications for issues

### Data Management
- [ ] Archive old audit logs monthly
- [ ] Delete test/demo data before production
- [ ] Implement data retention policies
- [ ] Regular data integrity checks

---

## Rollback Plan (If Issues Occur)

### Step 1: Stop Flask App
```bash
# Press Ctrl+C or kill process
pkill -f "python app.py"
```

### Step 2: Restore from Backup
If you have MySQL backup:
```bash
mysql -u root -p reconx < mysql_backup_$(date +%Y%m%d).sql
```

### Step 3: Revert Flask Config
```bash
git checkout HEAD~1 app.py
# Or revert to previous connection string
```

### Step 4: Restart with MySQL
```bash
python app.py
```

---

## Success Criteria

You know the migration is complete when:

✅ **Schema**
- [ ] 11 tables visible in Supabase Dashboard
- [ ] All ENUM types created
- [ ] Triggers for updated_at working
- [ ] Indexes applied (40+)

✅ **Data**
- [ ] Admin user can log in (admin/admin123)
- [ ] 4 roles exist with permissions
- [ ] health_check table populated

✅ **API**
- [ ] test_supabase_api.py returns Status 200
- [ ] HTTP endpoints working
- [ ] POST/GET/PUT/DELETE all work

✅ **Flask App**
- [ ] Starts without database errors
- [ ] Dashboard loads with data
- [ ] Login works with Supabase
- [ ] File upload processes files
- [ ] Reconciliation creates records
- [ ] Audit logs track activities

✅ **Git**
- [ ] All migration files committed
- [ ] Pushed to GitHub main branch
- [ ] Documentation complete

---

## Time Estimates

| Task | Time | Status |
|------|------|--------|
| Import schema to Supabase | 5 min | ⏱️ |
| Verify tables & data | 2 min | ⏱️ |
| Test HTTP API | 1 min | ⏱️ |
| Migrate MySQL data (optional) | 5-10 min | ⏱️ |
| Update Flask app | 5 min | ⏱️ |
| Test endpoints | 5 min | ⏱️ |
| Browser testing | 5 min | ⏱️ |
| **Total** | **25-30 min** | ⏱️ |

---

## Support & Resources

| Resource | Link |
|----------|------|
| Migration Guide | [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) |
| Quick Reference | [SCHEMA_MIGRATION_QUICKREF.md](./SCHEMA_MIGRATION_QUICKREF.md) |
| Database Docs | [DATABASE_SCHEMA_DOCS.md](./DATABASE_SCHEMA_DOCS.md) |
| HTTP Client | [supabase_client.py](./supabase_client.py) |
| Supabase Docs | https://supabase.com/docs |
| PostgreSQL Docs | https://www.postgresql.org/docs/14 |

---

**Ready?** Start with Step 1! ✅

Good luck with your migration! 🚀
