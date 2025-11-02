#!/usr/bin/env python3
"""
Test login functionality
"""

import requests
import json

def test_login():
    """Test login with admin credentials"""
    url = "http://127.0.0.1:5000/api/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("🔐 Testing login with admin credentials...")
        response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"Token: {result.get('token', 'No token')[:50]}...")
            print(f"User: {result.get('user', {})}")
            return result.get('token')
        else:
            print("❌ Login failed!")
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def test_health():
    """Test health endpoint"""
    try:
        print("🏥 Testing health endpoint...")
        response = requests.get("http://127.0.0.1:5000/api/health")
        print(f"Health Status: {response.status_code}")
        print(f"Health Response: {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing ReconX API...")
    print("=" * 50)
    
    # Test health first
    if test_health():
        print("\n✅ Health check passed!")
        
        # Test login
        token = test_login()
        if token:
            print("\n🎉 All tests passed! Ready to test file uploads.")
        else:
            print("\n❌ Login test failed.")
    else:
        print("\n❌ Health check failed. App may not be running.")
