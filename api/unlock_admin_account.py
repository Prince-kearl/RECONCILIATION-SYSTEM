#!/usr/bin/env python3
"""
Script to unlock admin account and reset failed login attempts
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
from datetime import datetime, timedelta

def unlock_admin_account():
    """Unlock admin account and reset failed login attempts"""
    
    print("🔓 Unlocking Admin Account")
    print("=" * 40)
    
    db = DatabaseManager()
    
    try:
        # Check current admin account status
        print("🔍 Checking admin account status...")
        admin_query = """
            SELECT user_id, username, status, failed_login_attempts, 
                   account_locked_until, last_login
            FROM users 
            WHERE username = 'admin'
        """
        admin_result = db.execute_query(admin_query)
        
        if not admin_result:
            print("❌ Admin account not found!")
            return False
        
        admin = admin_result[0]
        print(f"📊 Current admin status:")
        print(f"   User ID: {admin['user_id']}")
        print(f"   Username: {admin['username']}")
        print(f"   Status: {admin['status']}")
        print(f"   Failed attempts: {admin['failed_login_attempts']}")
        print(f"   Locked until: {admin['account_locked_until']}")
        print(f"   Last login: {admin['last_login']}")
        
        # Reset failed login attempts and unlock account
        print("\n🔧 Resetting failed login attempts and unlocking account...")
        
        unlock_query = """
            UPDATE users 
            SET failed_login_attempts = 0,
                status = 'active',
                account_locked_until = NULL,
                updated_at = %s
            WHERE username = 'admin'
        """
        
        affected_rows = db.execute_update(unlock_query, (datetime.now(),))
        
        if affected_rows > 0:
            print("✅ Admin account successfully unlocked!")
            print("✅ Failed login attempts reset to 0")
            print("✅ Account status set to 'active'")
            print("✅ Account lockout time cleared")
            
            # Verify the unlock
            print("\n🔍 Verifying unlock...")
            verify_result = db.execute_query(admin_query)
            if verify_result:
                admin = verify_result[0]
                print(f"✅ Status: {admin['status']}")
                print(f"✅ Failed attempts: {admin['failed_login_attempts']}")
                print(f"✅ Locked until: {admin['account_locked_until']}")
            
            return True
        else:
            print("❌ Failed to unlock admin account")
            return False
            
    except Exception as e:
        print(f"❌ Error unlocking admin account: {e}")
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
            print("\n🎉 SUCCESS! Admin account is now unlocked and working!")
            print("\n📋 You can now:")
            print("   ✅ Log in with username: admin")
            print("   ✅ Password: admin123")
            print("   ✅ Access the reconciliation dashboard")
        else:
            print("\n⚠️  Account unlocked but login test failed.")
            print("   Check if the server is running on http://localhost:5000")
    else:
        print("\n❌ Failed to unlock admin account")
        print("   Check database connection and permissions")

if __name__ == "__main__":
    main()
