#!/usr/bin/env python3
"""
Check what tables exist in the database
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager

def check_database_tables():
    """Check what tables exist in the database"""
    
    print("🔍 Checking Database Tables")
    print("=" * 40)
    
    db = DatabaseManager()
    
    try:
        # Get list of tables
        tables_query = "SHOW TABLES"
        tables = db.execute_query(tables_query)
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            table_name = list(table.values())[0]
            print(f"   - {table_name}")
        
        # Check if file_uploads table exists
        file_uploads_exists = any('file_uploads' in str(table) for table in tables)
        print(f"\n📁 file_uploads table exists: {file_uploads_exists}")
        
        if file_uploads_exists:
            # Check file_uploads table structure
            print("\n🔍 file_uploads table structure:")
            structure_query = "DESCRIBE file_uploads"
            columns = db.execute_query(structure_query)
            for col in columns:
                print(f"   - {col['Field']} ({col['Type']})")
        
        # Check users table structure
        print("\n👤 users table structure:")
        users_structure = db.execute_query("DESCRIBE users")
        for col in users_structure:
            print(f"   - {col['Field']} ({col['Type']})")
        
        # Check if we have any uploaded files in existing tables
        print("\n📊 Checking for existing file data...")
        
        # Check bank_statements table
        try:
            bank_count = db.execute_query("SELECT COUNT(*) as count FROM bank_statements")
            print(f"   Bank statements: {bank_count[0]['count']} records")
        except Exception as e:
            print(f"   Bank statements table: {e}")
        
        # Check internal_records table  
        try:
            internal_count = db.execute_query("SELECT COUNT(*) as count FROM internal_records")
            print(f"   Internal records: {internal_count[0]['count']} records")
        except Exception as e:
            print(f"   Internal records table: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ReconX Database Table Checker")
    print("=" * 50)
    
    check_database_tables()

if __name__ == "__main__":
    main()
