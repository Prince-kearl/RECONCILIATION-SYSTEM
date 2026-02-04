#!/usr/bin/env python3
"""
Check roles table and admin user data
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager

def check_roles_and_admin():
    """Check roles table and admin user data"""
    
    print("🔍 Checking Roles Table and Admin User")
    print("=" * 50)
    
    db = DatabaseManager()
    
    try:
        # Check if roles table exists
        print("1. Checking roles table...")
        try:
            roles_query = "SELECT * FROM roles"
            roles = db.execute_query(roles_query)
            print(f"✅ Roles table exists with {len(roles)} roles:")
            for role in roles:
                print(f"   - {role['role_name']} (ID: {role['role_id']})")
        except Exception as e:
            print(f"❌ Roles table error: {e}")
            return False
        
        # Check admin user data
        print("\n2. Checking admin user data...")
        try:
            admin_query = """
                SELECT u.*, r.role_name 
                FROM users u 
                LEFT JOIN roles r ON u.role_id = r.role_id 
                WHERE u.username = 'admin'
            """
            admin_result = db.execute_query(admin_query)
            
            if admin_result:
                admin = admin_result[0]
                print(f"✅ Admin user found:")
                for key, value in admin.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ Admin user not found!")
                return False
        except Exception as e:
            print(f"❌ Admin user query error: {e}")
            return False
        
        # Test the exact query used by user_manager
        print("\n3. Testing user_manager query...")
        try:
            user_manager_query = """
                SELECT u.*, r.role_name 
                FROM users u 
                JOIN roles r ON u.role_id = r.role_id 
                WHERE u.username = %s
            """
            result = db.execute_query(user_manager_query, ('admin',))
            
            if result:
                user_data = result[0]
                print(f"✅ User manager query result:")
                for key, value in user_data.items():
                    print(f"   {key}: {value}")
            else:
                print("❌ User manager query returned no results!")
                return False
        except Exception as e:
            print(f"❌ User manager query error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ General error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login_again():
    """Test login again"""
    print("\n🧪 Testing login again...")
    
    try:
        import requests
        
        # Test login
        login_url = "http://localhost:5000/api/auth/login"
        login_data = {"username": "admin", "password": "admin123"}
        
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"✅ Token: {data['token'][:50]}...")
            print(f"✅ User data: {data.get('user', {})}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ReconX Database Check")
    print("=" * 50)
    
    if check_roles_and_admin():
        print("\n" + "=" * 50)
        test_login_again()
    else:
        print("\n❌ Database check failed")

if __name__ == "__main__":
    main()
