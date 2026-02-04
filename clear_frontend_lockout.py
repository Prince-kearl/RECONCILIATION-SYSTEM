#!/usr/bin/env python3
"""
Clear frontend lockout and ensure backend is unlocked
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from database import DatabaseManager
from datetime import datetime

def clear_backend_lockout():
    """Clear any backend lockout mechanisms"""
    
    print("🔧 Clearing Backend Lockout")
    print("=" * 40)
    
    db = DatabaseManager()
    
    try:
        # Check current admin account status
        print("🔍 Checking admin account...")
        admin_query = """
            SELECT u.*, r.role_name 
            FROM users u 
            LEFT JOIN roles r ON u.role_id = r.role_id 
            WHERE u.username = 'admin'
        """
        admin_result = db.execute_query(admin_query)
        
        if not admin_result:
            print("❌ Admin account not found!")
            return False
        
        admin = admin_result[0]
        print(f"📊 Current admin status:")
        for key, value in admin.items():
            print(f"   {key}: {value}")
        
        # Clear all lockout fields
        print("\n🔧 Clearing all lockout fields...")
        
        # Check what columns exist and update accordingly
        update_fields = []
        update_values = []
        
        # Reset failed login attempts
        if 'failed_login_attempts' in admin:
            update_fields.append("failed_login_attempts = %s")
            update_values.append(0)
        
        # Set status to active
        if 'status' in admin:
            update_fields.append("status = %s")
            update_values.append('active')
        
        # Clear lockout time
        if 'account_locked_until' in admin:
            update_fields.append("account_locked_until = NULL")
        
        if update_fields:
            update_query = f"UPDATE users SET {', '.join(update_fields)} WHERE username = 'admin'"
            print(f"Executing: {update_query}")
            print(f"Values: {update_values}")
            
            affected_rows = db.execute_update(update_query, tuple(update_values))
            print(f"✅ Updated {affected_rows} admin account(s)")
        else:
            print("⚠️  No lockout fields to update")
        
        # Verify the update
        print("\n🔍 Verifying update...")
        verify_result = db.execute_query(admin_query)
        if verify_result:
            admin = verify_result[0]
            print(f"📊 Updated admin data:")
            for key, value in admin.items():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_frontend_unlock_script():
    """Create a script to clear frontend localStorage lockout"""
    
    print("\n🔧 Creating Frontend Unlock Script")
    print("=" * 40)
    
    unlock_script = """
<!DOCTYPE html>
<html>
<head>
    <title>ReconX - Clear Login Lockout</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 500px; margin: 0 auto; }
        .success { color: #28a745; font-weight: bold; }
        .info { color: #17a2b8; }
        .warning { color: #ffc107; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 10px 5px; }
        button:hover { background: #0056b3; }
        .status { margin: 20px 0; padding: 15px; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>🔓 ReconX Login Lockout Clearer</h2>
        
        <div id="status" class="status" style="display: none;"></div>
        
        <p class="info">This tool will clear the frontend login lockout stored in your browser's localStorage.</p>
        
        <button onclick="clearLockout()">Clear Login Lockout</button>
        <button onclick="checkStatus()">Check Current Status</button>
        <button onclick="window.location.href='login.html'">Go to Login</button>
        
        <div id="details" style="margin-top: 20px; display: none;">
            <h3>Current Status:</h3>
            <div id="statusDetails"></div>
        </div>
    </div>

    <script>
        function showStatus(message, type = 'info') {
            const statusEl = document.getElementById('status');
            statusEl.textContent = message;
            statusEl.className = 'status ' + type;
            statusEl.style.display = 'block';
        }
        
        function getFails() {
            try {
                return Number(localStorage.getItem('loginFails') || '0');
            } catch {
                return 0;
            }
        }
        
        function getLastFail() {
            try {
                return Number(localStorage.getItem('loginLastFail') || '0');
            } catch {
                return 0;
            }
        }
        
        function isLocked() {
            try {
                const fails = getFails();
                const last = getLastFail();
                if (fails >= 5) {
                    const elapsed = Date.now() - last;
                    return elapsed < 5 * 60 * 1000; // 5 minutes
                }
                return false;
            } catch {
                return false;
            }
        }
        
        function clearLockout() {
            try {
                // Clear the lockout data
                localStorage.removeItem('loginFails');
                localStorage.removeItem('loginLastFail');
                
                showStatus('✅ Login lockout cleared successfully! You can now try logging in again.', 'success');
                
                // Show updated status
                setTimeout(checkStatus, 1000);
                
            } catch (error) {
                showStatus('❌ Error clearing lockout: ' + error.message, 'warning');
            }
        }
        
        function checkStatus() {
            try {
                const fails = getFails();
                const lastFail = getLastFail();
                const locked = isLocked();
                const lastFailDate = lastFail ? new Date(lastFail).toLocaleString() : 'Never';
                
                const detailsEl = document.getElementById('details');
                const statusDetailsEl = document.getElementById('statusDetails');
                
                statusDetailsEl.innerHTML = `
                    <p><strong>Failed Attempts:</strong> ${fails}</p>
                    <p><strong>Last Failed Attempt:</strong> ${lastFailDate}</p>
                    <p><strong>Currently Locked:</strong> ${locked ? '🔒 YES' : '🔓 NO'}</p>
                `;
                
                detailsEl.style.display = 'block';
                
                if (locked) {
                    showStatus('🔒 Account is currently locked. Click "Clear Login Lockout" to unlock.', 'warning');
                } else {
                    showStatus('🔓 Account is not locked. You can try logging in.', 'success');
                }
                
            } catch (error) {
                showStatus('❌ Error checking status: ' + error.message, 'warning');
            }
        }
        
        // Check status on page load
        window.onload = function() {
            checkStatus();
        };
    </script>
</body>
</html>
"""
    
    # Write the unlock script to the parent directory (where login.html is)
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'clear_lockout.html')
    
    try:
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(unlock_script)
        print(f"✅ Frontend unlock script created: {script_path}")
        return script_path
    except Exception as e:
        print(f"❌ Error creating unlock script: {e}")
        return None

def test_login():
    """Test login after clearing lockout"""
    print("\n🧪 Testing Login After Clear")
    print("=" * 40)
    
    try:
        import requests
        
        # Test login
        login_url = "http://localhost:5000/api/auth/login"
        login_data = {"username": "admin", "password": "admin123"}
        
        response = requests.post(login_url, json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend login successful!")
            print(f"✅ Token: {data['token'][:50]}...")
            print(f"✅ User: {data.get('user', {})}")
            return True
        else:
            print(f"❌ Backend login failed: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running.")
        return False
    except Exception as e:
        print(f"❌ Login test failed: {e}")
        return False

def main():
    """Main function"""
    print("🚀 ReconX Complete Lockout Clearer")
    print("=" * 60)
    
    # Step 1: Clear backend lockout
    if clear_backend_lockout():
        print("\n✅ Backend lockout cleared!")
    else:
        print("\n❌ Failed to clear backend lockout")
        return
    
    # Step 2: Create frontend unlock script
    script_path = create_frontend_unlock_script()
    
    # Step 3: Test backend login
    print("\n" + "=" * 60)
    if test_login():
        print("✅ Backend login working!")
    else:
        print("⚠️  Backend login test failed")
    
    # Step 4: Instructions
    print("\n" + "=" * 60)
    print("🎯 NEXT STEPS TO COMPLETE THE FIX:")
    print("=" * 60)
    print("1. 🔓 CLEAR FRONTEND LOCKOUT:")
    if script_path:
        print(f"   → Open: {script_path}")
        print("   → Click 'Clear Login Lockout' button")
        print("   → Then go to login.html")
    else:
        print("   → Open your browser's Developer Tools (F12)")
        print("   → Go to Application/Storage → Local Storage")
        print("   → Delete 'loginFails' and 'loginLastFail' entries")
    
    print("\n2. 🔄 REFRESH THE LOGIN PAGE:")
    print("   → Clear browser cache (Ctrl+F5)")
    print("   → Or open login.html in an incognito/private window")
    
    print("\n3. 🧪 TEST LOGIN:")
    print("   → Username: admin")
    print("   → Password: admin123")
    
    print("\n4. 🎉 SUCCESS:")
    print("   → You should now be able to login without lockout errors!")

if __name__ == "__main__":
    main()
