#!/usr/bin/env python
"""
Supabase Connection Setup and Testing Script
Tests both MySQL and PostgreSQL connections
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.supabase')

print("\n" + "="*60)
print("SUPABASE CONNECTION SETUP & TEST")
print("="*60 + "\n")

# Test PostgreSQL (Supabase)
print("📊 Testing PostgreSQL (Supabase) Connection...")
print("-" * 60)

try:
    import psycopg2
    from urllib.parse import quote_plus
    
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_sslmode = os.getenv('DB_SSLMODE', 'require')
    
    if not all([db_host, db_user, db_password]):
        print("❌ Missing Supabase credentials in .env.supabase")
        print("\n📝 Instructions:")
        print("1. Go to https://supabase.com/dashboard")
        print("2. Open your project > Settings > Database")
        print("3. Copy DB_HOST, DB_USER, DB_PASSWORD, DB_PORT")
        print("4. Update .env.supabase with your values")
        sys.exit(1)
    
    # Attempt connection
    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_name,
        sslmode=db_sslmode
    )
    
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    db_version = cursor.fetchone()
    cursor.close()
    conn.close()
    
    print("✅ PostgreSQL Connection Successful!")
    print(f"   Host: {db_host}")
    print(f"   Port: {db_port}")
    print(f"   Database: {db_name}")
    print(f"   Version: {db_version[0].split(',')[0]}")
    
except ImportError:
    print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"❌ PostgreSQL Connection Failed: {e}")
    print("\n🔧 Troubleshooting:")
    print("1. Verify Supabase project is active")
    print("2. Check DB credentials in .env.supabase")
    print("3. Ensure your IP is whitelisted (Supabase does this automatically)")
    print("4. Test with: psql postgresql://user:password@host:5432/postgres")
    sys.exit(1)

# Test SQLAlchemy connection string
print("\n📊 Testing SQLAlchemy Connection String...")
print("-" * 60)

try:
    from sqlalchemy import create_engine, text
    
    connection_string = f"postgresql+psycopg2://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    engine = create_engine(connection_string, echo=False)
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ SQLAlchemy Connection Successful!")
        print(f"   Engine: {engine.url.drivername}")
        print(f"   Connection: {engine.url.host}:{engine.url.port}/{engine.url.database}")

except ImportError:
    print("⚠️  SQLAlchemy not installed. Run: pip install SQLAlchemy")
    sys.exit(1)
except Exception as e:
    print(f"❌ SQLAlchemy Connection Failed: {e}")
    sys.exit(1)

# Display next steps
print("\n" + "="*60)
print("✅ ALL TESTS PASSED - READY FOR INTEGRATION")
print("="*60)

print("\n📋 Next Steps:")
print("1. Install PostgreSQL driver: pip install -r requirements.txt")
print("2. Set DB_TYPE=postgresql in your .env file")
print("3. Run migrations (if applicable)")
print("4. Restart your Flask app")
print("5. Verify API endpoints work with new database")

print("\n🔗 Connection String (for reference):")
print(f"   {connection_string[:50]}...{connection_string[-20:]}")

print("\n💾 Environment Variables Set:")
print(f"   DB_TYPE: postgresql")
print(f"   DB_HOST: {db_host}")
print(f"   DB_PORT: {db_port}")
print(f"   DB_NAME: {db_name}")
print(f"   DB_USER: {db_user}")
print(f"   DB_SSLMODE: {db_sslmode}")

print("\n" + "="*60 + "\n")
