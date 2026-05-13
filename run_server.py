#!/usr/bin/env python3
"""
ReconX Server Startup Script
This script handles the proper startup of the ReconX backend server
"""

import os
import sys
import socket

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add the parent directory to Python path for reconciliation engine
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

if __name__ == '__main__':
    try:
        from app import app
        port = int(os.getenv('FLASK_PORT', 5001))

        def find_free_port(start_port):
            for p in range(start_port, start_port + 20):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('', p))
                        return p
                except OSError:
                    continue
            return None

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
        except OSError:
            print(f"⚠️  Port {port} is in use. Finding an available port...")
            next_port = find_free_port(5001)
            if not next_port:
                print("❌ Could not find a free port in range 5001-5020")
                sys.exit(1)
            port = next_port

        print("🚀 Starting ReconX Backend Server...")
        print(f"📡 API will be available at: http://localhost:{port}")
        print(f"🔍 Health check: http://localhost:{port}/api/health")
        print("📚 API documentation: See README.md for endpoint details")
        print("=" * 60)
        
        debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'

        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug_mode,
            use_reloader=False
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
