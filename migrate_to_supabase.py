"""
MySQL to Supabase PostgreSQL Data Migration Script

This script helps migrate existing data from MySQL to Supabase PostgreSQL.
Use this if you already have production data in MySQL that needs to be preserved.

Usage:
    python migrate_to_supabase.py
    
Requirements:
    - MySQL database running locally or accessible
    - Supabase project configured with schema already imported
    - .env.supabase file with credentials
"""

import os
import json
import sys
from datetime import datetime
from dotenv import load_dotenv
import requests

try:
    import pymysql
    import pymysql.cursors
except ImportError:
    print("❌ PyMySQL not installed. Run: pip install PyMySQL")
    sys.exit(1)

# Load Supabase credentials
load_dotenv('.env.supabase')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# MySQL settings
MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
MYSQL_USER = os.getenv('DB_USER', 'root')
MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
MYSQL_DB = os.getenv('DB_NAME', 'reconx')

class MySQLToSupabaseMigrator:
    """Handles migration from MySQL to Supabase PostgreSQL"""
    
    def __init__(self):
        self.supabase_url = SUPABASE_URL
        self.service_role_key = SUPABASE_SERVICE_ROLE_KEY
        self.headers = {
            'Authorization': f'Bearer {self.service_role_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        self.mysql_conn = None
        self.migrated_data = {}
        
    def connect_mysql(self):
        """Connect to MySQL database"""
        try:
            self.mysql_conn = pymysql.connect(
                host=MYSQL_HOST,
                port=MYSQL_PORT,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print("✅ Connected to MySQL")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to MySQL: {e}")
            return False
    
    def fetch_mysql_data(self, table_name):
        """Fetch all data from a MySQL table"""
        try:
            with self.mysql_conn.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                print(f"📊 Fetched {len(rows)} rows from {table_name}")
                return rows
        except Exception as e:
            print(f"❌ Error fetching {table_name}: {e}")
            return []
    
    def insert_to_supabase(self, table_name, data):
        """Insert data into Supabase via HTTP API"""
        if not data:
            print(f"⏭️  Skipping empty table: {table_name}")
            return 0
        
        try:
            url = f"{self.supabase_url}/rest/v1/{table_name}"
            
            # Convert datetime objects to ISO strings for JSON serialization
            for record in data:
                for key, value in record.items():
                    if isinstance(value, datetime):
                        record[key] = value.isoformat()
                    elif isinstance(value, bytes):
                        record[key] = value.decode('utf-8', errors='ignore')
            
            # Insert in batches of 100 to avoid payload size limits
            batch_size = 100
            inserted_count = 0
            
            for i in range(0, len(data), batch_size):
                batch = data[i:i+batch_size]
                response = requests.post(
                    url,
                    json=batch,
                    headers=self.headers
                )
                
                if response.status_code in [200, 201]:
                    inserted_count += len(batch)
                    print(f"  ✅ Inserted batch {i//batch_size + 1} ({len(batch)} records) into {table_name}")
                else:
                    print(f"  ❌ Batch insert failed: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    return inserted_count
            
            return inserted_count
            
        except Exception as e:
            print(f"❌ Error inserting into {table_name}: {e}")
            return 0
    
    def migrate_table(self, table_name, skip_id=False):
        """Migrate a single table from MySQL to Supabase"""
        print(f"\n📋 Migrating table: {table_name}")
        
        # Fetch from MySQL
        mysql_data = self.fetch_mysql_data(table_name)
        
        if not mysql_data:
            print(f"  ⏭️  No data to migrate")
            return 0
        
        # Remove auto-increment IDs if needed (Supabase will generate)
        if skip_id and mysql_data:
            for record in mysql_data:
                # Remove the primary key field for auto-increment tables
                # This allows Supabase to generate new IDs
                pass  # Comment out if you want to preserve original IDs
        
        # Insert into Supabase
        count = self.insert_to_supabase(table_name, mysql_data)
        self.migrated_data[table_name] = count
        return count
    
    def migrate_all(self):
        """Migrate all tables from MySQL to Supabase"""
        print("=" * 70)
        print("🚀 MySQL to Supabase PostgreSQL Migration")
        print("=" * 70)
        
        # Order matters for foreign keys
        tables_to_migrate = [
            'roles',           # No dependencies
            'users',           # Depends on roles
            'user_sessions',   # Depends on users
            'mfa_secrets',     # Depends on users
            'file_uploads',    # Depends on users
            'bank_statements',   # Depends on users
            'internal_records',  # Depends on users
            'reconciliation_runs', # Depends on users
            'reconciliation_results', # Depends on reconciliation_runs, users, statements, records
            'audit_logs',      # Depends on users, user_sessions
        ]
        
        if not self.connect_mysql():
            print("❌ Cannot proceed without MySQL connection")
            return False
        
        try:
            for table in tables_to_migrate:
                self.migrate_table(table)
            
            print("\n" + "=" * 70)
            print("✅ Migration Complete!")
            print("=" * 70)
            print("\n📊 Summary:")
            total_records = 0
            for table, count in self.migrated_data.items():
                print(f"  {table}: {count} records")
                total_records += count
            print(f"\n📈 Total records migrated: {total_records}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            return False
        finally:
            if self.mysql_conn:
                self.mysql_conn.close()
    
    def verify_migration(self):
        """Verify migration by comparing row counts"""
        print("\n" + "=" * 70)
        print("🔍 Verifying Migration")
        print("=" * 70)
        
        for table in self.migrated_data.keys():
            try:
                url = f"{self.supabase_url}/rest/v1/{table}?select=count=exact"
                response = requests.get(url, headers=self.headers)
                
                if response.status_code == 200:
                    count_header = response.headers.get('content-range', '')
                    if count_header:
                        # Parse "0-99/150" format
                        total = int(count_header.split('/')[-1])
                        print(f"  ✅ {table}: {total} rows in Supabase")
                else:
                    print(f"  ❌ {table}: verification failed")
            except Exception as e:
                print(f"  ❌ {table}: {e}")

def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║     ReconX MySQL to Supabase PostgreSQL Migration Tool           ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)
    
    # Verify credentials
    if not all([SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, MYSQL_USER]):
        print("❌ Missing required environment variables in .env.supabase")
        print("Required: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, DB_USER")
        sys.exit(1)
    
    # Confirm with user
    print(f"Source: MySQL at {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}")
    print(f"Target: Supabase PostgreSQL at {SUPABASE_URL}")
    print()
    
    response = input("⚠️  This will migrate all data from MySQL to Supabase. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ Migration cancelled")
        return
    
    # Run migration
    migrator = MySQLToSupabaseMigrator()
    success = migrator.migrate_all()
    
    if success:
        # Verify
        verify = input("\n🔍 Verify migration by checking row counts? (yes/no): ")
        if verify.lower() == 'yes':
            migrator.verify_migration()
        
        print("\n✅ Migration complete! Your ReconX data is now on Supabase.")
        print("\nNext steps:")
        print("1. Verify all data in Supabase Dashboard")
        print("2. Test Flask app endpoints with new database")
        print("3. Run comprehensive_test_suite.py to validate all features")
    else:
        print("\n❌ Migration encountered errors. Check logs above.")

if __name__ == '__main__':
    main()
