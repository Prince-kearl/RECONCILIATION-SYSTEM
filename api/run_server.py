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
        import socket
        
        # Get port from environment or use default (5001 to avoid AirPlay conflict)
        port = int(os.getenv('FLASK_PORT', 5001))
        
        # Try to find an available port if the default is in use
        def find_free_port(start_port):
            for port in range(start_port, start_port + 10):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('', port))
                        return port
                except OSError:
                    continue
            return None
        
        # Check if port is available, if not find a free one
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
        except OSError:
            print(f"⚠️  Port {port} is in use. Finding available port...")
            port = find_free_port(5001)
            if not port:
                print("❌ Could not find an available port")
                sys.exit(1)
            print(f"✅ Using port {port} instead")
        
        print("🚀 Starting ReconX Backend Server...")
        print(f"📡 API will be available at: http://localhost:{port}")
        print(f"🔍 Health check: http://localhost:{port}/api/health")
        print("📚 API documentation: See README.md for endpoint details")
        print("=" * 60)
        
        # Run the Flask app
        app.run(
            host='0.0.0.0',
            port=port,
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
