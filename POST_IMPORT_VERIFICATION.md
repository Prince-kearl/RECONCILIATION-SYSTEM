# 📋 Post-Import Verification Checklist

## ✅ After You Import the Schema to Supabase

Use this checklist to verify the import was successful.

---

## 1️⃣ Check Tables Created (Supabase Dashboard)

**Go to:** Supabase Dashboard → Your Project → **Tables**

In the left sidebar "Tables" section, you should see **exactly 11 tables**:

```
✓ audit_logs
✓ bank_statements
✓ file_uploads
✓ health_check
✓ internal_records
✓ mfa_secrets
✓ reconciliation_results
✓ reconciliation_runs
✓ roles
✓ user_sessions
✓ users
```

**If you see fewer than 11 tables:**
- The import may have failed
- Check Supabase error messages in the SQL Editor
- See MIGRATION_GUIDE.md "Common Errors & Solutions"

---

## 2️⃣ Verify Roles Inserted

**In Supabase SQL Editor**, create a NEW query and run:

```sql
SELECT role_name, description FROM roles ORDER BY role_id;
```

**Expected output (4 rows):**
```
admin            | System Administrator - Full access...
finance_officer  | Finance Officer - Can upload files...
auditor          | Auditor - Can view reports and audit logs
viewer           | Viewer - Read-only access to reports
```

**If you see 0 rows:**
- The roles INSERT didn't work
- Roles table exists but is empty
- Check SQL Editor for errors during import

---

## 3️⃣ Verify Admin User Created

**In Supabase SQL Editor**, create a NEW query and run:

```sql
SELECT user_id, username, email, role_id, status 
FROM users 
WHERE username = 'admin';
```

**Expected output (1 row):**
```
user_id: 1
username: admin
email: admin@reconx.com
role_id: 1
status: active
```

**If you see 0 rows:**
- The admin user INSERT didn't work
- Users table exists but no admin
- Check SQL Editor errors

---

## 4️⃣ Quick Table Count

**In Supabase SQL Editor**, create a NEW query and run:

```sql
SELECT COUNT(*) as total_tables FROM information_schema.tables 
WHERE table_schema = 'public';
```

**Expected output:**
```
total_tables: 11
```

**If you see fewer:**
- Not all tables were created
- Re-run the schema import
- Check for errors in the first few lines of SQL

---

## 5️⃣ Test API Connection

**In your terminal**, run:

```bash
cd "/Users/tavido/Desktop/GCB reconx"
source venv/bin/activate
python test_supabase_api.py
```

**Expected output:**
```
======================================================================
Testing Supabase HTTP API Connection
======================================================================

📊 Querying table `health_check`...
Status code: 200
✅ HTTP API Connection Successful!
Data: [
  {
    "id": 1,
    "message": "Supabase PostgreSQL schema initialized successfully",
    "created_at": "2026-02-23T..."
  }
]
```

**If you get Status 401 or 403:**
- Check SUPABASE_SERVICE_ROLE_KEY in .env.supabase
- Make sure it's the correct key

**If you get a connection error:**
- Check internet connection
- Verify SUPABASE_URL in .env.supabase

---

## 6️⃣ Check for Indexes

**In Supabase SQL Editor**, create a NEW query and run:

```sql
SELECT COUNT(*) as index_count FROM pg_indexes 
WHERE schemaname = 'public';
```

**Expected output:**
```
index_count: 70+ (should be higher than 70)
```

**What this means:**
- Indexes are crucial for query performance
- 70+ indexes were created per the schema
- If count is < 50, some indexes may be missing

---

## 7️⃣ Verify Triggers (Automatic updated_at)

**In Supabase SQL Editor**, create a NEW query and run:

```sql
SELECT COUNT(*) as trigger_count FROM information_schema.triggers 
WHERE trigger_schema = 'public';
```

**Expected output:**
```
trigger_count: 8 (one for each table with updated_at)
```

**What this means:**
- Automatic timestamp updates on every table modification
- If count is < 8, some triggers didn't create

---

## 8️⃣ Check ENUM Types

**In Supabase SQL Editor**, create a NEW query and run:

```sql
SELECT COUNT(*) as enum_count FROM pg_type 
WHERE typtype = 'e' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
```

**Expected output:**
```
enum_count: 9 (9 ENUM types for data validation)
```

**What this means:**
- Data type constraints for status, roles, etc.
- If count is < 9, some ENUM types didn't create

---

## ✅ SUCCESS CHECKLIST

Mark each item as you verify:

- [ ] All 11 tables visible in Dashboard
- [ ] `roles` table has 4 rows
- [ ] `users` table has admin user (user_id=1)
- [ ] Total table count: 11
- [ ] API test returns Status 200
- [ ] Index count: 70+
- [ ] Trigger count: 8
- [ ] ENUM type count: 9

**If all items are checked:** ✅ **Migration successful! Proceed to next steps.**

---

## 🚨 Troubleshooting

### ❌ "Role admin already exists"
- This is normal on re-import
- The schema uses `INSERT INTO ... ON CONFLICT DO NOTHING`
- Safe to ignore

### ❌ "Extension uuid-ossp already exists"
- Normal on re-import
- Uses `CREATE EXTENSION IF NOT EXISTS`
- Safe to ignore

### ❌ "Relation users already exists"
- Tables already exist from previous import
- Either drop them first or re-run full schema
- Schema file includes `DROP TABLE IF EXISTS`

### ❌ "Syntax error near ENUM"
- PostgreSQL version too old
- Supabase uses PostgreSQL 14+ (should be fine)
- Check Supabase project settings

### ❌ "Connection refused" in API test
- Network/firewall issue
- Check `.env.supabase` SUPABASE_URL is correct
- Verify internet connection

---

## 📞 Need Help?

1. **Schema import errors?** → Check MIGRATION_GUIDE.md "Common Errors"
2. **API connection errors?** → Check SCHEMA_MIGRATION_QUICKREF.md "Troubleshooting"
3. **Database questions?** → Check DATABASE_SCHEMA_DOCS.md
4. **Full walkthrough?** → Follow MIGRATION_IMPLEMENTATION_CHECKLIST.md

---

## 🎯 Next Steps After Verification

Once all items in ✅ SUCCESS CHECKLIST are checked:

1. **Optional:** Migrate existing MySQL data
   ```bash
   python migrate_to_supabase.py
   ```

2. **Test Flask app:**
   ```bash
   python app.py
   ```

3. **Run full test suite:**
   ```bash
   python comprehensive_test_suite.py
   ```

4. **Test in browser:**
   - Go to http://localhost:5000/login.html
   - Login: admin / admin123
   - Should see dashboard with Supabase data

5. **Change admin password:**
   - Don't forget to change from "admin123" before production!

---

**You're almost there!** 🚀

Keep this checklist handy to verify your import was successful.
