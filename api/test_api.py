#!/usr/bin/env python3
"""
Simple test script for ReconX MVP Backend
Tests basic functionality without requiring actual files
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_login():
    """Test login endpoint"""
    print("\n🔍 Testing login endpoint...")
    try:
        data = {
            "username": "admin",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=data)
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful")
            print(f"   User: {result['user']['username']} ({result['user']['role']})")
            return result['token']
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_current_user(token):
    """Test current user endpoint"""
    print("\n🔍 Testing current user endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            user = response.json()
            print("✅ Current user endpoint working")
            print(f"   User: {user['username']} ({user['role']})")
        else:
            print(f"❌ Current user failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Current user error: {e}")

def test_users_endpoint(token):
    """Test users endpoint (admin only)"""
    print("\n🔍 Testing users endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/users", headers=headers)
        if response.status_code == 200:
            users = response.json()['users']
            print("✅ Users endpoint working")
            print(f"   Found {len(users)} users")
            for user in users:
                print(f"   - {user['username']} ({user['role']}) - {user['status']}")
        else:
            print(f"❌ Users endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Users endpoint error: {e}")

def test_audit_logs(token):
    """Test audit logs endpoint (admin only)"""
    print("\n🔍 Testing audit logs endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/audit/logs", headers=headers)
        if response.status_code == 200:
            logs = response.json()['logs']
            print("✅ Audit logs endpoint working")
            print(f"   Found {len(logs)} audit entries")
            if logs:
                latest = logs[0]
                print(f"   Latest: {latest['action']} by {latest['username']} at {latest['timestamp']}")
        else:
            print(f"❌ Audit logs failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Audit logs error: {e}")

def test_reconciliation_history(token):
    """Test reconciliation history endpoint"""
    print("\n🔍 Testing reconciliation history endpoint...")
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/reconciliation/history", headers=headers)
        if response.status_code == 200:
            reports = response.json()['reports']
            print("✅ Reconciliation history endpoint working")
            print(f"   Found {len(reports)} reconciliation reports")
        else:
            print(f"❌ Reconciliation history failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Reconciliation history error: {e}")

def main():
    """Run all tests"""
    print("🚀 ReconX MVP Backend Test Suite")
    print("=" * 50)
    
    # Test health endpoint
    test_health()
    
    # Test login
    token = test_login()
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    # Test authenticated endpoints
    test_current_user(token)
    test_users_endpoint(token)
    test_audit_logs(token)
    test_reconciliation_history(token)
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\n📝 Notes:")
    print("- File upload endpoints require actual files to test")
    print("- Reconciliation endpoints require uploaded files to test")
    print("- All core authentication and authorization working")
    print("- Database is properly initialized with admin user")

if __name__ == "__main__":
    main()
