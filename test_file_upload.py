#!/usr/bin/env python3
"""
Test script for file upload functionality
"""

import requests
import os
import json

def test_file_upload():
    """Test the file upload functionality"""
    
    # Get JWT token
    login_url = "http://localhost:5000/api/auth/login"
    login_data = {"username": "admin", "password": "admin123"}
    
    print("🔐 Getting JWT token...")
    response = requests.post(login_url, json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    token = response.json()['token']
    print(f"✅ Login successful, token: {token[:50]}...")
    
    # Test file uploads list (should be empty initially)
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n📋 Getting file uploads list...")
    response = requests.get("http://localhost:5000/api/files/uploads", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File uploads list: {data['count']} files")
        if data['files']:
            for file in data['files']:
                print(f"   - {file['original_filename']} ({file['status']})")
    else:
        print(f"❌ Failed to get file uploads: {response.text}")
    
    # Test bank statement upload
    print("\n📤 Testing bank statement upload...")
    
    # Create test file content
    test_content = """date,amount,ref,description,branch
2024-01-15,1500.00,REF001,Payment from Customer A,Main Branch
2024-01-16,2500.50,REF002,Service Payment,Main Branch
2024-01-17,750.25,REF003,Refund Processing,Main Branch"""
    
    # Write test file
    with open("test_upload.csv", "w") as f:
        f.write(test_content)
    
    # Upload file
    with open("test_upload.csv", "rb") as f:
        files = {"file": ("test_bank_statement.csv", f, "text/csv")}
        response = requests.post("http://localhost:5000/api/files/upload/bank-statement", 
                               headers=headers, files=files)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Bank statement uploaded successfully!")
        print(f"   Upload ID: {data['upload_id']}")
        print(f"   Records processed: {data['records_count']}")
        print(f"   Status: {data['status']}")
        print(f"   File size: {data['file_size']} bytes")
        
        upload_id = data['upload_id']
        
        # Test getting specific file upload
        print(f"\n🔍 Getting file upload details for ID {upload_id}...")
        response = requests.get(f"http://localhost:5000/api/files/uploads/{upload_id}", headers=headers)
        
        if response.status_code == 200:
            file_data = response.json()
            print(f"✅ File details retrieved:")
            print(f"   Original filename: {file_data['file']['original_filename']}")
            print(f"   Status: {file_data['file']['status']}")
            print(f"   Records count: {file_data['file']['records_count']}")
            print(f"   Uploaded at: {file_data['file']['uploaded_at']}")
        
        # Test getting file upload status
        print(f"\n📊 Getting file upload status for ID {upload_id}...")
        response = requests.get(f"http://localhost:5000/api/files/uploads/{upload_id}/status", headers=headers)
        
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Status: {status_data['status']}")
            print(f"   Records count: {status_data['records_count']}")
            if status_data.get('error_message'):
                print(f"   Error: {status_data['error_message']}")
    
    else:
        print(f"❌ Upload failed: {response.text}")
    
    # Test file uploads list again (should now have 1 file)
    print("\n📋 Getting updated file uploads list...")
    response = requests.get("http://localhost:5000/api/files/uploads", headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ File uploads list: {data['count']} files")
        for file in data['files']:
            print(f"   - {file['original_filename']} ({file['status']}) - {file['records_count']} records")
    
    # Clean up test file
    if os.path.exists("test_upload.csv"):
        os.remove("test_upload.csv")
        print("\n🧹 Cleaned up test file")

if __name__ == "__main__":
    print("🚀 Testing ReconX File Upload System")
    print("=" * 50)
    test_file_upload()
    print("\n✅ Test completed!")
