#!/usr/bin/env python3
"""
Fix admin user password script
This script checks and fixes the admin user password
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
import bcrypt

def check_and_fix_admin():
    """Check and fix admin user password"""
    db = DatabaseManager()
    
    try:
        # Check if admin user exists
        result = db.execute_query("SELECT * FROM users WHERE username = 'admin'")
        
        if not result:
            print("❌ Admin user not found!")
            return False
        
        admin_user = result[0]
        print(f"✅ Admin user found: {admin_user['username']}")
        print(f"   Current password hash: {admin_user['password_hash'][:20]}...")
        
        # Test current password
        test_password = "admin123"
        current_hash = admin_user['password_hash']
        
        try:
            if current_hash.startswith('$2b$'):
                # bcrypt hash
                is_valid = bcrypt.checkpw(test_password.encode('utf-8'), current_hash.encode('utf-8'))
            else:
                # werkzeug hash
                from werkzeug.security import check_password_hash
                is_valid = check_password_hash(current_hash, test_password)
            
            if is_valid:
                print("✅ Current password is correct!")
                return True
            else:
                print("❌ Current password is incorrect, updating...")
        except Exception as e:
            print(f"❌ Error checking password: {e}")
            print("🔄 Updating password hash...")
        
        # Update password with bcrypt
        new_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        
        db.execute_update(
            "UPDATE users SET password_hash = %s WHERE username = 'admin'",
            (new_hash.decode('utf-8'),)
        )
        
        print("✅ Admin password updated successfully!")
        print(f"   New password hash: {new_hash.decode('utf-8')[:20]}...")
        
        # Test the new password
        test_result = db.execute_query("SELECT password_hash FROM users WHERE username = 'admin'")
        if test_result:
            test_hash = test_result[0]['password_hash']
            is_valid = bcrypt.checkpw(test_password.encode('utf-8'), test_hash.encode('utf-8'))
            if is_valid:
                print("✅ Password verification successful!")
                return True
        
        print("❌ Password verification failed!")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Checking and fixing admin user password...")
    print("=" * 50)
    
    success = check_and_fix_admin()
    
    if success:
        print("\n🎉 Admin user is ready!")
        print("📝 You can now login with:")
        print("   Username: admin")
        print("   Password: admin123")
    else:
        print("\n❌ Failed to fix admin user")
        sys.exit(1)