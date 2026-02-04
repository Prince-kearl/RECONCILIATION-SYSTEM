#!/usr/bin/env python3
"""
Test script for file status API
"""

import requests
import json

def test_file_status():
    """Test the file status API"""
    
    # Get JWT token
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    
    print("🔐 Getting JWT token...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json()['token']
    print(f"✅ Login successful")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test file status summary
    print("\n📊 Testing file status summary...")
    response = requests.get("http://localhost:5000/api/files/status/summary", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("✅ File status summary:")
        print(f"   Total files: {data['summary']['total_files']}")
        print(f"   Processed: {data['summary']['processed_files']}")
        print(f"   Errors: {data['summary']['error_files']}")
        print(f"   Processing: {data['summary']['processing_files']}")
        
        print(f"\n📄 Bank Statement Status:")
        bank_status = data['bank_statement']
        print(f"   Status: {bank_status['status']}")
        if bank_status['filename']:
            print(f"   File: {bank_status['filename']}")
            print(f"   Records: {bank_status['records_count']}")
            print(f"   Size: {bank_status['file_size']} bytes")
            print(f"   Uploaded: {bank_status['uploaded_at']}")
        
        print(f"\n📋 Internal Record Status:")
        internal_status = data['internal_record']
        print(f"   Status: {internal_status['status']}")
        if internal_status['filename']:
            print(f"   File: {internal_status['filename']}")
            print(f"   Records: {internal_status['records_count']}")
            print(f"   Size: {internal_status['file_size']} bytes")
            print(f"   Uploaded: {internal_status['uploaded_at']}")
        
        # Show recent files
        if data['recent_files']['bank_statements']:
            print(f"\n📄 Recent Bank Statements:")
            for file in data['recent_files']['bank_statements']:
                print(f"   - {file['original_filename']} ({file['status']}) - {file.get('records_count', 0)} records")
        
        if data['recent_files']['internal_records']:
            print(f"\n📋 Recent Internal Records:")
            for file in data['recent_files']['internal_records']:
                print(f"   - {file['original_filename']} ({file['status']}) - {file.get('records_count', 0)} records")
        
    else:
        print(f"❌ Failed to get file status summary: {response.text}")
    
    # Test individual file uploads list
    print("\n📋 Testing file uploads list...")
    response = requests.get("http://localhost:5000/api/files/uploads", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['count']} uploaded files:")
        for file in data['files']:
            status_icon = "✅" if file['status'] == 'processed' else "⏳" if file['status'] == 'processing' else "❌"
            print(f"   {status_icon} {file['original_filename']} ({file['status']}) - {file.get('records_count', 0)} records")
    else:
        print(f"❌ Failed to get file uploads: {response.text}")

if __name__ == "__main__":
    print("🚀 Testing ReconX File Status API")
    print("=" * 50)
    test_file_status()
    print("\n✅ Test completed!")
