#!/usr/bin/env python3
"""
Debug script for file status API
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from database import file_manager

def debug_file_status():
    """Debug the file status issue"""
    
    try:
        print("🔍 Testing file_manager methods...")
        
        # Test get_file_uploads with no parameters
        print("\n1. Testing get_file_uploads() with no parameters...")
        files = file_manager.get_file_uploads()
        print(f"   ✅ Got {len(files)} files")
        
        # Test get_file_uploads with file_type
        print("\n2. Testing get_file_uploads(file_type='bank_statement')...")
        bank_files = file_manager.get_file_uploads(file_type='bank_statement')
        print(f"   ✅ Got {len(bank_files)} bank statement files")
        
        # Test get_file_uploads with status
        print("\n3. Testing get_file_uploads(status='processed')...")
        processed_files = file_manager.get_file_uploads(status='processed')
        print(f"   ✅ Got {len(processed_files)} processed files")
        
        # Test get_user_file_uploads
        print("\n4. Testing get_user_file_uploads(user_id=1)...")
        user_files = file_manager.get_user_file_uploads(1)
        print(f"   ✅ Got {len(user_files)} user files")
        
        # Test the specific calls used in the API
        print("\n5. Testing API-specific calls...")
        bank_files = file_manager.get_file_uploads(file_type='bank_statement', limit=10)
        internal_files = file_manager.get_file_uploads(file_type='internal_record', limit=10)
        print(f"   ✅ Bank files: {len(bank_files)}")
        print(f"   ✅ Internal files: {len(internal_files)}")
        
        # Test list concatenation
        print("\n6. Testing list concatenation...")
        all_files = bank_files + internal_files
        print(f"   ✅ Combined files: {len(all_files)}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🐛 Debugging File Status API")
    print("=" * 50)
    debug_file_status()
