#!/bin/bash
# Supabase Schema Import Assistant
# This script helps you import the PostgreSQL schema to your Supabase project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   ReconX MySQL to Supabase PostgreSQL Schema Import Tool       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Verify environment
echo -e "${BLUE}Step 1: Verifying environment...${NC}"

if [ ! -f ".env.supabase" ]; then
    echo -e "${RED}✗ .env.supabase file not found${NC}"
    exit 1
fi

if [ ! -f "database_schema_postgresql.sql" ]; then
    echo -e "${RED}✗ database_schema_postgresql.sql file not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment files found${NC}"

# Step 2: Load credentials
echo -e "${BLUE}Step 2: Loading Supabase credentials...${NC}"
source .env.supabase

if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo -e "${RED}✗ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Credentials loaded${NC}"
echo "  Project: $SUPABASE_URL"

# Step 3: Check PostgreSQL connectivity option
echo -e "${BLUE}Step 3: Import options${NC}"
echo "  Option A: Via Supabase SQL Editor (Recommended - Web UI)"
echo "  Option B: Via psql command line (if PostgreSQL installed locally)"
echo ""

# Verify psql availability for Option B
if command -v psql &> /dev/null; then
    PSQL_AVAILABLE=true
    PSQL_VERSION=$(psql --version | awk '{print $3}')
    echo -e "${GREEN}✓ PostgreSQL client available (v$PSQL_VERSION)${NC}"
else
    PSQL_AVAILABLE=false
    echo -e "${YELLOW}⚠ PostgreSQL client (psql) not found${NC}"
fi

# Step 4: Show manual import instructions
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║                 MANUAL IMPORT VIA WEB UI (OPTION A)             ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

cat << 'EOF'

STEP-BY-STEP INSTRUCTIONS:

1. Open Supabase Dashboard:
   → Go to https://app.supabase.com
   → Select your project: reconx-db
   → Left sidebar → SQL Editor

2. Create New Query:
   → Click "+ New Query" or "New" button
   → You'll see a blank SQL editor

3. Copy the Schema:
   → Open this file in your text editor: database_schema_postgresql.sql
   → Select ALL content (Cmd+A)
   → Copy (Cmd+C)

4. Paste into Supabase:
   → In the SQL Editor, click in the text area
   → Paste the entire schema (Cmd+V)
   → You should see the SQL code in the editor

5. Execute the Import:
   → Click the "▶ Run" button (top right corner)
   → The query will execute
   → Status bar at bottom should show "Statement executed successfully"
   → This typically takes 10-30 seconds

6. Verify Success:
   → In left sidebar, expand "Tables" section
   → You should see 11 new tables:
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

TIMING: 5 minutes total

If you see any errors, note the error message and check:
→ MIGRATION_GUIDE.md "Common Errors & Solutions" section

EOF

# Step 5: Offer command line option if available
if [ "$PSQL_AVAILABLE" = true ]; then
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║               ALTERNATIVE: COMMAND LINE OPTION (B)              ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    
    cat << 'EOF'

Commands to run in terminal:

1. Copy database host from .env.supabase:
   DB_HOST=db.vlwdzlrphofhevfllrgp.supabase.co
   DB_NAME=postgres
   DB_USER=postgres

2. Import schema via psql:
   psql -h db.vlwdzlrphofhevfllrgp.supabase.co \
        -U postgres \
        -d postgres \
        -f database_schema_postgresql.sql

3. When prompted for password, enter your Supabase database password
   (from .env.supabase → DB_PASSWORD)

4. Wait for import to complete (should show no errors)

5. Verify tables were created:
   psql -h db.vlwdzlrphofhevfllrgp.supabase.co \
        -U postgres \
        -d postgres \
        -c "\dt public.*"

TIMING: 5 minutes total

WARNING: Direct PostgreSQL connections may fail due to DNS issues on macOS.
If you get "could not translate host name" error, use Option A (Web UI) instead.

EOF
fi

# Step 6: Post-import instructions
echo ""
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              AFTER SUCCESSFUL IMPORT: VERIFICATION              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"

cat << 'EOF'

1. In Supabase SQL Editor, create a NEW query and run:

   SELECT COUNT(*) as table_count FROM information_schema.tables 
   WHERE table_schema = 'public';

   Expected result: 11 tables

2. Check roles were inserted:

   SELECT * FROM roles;

   Expected: 4 rows (admin, finance_officer, auditor, viewer)

3. Check admin user created:

   SELECT user_id, username, email, role_id, status FROM users 
   WHERE username = 'admin';

   Expected: 1 row with status='active'

4. Back in terminal, test API connection:

   python test_supabase_api.py

   Expected output:
   Status code: 200
   ✅ HTTP API Connection Successful!

═══════════════════════════════════════════════════════════════════════════════

NEXT STEPS AFTER VERIFICATION:

✓ Read: MIGRATION_IMPLEMENTATION_CHECKLIST.md
✓ Update Flask app (if needed)
✓ Test endpoints
✓ Migrate existing MySQL data (if applicable)

═══════════════════════════════════════════════════════════════════════════════

More help:
→ MIGRATION_GUIDE.md - Full step-by-step guide
→ SCHEMA_MIGRATION_QUICKREF.md - Quick reference
→ DATABASE_SCHEMA_DOCS.md - Technical documentation
→ MIGRATE_TO_SUPABASE.md - Data migration guide

Good luck! 🚀

EOF

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Ready to import? Choose Option A or B above and follow the instructions.${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════════${NC}"
echo ""
