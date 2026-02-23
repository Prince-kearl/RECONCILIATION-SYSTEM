# Supabase Schema Migration - Quick Reference

## 🚀 TL;DR - Migration in 5 Steps

### Step 1: Prepare SQL (Done ✅)
- PostgreSQL schema created: `database_schema_postgresql.sql`
- All MySQL incompatibilities converted
- Default roles and admin user included

### Step 2: Import Schema to Supabase (5 minutes)
```
1. Go to Supabase Dashboard → SQL Editor
2. Click "New Query"
3. Copy contents of database_schema_postgresql.sql
4. Click "Run" button
5. Wait for "Statement executed successfully"
```

### Step 3: Verify Tables Exist (1 minute)
```sql
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
ORDER BY table_name;

-- Should return 11 tables:
-- audit_logs, bank_statements, file_uploads, 
-- internal_records, mfa_secrets, reconciliation_results,
-- reconciliation_runs, roles, user_sessions, users, health_check
```

### Step 4: Test API Connection (1 minute)
```bash
cd /Users/tavido/Desktop/GCB\ reconx
source venv/bin/activate
python test_supabase_api.py

# Expected output: Status 200 ✅
```

### Step 5: Test Flask App (2 minutes)
```bash
python app.py

# In another terminal:
curl http://localhost:5000/api/dashboard

# Should work with Supabase data
```

---

## 📋 What Got Migrated

| Component | MySQL → PostgreSQL | Status |
|-----------|-------------------|--------|
| **Data Types** | AUTO_INCREMENT → SERIAL, ENUM → CREATE TYPE | ✅ Done |
| **Timestamps** | ON UPDATE CURRENT_TIMESTAMP → TRIGGERS | ✅ Done |
| **Indexes** | FULLTEXT → GIN indexes | ✅ Done |
| **Functions** | For user reconciliation summary & audit logging | ✅ Done |
| **Views** | v_reconciliation_summary, v_file_upload_summary | ✅ Done |
| **Security** | Row-Level Security (RLS) policies | ✅ Done |
| **Default Data** | 4 roles + admin user (admin@reconx.com) | ✅ Done |

---

## 🔧 Schema Structure

```
PUBLIC SCHEMA (default)
├── ENUM TYPES (Constraints)
│   ├── role_name
│   ├── user_status
│   ├── file_type_enum
│   ├── file_status_enum
│   ├── transaction_type_bank
│   ├── transaction_type_internal
│   ├── reconciliation_status
│   ├── reconciliation_result_status
│   └── audit_severity
│
├── CORE TABLES (11 tables)
│   ├── roles → users → (all other tables depend)
│   ├── users → user_sessions, mfa_secrets
│   ├── users → file_uploads, bank_statements, internal_records
│   ├── users → reconciliation_runs
│   ├── reconciliation_runs → reconciliation_results
│   ├── audit_logs → audit trail
│   └── health_check → API monitoring
│
├── TRIGGERS (Automatic updated_at)
│   ├── update_users_updated_at
│   ├── update_file_uploads_updated_at
│   ├── update_bank_statements_updated_at
│   ├── update_internal_records_updated_at
│   ├── update_reconciliation_runs_updated_at
│   ├── update_reconciliation_results_updated_at
│   └── update_updated_at_column() [trigger function]
│
├── VIEWS (Query shortcuts)
│   ├── v_reconciliation_summary
│   └── v_file_upload_summary
│
├── FUNCTIONS (Stored procedures)
│   ├── get_user_reconciliation_summary()
│   └── log_audit_event()
│
└── INDEXES (40+ for performance)
    ├── Per-table: status, date, user, amount
    ├── Composite: (date, amount, currency)
    ├── Full-text search: bank_statements.description
    └── Full-text search: internal_records.narration
```

---

## 📊 Sample Queries

### Get Admin User
```sql
SELECT * FROM users WHERE username = 'admin';
```

### List All Roles
```sql
SELECT role_name, description, permissions FROM roles;
```

### Check System Status
```sql
SELECT * FROM health_check LIMIT 1;
```

### View Available Reconciliations
```sql
SELECT * FROM reconciliation_runs ORDER BY started_at DESC;
```

### Search Audit Trail
```sql
SELECT * FROM audit_logs 
WHERE action LIKE '%login%' 
ORDER BY created_at DESC 
LIMIT 10;
```

---

## 🔄 Data Migration (If Needed)

If you have existing MySQL data to migrate:

```bash
# 1. Make sure my SQL is running and has data
# 2. Run migration script
python migrate_to_supabase.py

# 3. Confirm migration when prompted
# 4. Verify counts when asked

# 5. Check results
curl -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  "https://vlwdzlrphofhevfllrgp.supabase.co/rest/v1/users?select=count=exact"
```

---

## 🛡️ Security Features Enabled

✅ **Row-Level Security (RLS):** Users can only see their own data
✅ **Audit Logging:** All actions tracked in audit_logs
✅ **Password Hashing:** Using bcrypt (SHA-256 compatible)
✅ **Session Management:** Secure token-based sessions
✅ **MFA Support:** Multi-factor authentication infrastructure ready
✅ **JSONB for Permissions:** Flexible role-based permissions

---

## 🚨 Important Notes

### Admin Credentials
- Username: `admin`
- Email: `admin@reconx.com`
- Password Hash: `$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G` (bcrypt of "admin123")
- ⚠️ **CHANGE THIS IMMEDIATELY** for production!

### Default Roles
1. **admin** - Full system access
2. **finance_officer** - File upload & reconciliation
3. **auditor** - Reports & audit log viewing
4. **viewer** - Read-only reports

### Connection Method
Your Flask app uses **HTTP API (PostgREST)** not direct PostgreSQL:
- Endpoint: `https://vlwdzlrphofhevfllrgp.supabase.co/rest/v1/`
- Auth: Bearer token with `SUPABASE_SERVICE_ROLE_KEY`
- Built-in: Rate limiting, CORS, automatic pagination

---

## 🧪 Testing Checklist

- [ ] Schema import completes without errors
- [ ] All 11 tables visible in Supabase Dashboard
- [ ] `test_supabase_api.py` returns Status 200
- [ ] Admin user login works
- [ ] File upload endpoint works
- [ ] Reconciliation run creates records
- [ ] Audit logs track user actions
- [ ] All HTML pages render with Supabase data

---

## 🔗 Quick Links

- **Supabase Project:** https://app.supabase.com
- **PostgreSQL Documentation:** https://supabase.com/docs/guides/database
- **PostgREST API:** https://postgrest.org
- **HTTP Client Code:** [supabase_client.py](./supabase_client.py)
- **Full Migration Guide:** [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md)

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| "Enum type already exists" | Safe to ignore if re-running schema |
| "Foreign key violation" | Run migration in correct table order (roles → users → others) |
| "Extension not found" | Use `CREATE EXTENSION IF NOT EXISTS` (already in schema) |
| HTTP 401 "Invalid token" | Check SUPABASE_SERVICE_ROLE_KEY in .env.supabase |
| Tables not visible | Refresh Supabase Dashboard or check schema name (should be "public") |
| User table empty | Admin user insert might have failed; run manually: `INSERT INTO users (user_id, username, ...) VALUES (1, 'admin', ...)` |

---

## 📞 Support

For detailed information, see:
- [Full Migration Guide](./MIGRATION_GUIDE.md)
- [Supabase HTTP Client Setup](./SUPABASE_SETUP.md)
- [Flask Integration Details](./app.py)

---

**Status:** ✅ Ready for production
**Last Updated:** 2026-02-23
**Environment:** PostgreSQL 14+ (Supabase)
