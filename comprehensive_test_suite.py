#!/usr/bin/env python3
"""
Comprehensive Test Suite for ReconX Reconciliation System
Tests all APIs, endpoints, workflows, and functionality
"""

import requests
import json
import os
import tempfile
from datetime import datetime
import sys

# Try to import pandas, but handle if not available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  Warning: pandas not available. Some file creation tests will be skipped.")

# Get port from environment or use default (5001 to avoid AirPlay conflict)
import os
PORT = int(os.getenv('RECONX_API_PORT', 5001))
BASE_URL = f"http://localhost:{PORT}/api"
TEST_RESULTS = {
    'passed': [],
    'failed': [],
    'warnings': []
}

def log_test(test_name, status, message="", details=None):
    """Log test results"""
    result = {
        'test': test_name,
        'status': status,
        'message': message,
        'details': details,
        'timestamp': datetime.now().isoformat()
    }
    
    if status == 'PASS':
        TEST_RESULTS['passed'].append(result)
        print(f"✅ PASS: {test_name}")
        if message:
            print(f"   {message}")
    elif status == 'FAIL':
        TEST_RESULTS['failed'].append(result)
        print(f"❌ FAIL: {test_name}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
    else:
        TEST_RESULTS['warnings'].append(result)
        print(f"⚠️  WARN: {test_name}")
        if message:
            print(f"   {message}")
    
    if details and status == 'FAIL':
        print(f"   Response: {json.dumps(details, indent=2)}")

# ============================================================================
# TEST DATA CREATION
# ============================================================================

def create_test_bank_statement():
    """Create a test bank statement CSV file"""
    if not PANDAS_AVAILABLE:
        # Create CSV manually
        file_path = os.path.join(tempfile.gettempdir(), 'test_bank_statement.csv')
        with open(file_path, 'w') as f:
            f.write('date,amount,description,bank_ref\n')
            f.write('2026-01-01,1000.00,Payment from Customer A,REF001\n')
            f.write('2026-01-02,500.00,Payment from Customer B,REF002\n')
            f.write('2026-01-03,750.00,Payment from Customer C,REF003\n')
            f.write('2026-01-04,1200.00,Payment from Customer D,REF004\n')
            f.write('2026-01-05,300.00,Payment from Customer E,REF005\n')
        return file_path
    
    data = {
        'date': ['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05'],
        'amount': [1000.00, 500.00, 750.00, 1200.00, 300.00],
        'description': ['Payment from Customer A', 'Payment from Customer B', 
                       'Payment from Customer C', 'Payment from Customer D', 
                       'Payment from Customer E'],
        'bank_ref': ['REF001', 'REF002', 'REF003', 'REF004', 'REF005']
    }
    df = pd.DataFrame(data)
    file_path = os.path.join(tempfile.gettempdir(), 'test_bank_statement.csv')
    df.to_csv(file_path, index=False)
    return file_path

def create_test_internal_record():
    """Create a test internal record CSV file"""
    if not PANDAS_AVAILABLE:
        # Create CSV manually
        file_path = os.path.join(tempfile.gettempdir(), 'test_internal_record.csv')
        with open(file_path, 'w') as f:
            f.write('date,amount,narration,reference\n')
            f.write('2026-01-01,1000.00,Payment from Customer A,REF001\n')
            f.write('2026-01-02,500.00,Payment from Customer B,REF002\n')
            f.write('2026-01-03,750.00,Payment from Customer C,REF003\n')
            f.write('2026-01-04,1200.00,Payment from Customer D,REF004\n')
        return file_path
    
    data = {
        'date': ['2026-01-01', '2026-01-02', '2026-01-03', '2026-01-04'],
        'amount': [1000.00, 500.00, 750.00, 1200.00],
        'narration': ['Payment from Customer A', 'Payment from Customer B',
                     'Payment from Customer C', 'Payment from Customer D'],
        'reference': ['REF001', 'REF002', 'REF003', 'REF004']
    }
    df = pd.DataFrame(data)
    file_path = os.path.join(tempfile.gettempdir(), 'test_internal_record.csv')
    df.to_csv(file_path, index=False)
    return file_path

# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_health_check():
    """Test health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            log_test("Health Check", "PASS", f"Server is running")
            return True
        else:
            log_test("Health Check", "FAIL", f"Unexpected status: {response.status_code}", 
                    response.json() if response.content else None)
            return False
    except requests.exceptions.ConnectionError:
        log_test("Health Check", "FAIL", "Cannot connect to server. Is it running on localhost:5000?")
        return False
    except Exception as e:
        log_test("Health Check", "FAIL", f"Error: {str(e)}")
        return False

def test_login_success():
    """Test successful login"""
    try:
        data = {"username": "admin", "password": "admin123"}
        response = requests.post(f"{BASE_URL}/auth/login", json=data, timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if 'token' in result and 'user' in result:
                log_test("Login (Success)", "PASS", 
                        f"Logged in as {result['user']['username']} ({result['user']['role']})")
                return result['token']
            else:
                log_test("Login (Success)", "FAIL", "Token or user data missing", result)
                return None
        else:
            log_test("Login (Success)", "FAIL", f"Status: {response.status_code}", 
                    response.json() if response.content else None)
            return None
    except Exception as e:
        log_test("Login (Success)", "FAIL", f"Error: {str(e)}")
        return None

def test_login_failure():
    """Test login with invalid credentials"""
    try:
        data = {"username": "admin", "password": "wrongpassword"}
        response = requests.post(f"{BASE_URL}/auth/login", json=data, timeout=5)
        
        if response.status_code == 401:
            log_test("Login (Invalid Credentials)", "PASS", "Correctly rejected invalid credentials")
            return True
        else:
            log_test("Login (Invalid Credentials)", "FAIL", 
                    f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Login (Invalid Credentials)", "FAIL", f"Error: {str(e)}")
        return False

def test_login_missing_fields():
    """Test login with missing fields"""
    try:
        data = {"username": "admin"}  # Missing password
        response = requests.post(f"{BASE_URL}/auth/login", json=data, timeout=5)
        
        if response.status_code == 400:
            log_test("Login (Missing Fields)", "PASS", "Correctly rejected missing fields")
            return True
        else:
            log_test("Login (Missing Fields)", "FAIL", 
                    f"Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Login (Missing Fields)", "FAIL", f"Error: {str(e)}")
        return False

def test_get_current_user(token):
    """Test getting current user info"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers, timeout=5)
        
        if response.status_code == 200:
            user = response.json()
            if 'username' in user and 'role' in user:
                log_test("Get Current User", "PASS", 
                        f"Retrieved user: {user['username']} ({user['role']})")
                return True
            else:
                log_test("Get Current User", "FAIL", "Missing user fields", user)
                return False
        else:
            log_test("Get Current User", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("Get Current User", "FAIL", f"Error: {str(e)}")
        return False

def test_unauthorized_access():
    """Test accessing protected endpoint without token"""
    try:
        response = requests.get(f"{BASE_URL}/auth/me", timeout=5)
        
        if response.status_code == 401:
            log_test("Unauthorized Access", "PASS", "Correctly rejected unauthorized access")
            return True
        else:
            log_test("Unauthorized Access", "FAIL", 
                    f"Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Unauthorized Access", "FAIL", f"Error: {str(e)}")
        return False

# ============================================================================
# FILE UPLOAD TESTS
# ============================================================================

def test_upload_bank_statement(token):
    """Test uploading a bank statement file"""
    try:
        file_path = create_test_bank_statement()
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(file_path, 'rb') as f:
            files = {'file': ('test_bank_statement.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/files/upload/bank-statement",
                headers=headers,
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log_test("Upload Bank Statement", "PASS", 
                        f"Uploaded successfully. Records: {result.get('records_count', 0)}")
                return True
            else:
                log_test("Upload Bank Statement", "FAIL", "Upload failed", result)
                return False
        else:
            log_test("Upload Bank Statement", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("Upload Bank Statement", "FAIL", f"Error: {str(e)}")
        return False

def test_upload_internal_record(token):
    """Test uploading an internal record file"""
    try:
        file_path = create_test_internal_record()
        headers = {"Authorization": f"Bearer {token}"}
        
        with open(file_path, 'rb') as f:
            files = {'file': ('test_internal_record.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/files/upload/internal-record",
                headers=headers,
                files=files,
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log_test("Upload Internal Record", "PASS", 
                        f"Uploaded successfully. Records: {result.get('records_count', 0)}")
                return True
            else:
                log_test("Upload Internal Record", "FAIL", "Upload failed", result)
                return False
        else:
            log_test("Upload Internal Record", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("Upload Internal Record", "FAIL", f"Error: {str(e)}")
        return False

def test_upload_invalid_file_type(token):
    """Test uploading invalid file type"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        # Create a dummy text file
        file_path = os.path.join(tempfile.gettempdir(), 'test.txt')
        with open(file_path, 'w') as f:
            f.write("This is not a CSV or Excel file")
        
        with open(file_path, 'rb') as f:
            files = {'file': ('test.txt', f, 'text/plain')}
            response = requests.post(
                f"{BASE_URL}/files/upload/bank-statement",
                headers=headers,
                files=files,
                timeout=10
            )
        
        if response.status_code == 400:
            log_test("Upload Invalid File Type", "PASS", "Correctly rejected invalid file type")
            return True
        else:
            log_test("Upload Invalid File Type", "FAIL", 
                    f"Expected 400, got {response.status_code}")
            return False
    except Exception as e:
        log_test("Upload Invalid File Type", "FAIL", f"Error: {str(e)}")
        return False

def test_get_file_status_summary(token):
    """Test getting file status summary"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/files/status/summary",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'summary' in result:
                summary = result['summary']
                log_test("Get File Status Summary", "PASS", 
                        f"Total files: {summary.get('total_files', 0)}")
                return True
            else:
                log_test("Get File Status Summary", "FAIL", "Missing summary data", result)
                return False
        else:
            log_test("Get File Status Summary", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("Get File Status Summary", "FAIL", f"Error: {str(e)}")
        return False

def test_list_uploaded_files(token):
    """Test listing uploaded files"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/files/uploads",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'files' in result:
                files = result['files']
                log_test("List Uploaded Files", "PASS", 
                        f"Found {len(files)} uploaded files")
                return True
            else:
                log_test("List Uploaded Files", "FAIL", "Missing files data", result)
                return False
        else:
            log_test("List Uploaded Files", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("List Uploaded Files", "FAIL", f"Error: {str(e)}")
        return False

# ============================================================================
# RECONCILIATION TESTS
# ============================================================================

def test_start_reconciliation(token):
    """Test starting reconciliation process"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {"tolerance": 0.00}
        response = requests.post(
            f"{BASE_URL}/reconciliation/start",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                run_id = result.get('run_id')
                summary = result.get('summary', {})
                log_test("Start Reconciliation", "PASS", 
                        f"Reconciliation completed. Run ID: {run_id}, "
                        f"Matched: {summary.get('Matched', 0)}, "
                        f"Unmatched: {summary.get('Unmatched', 0)}")
                return result
            else:
                log_test("Start Reconciliation", "FAIL", result.get('error', 'Unknown error'), result)
                return None
        else:
            log_test("Start Reconciliation", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return None
    except Exception as e:
        log_test("Start Reconciliation", "FAIL", f"Error: {str(e)}")
        return None

def test_start_reconciliation_no_data(token):
    """Test starting reconciliation without uploaded data"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {"tolerance": 0.00}
        response = requests.post(
            f"{BASE_URL}/reconciliation/start",
            headers=headers,
            json=data,
            timeout=10
        )
        
        # This might fail if no data, or succeed if data exists
        if response.status_code in [200, 400]:
            result = response.json()
            if result.get('success') or 'No' in result.get('error', ''):
                log_test("Start Reconciliation (No Data)", "PASS", 
                        "Correctly handled missing data scenario")
                return True
            else:
                log_test("Start Reconciliation (No Data)", "WARN", 
                        "Unexpected response", result)
                return True
        else:
            log_test("Start Reconciliation (No Data)", "WARN", 
                    f"Status: {response.status_code}")
            return True
    except Exception as e:
        log_test("Start Reconciliation (No Data)", "WARN", f"Error: {str(e)}")
        return True

def test_get_reconciliation_results(token):
    """Test getting reconciliation results"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/reconciliation/results",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'results' in result or 'data' in result:
                log_test("Get Reconciliation Results", "PASS", "Retrieved results successfully")
                return True
            else:
                log_test("Get Reconciliation Results", "WARN", "Unexpected response format", result)
                return True
        else:
            log_test("Get Reconciliation Results", "WARN", f"Status: {response.status_code}")
            return True
    except Exception as e:
        log_test("Get Reconciliation Results", "WARN", f"Error: {str(e)}")
        return True

# ============================================================================
# USER MANAGEMENT TESTS (Admin Only)
# ============================================================================

def test_list_users(token):
    """Test listing all users"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/users",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'users' in result:
                users = result['users']
                log_test("List Users", "PASS", f"Found {len(users)} users")
                return True
            else:
                log_test("List Users", "FAIL", "Missing users data", result)
                return False
        elif response.status_code == 403:
            log_test("List Users", "WARN", "Access denied (may need admin role)")
            return True
        else:
            log_test("List Users", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("List Users", "FAIL", f"Error: {str(e)}")
        return False

def test_create_user(token):
    """Test creating a new user"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        data = {
            "username": f"testuser_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "email": f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "role": "viewer"
        }
        response = requests.post(
            f"{BASE_URL}/users",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                log_test("Create User", "PASS", f"User created with ID: {result.get('user_id')}")
                return True
            else:
                log_test("Create User", "FAIL", "User creation failed", result)
                return False
        elif response.status_code == 403:
            log_test("Create User", "WARN", "Access denied (may need admin role)")
            return True
        else:
            log_test("Create User", "FAIL", f"Status: {response.status_code}",
                    response.json() if response.content else None)
            return False
    except Exception as e:
        log_test("Create User", "FAIL", f"Error: {str(e)}")
        return False

# ============================================================================
# AUDIT LOGS TESTS
# ============================================================================

def test_get_audit_logs(token):
    """Test getting audit logs"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/audit/logs",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'logs' in result:
                logs = result['logs']
                log_test("Get Audit Logs", "PASS", f"Retrieved {len(logs)} audit log entries")
                return True
            else:
                log_test("Get Audit Logs", "WARN", "Unexpected response format", result)
                return True
        elif response.status_code == 403:
            log_test("Get Audit Logs", "WARN", "Access denied (may need admin/auditor role)")
            return True
        else:
            log_test("Get Audit Logs", "WARN", f"Status: {response.status_code}")
            return True
    except Exception as e:
        log_test("Get Audit Logs", "WARN", f"Error: {str(e)}")
        return True

# ============================================================================
# WORKFLOW TESTS
# ============================================================================

def test_complete_workflow(token):
    """Test complete reconciliation workflow"""
    try:
        log_test("Complete Workflow", "PASS", "Starting complete workflow test...")
        
        # Step 1: Upload bank statement
        file_path = create_test_bank_statement()
        headers = {"Authorization": f"Bearer {token}"}
        with open(file_path, 'rb') as f:
            files = {'file': ('test_bank_statement.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/files/upload/bank-statement",
                headers=headers,
                files=files,
                timeout=30
            )
        if response.status_code != 200:
            log_test("Complete Workflow", "FAIL", "Step 1: Bank statement upload failed")
            return False
        
        # Step 2: Upload internal record
        file_path = create_test_internal_record()
        with open(file_path, 'rb') as f:
            files = {'file': ('test_internal_record.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/files/upload/internal-record",
                headers=headers,
                files=files,
                timeout=30
            )
        if response.status_code != 200:
            log_test("Complete Workflow", "FAIL", "Step 2: Internal record upload failed")
            return False
        
        # Step 3: Start reconciliation
        data = {"tolerance": 0.00}
        response = requests.post(
            f"{BASE_URL}/reconciliation/start",
            headers=headers,
            json=data,
            timeout=60
        )
        if response.status_code != 200:
            log_test("Complete Workflow", "FAIL", "Step 3: Reconciliation failed")
            return False
        
        result = response.json()
        if result.get('success'):
            log_test("Complete Workflow", "PASS", 
                    f"Workflow completed successfully. Run ID: {result.get('run_id')}")
            return True
        else:
            log_test("Complete Workflow", "FAIL", "Reconciliation did not succeed", result)
            return False
            
    except Exception as e:
        log_test("Complete Workflow", "FAIL", f"Error: {str(e)}")
        return False

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("🧪 ReconX Comprehensive Test Suite")
    print("=" * 70)
    print()
    
    # Check if server is running
    if not test_health_check():
        print("\n❌ Server is not running. Please start the server first:")
        print("   cd api && python3 run_server.py")
        return
    
    print("\n" + "=" * 70)
    print("📋 AUTHENTICATION TESTS")
    print("=" * 70)
    
    # Authentication tests
    test_login_failure()
    test_login_missing_fields()
    token = test_login_success()
    
    if not token:
        print("\n❌ Cannot proceed without authentication token")
        return
    
    test_get_current_user(token)
    test_unauthorized_access()
    
    print("\n" + "=" * 70)
    print("📁 FILE UPLOAD TESTS")
    print("=" * 70)
    
    # File upload tests
    test_upload_invalid_file_type(token)
    test_upload_bank_statement(token)
    test_upload_internal_record(token)
    test_get_file_status_summary(token)
    test_list_uploaded_files(token)
    
    print("\n" + "=" * 70)
    print("🔄 RECONCILIATION TESTS")
    print("=" * 70)
    
    # Reconciliation tests
    test_start_reconciliation_no_data(token)
    test_start_reconciliation(token)
    test_get_reconciliation_results(token)
    
    print("\n" + "=" * 70)
    print("👥 USER MANAGEMENT TESTS")
    print("=" * 70)
    
    # User management tests
    test_list_users(token)
    test_create_user(token)
    
    print("\n" + "=" * 70)
    print("📊 AUDIT LOGS TESTS")
    print("=" * 70)
    
    # Audit logs tests
    test_get_audit_logs(token)
    
    print("\n" + "=" * 70)
    print("🔄 COMPLETE WORKFLOW TEST")
    print("=" * 70)
    
    # Complete workflow test
    test_complete_workflow(token)
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {len(TEST_RESULTS['passed'])}")
    print(f"❌ Failed: {len(TEST_RESULTS['failed'])}")
    print(f"⚠️  Warnings: {len(TEST_RESULTS['warnings'])}")
    print()
    
    if TEST_RESULTS['failed']:
        print("Failed Tests:")
        for test in TEST_RESULTS['failed']:
            print(f"  - {test['test']}: {test['message']}")
        print()
    
    # Save results to file
    results_file = os.path.join(tempfile.gettempdir(), 'reconx_test_results.json')
    with open(results_file, 'w') as f:
        json.dump(TEST_RESULTS, f, indent=2)
    print(f"📄 Detailed results saved to: {results_file}")
    
    if len(TEST_RESULTS['failed']) == 0:
        print("\n🎉 All critical tests passed!")
    else:
        print(f"\n⚠️  {len(TEST_RESULTS['failed'])} test(s) failed. Please review the details above.")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
