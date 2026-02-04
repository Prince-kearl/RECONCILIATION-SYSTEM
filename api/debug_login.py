#!/usr/bin/env python3
"""
Debug login issues by testing database connection and user lookup
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Test direct database connection"""
    try:
        from database import user_manager
        print("✅ Database connection successful")
        
        # Test getting admin user
        user = user_manager.get_user_by_username("admin")
        if user:
            print(f"✅ Admin user found: {user}")
            print(f"   Username: {user.get('username')}")
            print(f"   Password Hash: {user.get('password_hash')[:20]}...")
            print(f"   Status: {user.get('status')}")
            print(f"   Role: {user.get('role_name')}")
            return user
        else:
            print("❌ Admin user not found in database")
            return None
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def test_password_verification():
    """Test password verification"""
    try:
        import bcrypt
        from werkzeug.security import check_password_hash
        
        # Test bcrypt password
        password = "admin123"
        hash_bcrypt = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/RK.s5uO.G"
        
        print(f"Testing password: {password}")
        print(f"Testing hash: {hash_bcrypt}")
        
        # Test bcrypt
        result_bcrypt = bcrypt.checkpw(password.encode('utf-8'), hash_bcrypt.encode('utf-8'))
        print(f"Bcrypt result: {result_bcrypt}")
        
        # Test werkzeug
        result_werkzeug = check_password_hash(hash_bcrypt, password)
        print(f"Werkzeug result: {result_werkzeug}")
        
        return result_bcrypt or result_werkzeug
        
    except Exception as e:
        print(f"❌ Password verification failed: {e}")
        return False

def test_user_service():
    """Test user service directly"""
    try:
        from services.user_service import UserService
        
        service = UserService()
        user = service.get_by_username("admin")
        
        if user:
            print(f"✅ User service works: {user}")
            return user
        else:
            print("❌ User service failed to find admin user")
            return None
            
    except Exception as e:
        print(f"❌ User service failed: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Debugging Login Issues...")
    print("=" * 50)
    
    # Test database connection
    user = test_database_connection()
    
    if user:
        print("\n" + "=" * 30)
        # Test password verification
        password_ok = test_password_verification()
        
        print("\n" + "=" * 30)
        # Test user service
        service_user = test_user_service()
        
        if password_ok and service_user:
            print("\n✅ All components working! Login should work.")
        else:
            print("\n❌ Found issues with password verification or user service.")
    else:
        print("\n❌ Database connection failed. Cannot proceed with login tests.")
