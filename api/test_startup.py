#!/usr/bin/env python3
"""
Quick test to verify server can start without errors
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("Testing imports...")
    from app import app
    print("✅ App imported successfully")
    
    print("Testing configuration...")
    print(f"  UPLOAD_FOLDER: {app.config.get('UPLOAD_FOLDER')}")
    print(f"  OUTPUT_FOLDER: {app.config.get('OUTPUT_FOLDER')}")
    
    print("Testing directory creation...")
    upload_dir = app.config.get('UPLOAD_FOLDER')
    output_dir = app.config.get('OUTPUT_FOLDER')
    
    os.makedirs(upload_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)
    print(f"✅ Directories created: {upload_dir}, {output_dir}")
    
    print("\n✅ All startup checks passed!")
    print("You can now start the server with: python3 run_server.py")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
