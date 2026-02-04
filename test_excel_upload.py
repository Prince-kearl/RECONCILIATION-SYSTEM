#!/usr/bin/env python3
"""
Test script to verify Excel file upload with TRN_DT, DR, CR columns
"""

import requests
import pandas as pd
import io
import os

# Create a test Excel file with the same structure as the user's file
def create_test_excel():
    # Sample data matching the user's Excel structure
    data = {
        'AC_NO': ['1000000', '1000001', '1000002'],
        'AC_BRANCH': ['001', '004', '001'],
        'TRN_REF_NO': ['TRN00000', 'TRN00001', 'TRN00002'],
        'TRN_DT': ['2025-08-11', '2025-08-15', '2025-07-30'],
        'DRCR_IND': ['CR', 'CR', 'DR'],
        'AC_CCY': ['GHS', 'GHS', 'GHS'],
        'DR': [None, None, 3341.29],
        'CR': [2401.88, 4627.58, None],
        'TRN_CODE': ['PMT', 'PMT', 'DEP'],
        'DESCRPTN': ['Transaction for PMT', 'Transaction for PMT', 'Transaction for DEP'],
        'USER_ID': ['USR01', 'USR04', 'USR03'],
        'TELLER_ID': ['TEL03', 'TEL01', 'TEL03'],
        'TELLER_HOME_BRANCH': ['004', '004', '004'],
        'AUTH_ID': ['AUTH03', 'AUTH02', 'AUTH02'],
        'AUTH_ID_2': ['AUTH01', 'AUTH03', 'AUTH01'],
        'AUTH_HOME_BRANCH': ['002', '001', '001']
    }
    
    df = pd.DataFrame(data)
    filename = 'test_imbalanced_export.xlsx'
    df.to_excel(filename, index=False)
    return filename

def test_upload():
    # Create test file
    test_file = create_test_excel()
    
    # Test upload
    url = 'http://localhost:5000/api/files/upload/bank-statement'
    headers = {'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiZXhwIjoxNzU4ODc1NzkzfQ.whfkgpS-j3f2XcVtKt3m3EIVNMdpxA8tQVhG5G1l3Kw'}
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(url, headers=headers, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Upload successful! The fix works.")
        else:
            print("❌ Upload failed. Check the error message.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_upload()
