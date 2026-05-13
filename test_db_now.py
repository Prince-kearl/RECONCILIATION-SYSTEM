import os
import psycopg2
from dotenv import dotenv_values

vals = dotenv_values('/Users/tavido/Desktop/GCB reconx/.env.supabase')
host = vals.get('DB_HOST')
port = int(vals.get('DB_PORT', '5432'))
user = vals.get('DB_USER')
password = vals.get('DB_PASSWORD', '')
dbname = vals.get('DB_NAME', 'postgres')
sslmode = vals.get('DB_SSLMODE', 'require')

print(f"Host:            {host}:{port}")
print(f"User:            {user}")
print(f"Database:        {dbname}")
print(f"Password length: {len(password)}")

from urllib.parse import quote_plus

# Use URI form — psycopg2 keyword-args strips dotted usernames (Supabase pooler quirk)
uri = f"postgresql://{quote_plus(user)}:{quote_plus(password)}@{host}:{port}/{dbname}?sslmode={sslmode}"
print(f"URI user part:   {quote_plus(user)}")

try:
    conn = psycopg2.connect(uri)
    cur = conn.cursor()
    cur.execute("SELECT version()")
    print(f"OK: {cur.fetchone()[0][:70]}")
    cur.close()
    conn.close()
    print("=== CONNECTION SUCCESSFUL ===")
except Exception as e:
    print(f"FAIL: {e}")
