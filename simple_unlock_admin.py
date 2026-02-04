#!/usr/bin/env python3
"""
Simple script to unlock admin account
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
from datetime import datetime

def unlock_admin_account():
    """Unlock admin account and reset failed login attempts"""
    
    print("🔓 Unlocking Admin Account")
    print("=" * 40)
    
    db = DatabaseManager()
    
    try:
        # First, let's check what columns exist in the users table
        print("🔍 Checking users table structure...")
        structure_query = "DESCRIBE users"
        columns = db.execute_query(structure_query)
        
        print("📋 Available columns:")
        for col in columns:
            print(f"   - {col['Field']} ({col['Type']})")
        
        # Check current admin account
        print("\n🔍 Checking admin account...")
        admin_query = "SELECT * FROM users WHERE username = 'admin'"
        admin_result = db.execute_query(admin_query)
        
        if not admin_result:
            print("❌ Admin account not found!")
            return False
        
        admin = admin_result[0]
        print(f"📊 Current admin data:")
        for key, value in admin.items():
            print(f"   {key}: {value}")
        
        # Try to reset failed login attempts (if column exists)
        update_fields = []
        update_values = []
        
        # Check if failed_login_attempts column exists
        if 'failed_login_attempts' in admin:
            update_fields.append("failed_login_attempts = %s")
            update_values.append(0)
        
        # Check if status column exists
        if 'status' in admin:
            update_fields.append("status = %s")
            update_values.append('active')
        
        # Check if account_locked_until column exists
        if 'account_locked_until' in admin:
            update_fields.append("account_locked_until = NULL")
        
        if update_fields:
            print(f"\n🔧 Updating admin account...")
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = 'admin'"
            print(f"Query: {update_query}")
            print(f"Values: {update_values}")
            
            affected_rows = db.execute_update(update_query, tuple(update_values))
            
            if affected_rows > 0:
                print("✅ Admin account successfully updated!")
                
                # Verify the update
                print("\n🔍 Verifying update...")
                verify_result = db.execute_query(admin_query)
                if verify_result:
                    admin = verify_result[0]
                    print(f"📊 Updated admin data:")
                    for key, value in admin.items():
                        print(f"   {key}: {value}")
                
                return True
            else:
                print("❌ Failed to update admin account")
                return False
        else:
            print("⚠️  No security columns found to update")
            print("✅ Admin account exists and should be accessible")
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
    print("🚀 ReconX Admin Account Unlock Tool")
    print("=" * 50)
    
    # Step 1: Unlock the account
    if unlock_admin_account():
        print("\n" + "=" * 50)
        
        # Step 2: Test login
        if test_login():
            print("\n🎉 SUCCESS! Admin account is now working!")
            print("\n📋 You can now:")
            print("   ✅ Log in with username: admin")
            print("   ✅ Password: admin123")
            print("   ✅ Access the reconciliation dashboard")
        else:
            print("\n⚠️  Account updated but login test failed.")
            print("   Check if the server is running on http://localhost:5000")
    else:
        print("\n❌ Failed to unlock admin account")
        print("   Check database connection and permissions")

if __name__ == "__main__":
    main()
