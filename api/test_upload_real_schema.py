import requests
import os
import json
import time

BASE_URL = "http://localhost:5000/api"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

def get_jwt_token(username, password):
    login_url = f"{BASE_URL}/auth/login"
    headers = {"Content-Type": "application/json"}
    data = {"username": username, "password": password}
    response = requests.post(login_url, headers=headers, json=data)
    response.raise_for_status()
    return response.json().get("token")

def test_file_status_summary(token):
    """Test the file status summary endpoint"""
    summary_url = f"{BASE_URL}/files/status/summary"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(summary_url, headers=headers)
    response.raise_for_status()
    return response.json()

def test_file_uploads_list(token):
    """Test the file uploads list endpoint"""
    uploads_url = f"{BASE_URL}/files/uploads"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(uploads_url, headers=headers)
    response.raise_for_status()
    return response.json()

def upload_test_file(token, file_path, file_type):
    """Upload a test file"""
    endpoint = "/files/upload/bank-statement" if file_type == "bank" else "/files/upload/internal-record"
    upload_url = f"{BASE_URL}{endpoint}"
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'text/csv')}
        response = requests.post(upload_url, headers=headers, files=files)
        response.raise_for_status()
        return response.json()

def main():
    print("🚀 Testing ReconX Upload with Real Database Schema")
    print("==================================================")

    # 1. Get JWT token
    print("🔐 Getting JWT token...")
    try:
        token = get_jwt_token(ADMIN_USERNAME, ADMIN_PASSWORD)
        print("✅ Login successful")
    except requests.exceptions.RequestException as e:
        print(f"❌ Login failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
        return

    # 2. Test initial file status summary
    print("\n📊 Testing file status summary...")
    try:
        summary = test_file_status_summary(token)
        print("✅ File status summary:")
        print(f"   Total files: {summary['summary']['total_files']}")
        print(f"   Processed: {summary['summary']['processed_files']}")
        print(f"   Bank status: {summary['bank_statement']['status']}")
        print(f"   Internal status: {summary['internal_record']['status']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get file status summary: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

    # 3. Test file uploads list
    print("\n📋 Testing file uploads list...")
    try:
        uploads_list = test_file_uploads_list(token)
        print(f"✅ Found {uploads_list['count']} uploaded files")
        for f in uploads_list['files']:
            print(f"   - {f['filename']} ({f['file_type']}) - {f['records_count']} records")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get file uploads: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

    # 4. Create and upload test bank statement
    print("\n📤 Testing bank statement upload...")
    test_bank_file = "test_bank_real.csv"
    try:
        with open(test_bank_file, 'w') as f:
            f.write("date,amount,description,account_number\n")
            f.write("2025-01-01,100.00,Deposit from client A,ACC001\n")
            f.write("2025-01-02,-50.00,Payment to vendor B,ACC001\n")
            f.write("2025-01-03,200.00,Interest earned,ACC001\n")

        upload_response = upload_test_file(token, test_bank_file, "bank")
        print("✅ Bank statement uploaded successfully!")
        print(f"   Upload ID: {upload_response.get('upload_id')}")
        print(f"   Records processed: {upload_response.get('records_count')}")
        print(f"   Status: {upload_response.get('status')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Bank statement upload failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
    except Exception as e:
        print(f"❌ Error creating test file: {e}")

    # 5. Create and upload test internal record
    print("\n📤 Testing internal record upload...")
    test_internal_file = "test_internal_real.csv"
    try:
        with open(test_internal_file, 'w') as f:
            f.write("date,amount,reference,description\n")
            f.write("2025-01-01,100.00,REF001,Collection from client A\n")
            f.write("2025-01-02,50.00,REF002,Collection from client B\n")
            f.write("2025-01-03,200.00,REF003,Collection from client C\n")

        upload_response = upload_test_file(token, test_internal_file, "internal")
        print("✅ Internal record uploaded successfully!")
        print(f"   Upload ID: {upload_response.get('upload_id')}")
        print(f"   Records processed: {upload_response.get('records_count')}")
        print(f"   Status: {upload_response.get('status')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Internal record upload failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)
    except Exception as e:
        print(f"❌ Error creating test file: {e}")

    # 6. Test updated file status summary
    print("\n📊 Testing updated file status summary...")
    try:
        summary = test_file_status_summary(token)
        print("✅ Updated file status summary:")
        print(f"   Total files: {summary['summary']['total_files']}")
        print(f"   Processed: {summary['summary']['processed_files']}")
        print(f"   Bank status: {summary['bank_statement']['status']}")
        print(f"   Bank filename: {summary['bank_statement']['filename']}")
        print(f"   Bank records: {summary['bank_statement']['records_count']}")
        print(f"   Internal status: {summary['internal_record']['status']}")
        print(f"   Internal filename: {summary['internal_record']['filename']}")
        print(f"   Internal records: {summary['internal_record']['records_count']}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get updated file status summary: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

    # 7. Test updated file uploads list
    print("\n📋 Testing updated file uploads list...")
    try:
        uploads_list = test_file_uploads_list(token)
        print(f"✅ Found {uploads_list['count']} uploaded files")
        for f in uploads_list['files']:
            print(f"   - {f['filename']} ({f['file_type']}) - {f['records_count']} records")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get updated file uploads: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(e.response.text)

    # 8. Clean up test files
    for test_file in [test_bank_file, test_internal_file]:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n🧹 Cleaned up {test_file}")

    print("\n✅ Test completed!")

if __name__ == "__main__":
    main()
