#!/usr/bin/env python3
"""
ReconX Server Startup Script
This script handles the proper startup of the ReconX backend server
"""

import os
import sys

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add the parent directory to Python path for reconciliation engine
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

if __name__ == '__main__':
    try:
        from app import app
        print("🚀 Starting ReconX Backend Server...")
        print("📡 API will be available at: http://localhost:5000")
        print("🔍 Health check: http://localhost:5000/api/health")
        print("📚 API documentation: See README.md for endpoint details")
        print("=" * 60)
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're in the correct directory and all dependencies are installed")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Server Error: {e}")
        print("💡 Check your configuration and database connection")
        sys.exit(1)
