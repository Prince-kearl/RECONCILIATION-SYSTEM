#!/usr/bin/env python3
"""
Database setup script for ReconX
This script helps you set up the MySQL database with the proper schema
"""

import pymysql
import os
import sys
from dotenv import load_dotenv

def load_config():
    """Load configuration from environment variables"""
    load_dotenv()
    
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'reconx')
    }
    
    return config

def create_database(config):
    """Create the database if it doesn't exist"""
    try:
        # Connect without specifying database
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {config['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{config['database']}' is ready")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        return False

def run_schema_script(config):
    """Run the database schema script"""
    try:
        # Connect to the specific database
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
        
        # Read and execute the schema script
        schema_file = 'database_schema.sql'
        if not os.path.exists(schema_file):
            print(f"❌ Schema file '{schema_file}' not found")
            return False
        
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        # Split into individual statements
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        
        with connection.cursor() as cursor:
            for statement in statements:
                if statement:
                    try:
                        cursor.execute(statement)
                        print(f"✅ Executed: {statement[:50]}...")
                    except Exception as e:
                        print(f"⚠️  Warning executing statement: {e}")
                        print(f"   Statement: {statement[:100]}...")
        
        connection.commit()
        connection.close()
        print("✅ Database schema created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to run schema script: {e}")
        return False

def test_connection(config):
    """Test the database connection"""
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database'],
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"✅ Database connection successful - Found {user_count} users")
        
        connection.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 ReconX Database Setup")
    print("=" * 50)
    
    # Load configuration
    config = load_config()
    print(f"📋 Configuration loaded:")
    print(f"   Host: {config['host']}:{config['port']}")
    print(f"   User: {config['user']}")
    print(f"   Database: {config['database']}")
    print()
    
    # Check if MySQL is accessible
    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4'
        )
        connection.close()
        print("✅ MySQL connection successful")
    except Exception as e:
        print(f"❌ Cannot connect to MySQL: {e}")
        print("   Please ensure MySQL is running and credentials are correct")
        return False
    
    # Create database
    if not create_database(config):
        return False
    
    # Run schema script
    if not run_schema_script(config):
        return False
    
    # Test final connection
    if not test_connection(config):
        return False
    
    print()
    print("🎉 Database setup completed successfully!")
    print()
    print("📝 Next steps:")
    print("   1. Start the Flask backend: python app.py")
    print("   2. Test the API endpoints")
    print("   3. Default admin credentials: admin / admin123")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
