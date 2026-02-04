#!/usr/bin/env python3
"""
Test MySQL connection with different password options
"""

import pymysql
import sys

def test_connection(host, user, password, database=None):
    """Test MySQL connection with given credentials"""
    try:
        if database:
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4'
            )
        else:
            connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                charset='utf8mb4'
            )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ SUCCESS: Connected to MySQL {version[0]}")
            return True
            
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    """Test common MySQL password combinations"""
    print("🔍 Testing MySQL Connection Options...")
    print("=" * 50)
    
    # Common password options
    passwords_to_try = [
        "",           # No password
        "root",       # root as password
        "password",   # common password
        "admin",      # admin as password
        "123456",     # simple password
        "mysql",      # mysql as password
    ]
    
    host = "localhost"
    user = "root"
    
    print(f"Testing connection to {host} with user '{user}'")
    print()
    
    for password in passwords_to_try:
        print(f"Testing password: '{password if password else '(empty)'}'")
        if test_connection(host, user, password):
            print(f"🎯 CORRECT PASSWORD FOUND: '{password if password else '(empty)'}'")
            print()
            print("Now you can:")
            print("1. Update your .env file with this password")
            print("2. Run: python setup_database.py")
            return password
        print()
    
    print("❌ No working password found.")
    print("Please check your MySQL installation and try:")
    print("1. MySQL Workbench or phpMyAdmin")
    print("2. Check if MySQL service is running")
    print("3. Reset MySQL root password if needed")
    return None

if __name__ == "__main__":
    main()
