#!/usr/bin/env python3
"""
Test Supabase connection directly
"""
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

load_dotenv('.env.supabase')

db_user = os.getenv('DB_USER', 'postgres')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT', '5432')
db_name = os.getenv('DB_NAME', 'postgres')
db_sslmode = os.getenv('DB_SSLMODE', 'require')

print("\n" + "="*70)
print("SUPABASE CONNECTION TEST")
print("="*70)

try:
    connection_string = f"postgresql+psycopg2://{db_user}:{quote_plus(db_password)}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    print(f"\n📌 Connecting to: {db_host}:{db_port}/{db_name}")
    
    engine = create_engine(connection_string, echo=False)
    print("✅ Engine created")
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        print("✅ Query executed successfully")
        print("\n✅ YOUR SUPABASE DATABASE IS CONNECTED AND READY!")
        print(f"   Host: {db_host}")
        print(f"   Port: {db_port}")
        print(f"   Database: {db_name}")
        
except Exception as e:
    print(f"❌ Connection Failed: {str(e)[:100]}")

print("\n" + "="*70 + "\n")
