#!/usr/bin/env python3
"""
Fix admin account status issue
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager

def fix_admin_status():
    """Fix admin account status"""
    
    print("🔧 Fixing Admin Account Status")
    print("=" * 40)
    
    db = DatabaseManager()
    
    try:
        # Check current admin account
        print("🔍 Checking admin account...")
        admin_query = "SELECT * FROM users WHERE username = 'admin'"
        admin_result = db.execute_query(admin_query)
        
        if not admin_result:
            print("❌ Admin account not found!")
            return False
        
        admin = admin_result[0]
        print(f"📊 Current admin data:")
        for key, value in admin.items():
            print(f"   {key}: {value}")
        
        # The issue is that the current database doesn't have a 'status' column
        # but the auth controller is checking for it. Let's add the status column
        print("\n🔧 Adding status column to users table...")
        
        try:
            # Try to add the status column
            alter_query = """
                ALTER TABLE users 
                ADD COLUMN status ENUM('active', 'inactive', 'locked', 'pending_verification') 
                DEFAULT 'active'
            """
            db.execute_update(alter_query)
            print("✅ Status column added successfully!")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("✅ Status column already exists!")
            else:
                print(f"⚠️  Could not add status column: {e}")
        
        # Set admin status to active
        print("\n🔧 Setting admin status to active...")
        try:
            update_query = "UPDATE users SET status = 'active' WHERE username = 'admin'"
            affected_rows = db.execute_update(update_query)
            print(f"✅ Updated {affected_rows} admin account(s) to active status")
        except Exception as e:
            print(f"⚠️  Could not update status: {e}")
        
        # Verify the fix
        print("\n🔍 Verifying fix...")
        verify_result = db.execute_query(admin_query)
        if verify_result:
            admin = verify_result[0]
            print(f"📊 Updated admin data:")
            for key, value in admin.items():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_login():
    """Test login with admin credentials"""
    print("\n🧪 Testing admin login...")
    
    try:
        import requests
        
        # Test login
        login_url = "http://localhost:5000/api/auth/login"
        login_data = {"username": "admin", "password": "admin123"}
        
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Login successful!")
            print(f"✅ Token received: {data['token'][:50]}...")
            print(f"✅ User: {data['user']['full_name']}")
            print(f"✅ Role: {data['user']['role_name']}")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ReconX Admin Account Status Fix")
    print("=" * 50)
    
    # Step 1: Fix the account status
    if fix_admin_status():
        print("\n" + "=" * 50)
        
        # Step 2: Test login
        if test_login():
            print("\n🎉 SUCCESS! Admin account is now working!")
            print("\n📋 You can now:")
            print("   ✅ Log in with username: admin")
            print("   ✅ Password: admin123")
            print("   ✅ Access the reconciliation dashboard")
        else:
            print("\n⚠️  Status fixed but login test failed.")
            print("   Check if the server is running on http://localhost:5000")
    else:
        print("\n❌ Failed to fix admin account status")

if __name__ == "__main__":
    main()
