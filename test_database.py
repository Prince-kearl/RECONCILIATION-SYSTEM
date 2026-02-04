#!/usr/bin/env python3
"""
Database test script for ReconX
Tests the new MySQL database structure and managers
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_database_connection():
    """Test basic database connection"""
    print("🔌 Testing database connection...")
    
    try:
        from database import DatabaseConfig
        config = DatabaseConfig()
        connection = config.get_connection()
        print("✅ Database connection successful")
        connection.close()
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_user_manager():
    """Test user management functionality"""
    print("\n👥 Testing user manager...")
    
    try:
        from database import user_manager
        
        # Test getting admin user
        admin_user = user_manager.get_user_by_username('admin')
        if admin_user:
            print(f"✅ Admin user found: {admin_user['username']} ({admin_user['role_name']})")
        else:
            print("❌ Admin user not found")
            return False
        
        # Test getting all users
        users = user_manager.get_all_users()
        print(f"✅ Found {len(users)} users in system")
        
        return True
    except Exception as e:
        print(f"❌ User manager test failed: {e}")
        return False

def test_file_manager():
    """Test file management functionality"""
    print("\n📁 Testing file manager...")
    
    try:
        from database import file_manager
        
        # Test getting bank statements
        bank_statements = file_manager.get_bank_statements(limit=10)
        print(f"✅ Bank statements query successful: {len(bank_statements)} records")
        
        # Test getting internal records
        internal_records = file_manager.get_internal_records(limit=10)
        print(f"✅ Internal records query successful: {len(internal_records)} records")
        
        return True
    except Exception as e:
        print(f"❌ File manager test failed: {e}")
        return False

def test_audit_manager():
    """Test audit logging functionality"""
    print("\n📝 Testing audit manager...")
    
    try:
        from database import audit_manager
        
        # Test getting audit logs
        logs = audit_manager.get_audit_logs(limit=10)
        print(f"✅ Audit logs query successful: {len(logs)} records")
        
        return True
    except Exception as e:
        print(f"❌ Audit manager test failed: {e}")
        return False

def test_reconciliation_manager():
    """Test reconciliation manager functionality"""
    print("\n🔄 Testing reconciliation manager...")
    
    try:
        from database import reconciliation_manager
        
        # Test getting reconciliation results
        results = reconciliation_manager.get_reconciliation_results(limit=10)
        print(f"✅ Reconciliation results query successful: {len(results)} records")
        
        return True
    except Exception as e:
        print(f"❌ Reconciliation manager test failed: {e}")
        return False

def test_database_schema():
    """Test database schema and tables"""
    print("\n🗄️ Testing database schema...")
    
    try:
        from database import DatabaseConfig
        config = DatabaseConfig()
        connection = config.get_connection()
        
        with connection.cursor() as cursor:
            # Check if all required tables exist
            cursor.execute("SHOW TABLES")
            tables = [row['Tables_in_reconx'] for row in cursor.fetchall()]
            
            required_tables = [
                'users', 'roles', 'bank_statements', 
                'internal_records', 'reconciliation_results', 'audit_logs'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            print(f"✅ All required tables exist: {', '.join(tables)}")
            
            # Check table structures
            for table in required_tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                print(f"   📋 {table}: {len(columns)} columns")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 ReconX Database Test Suite")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Database Schema", test_database_schema),
        ("User Manager", test_user_manager),
        ("File Manager", test_file_manager),
        ("Audit Manager", test_audit_manager),
        ("Reconciliation Manager", test_reconciliation_manager)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"⚠️  {test_name} test failed")
        except Exception as e:
            print(f"❌ {test_name} test error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Database is ready.")
        print("\n📝 Next steps:")
        print("   1. Start the Flask backend: python app.py")
        print("   2. Test the API endpoints")
        print("   3. Default admin credentials: admin / admin123")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure MySQL is running")
        print("   2. Check database credentials in .env file")
        print("   3. Run setup_database.py if needed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
