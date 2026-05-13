import os
import psycopg2
from dotenv import load_dotenv

load_dotenv('.env.supabase')

host = os.getenv('DB_HOST')
port = os.getenv('DB_PORT')
user = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')
dbname = os.getenv('DB_NAME')
sslmode = os.getenv('DB_SSLMODE', 'require')

if password and password.startswith('"') and password.endswith('"'):
    password = password[1:-1]

print(f"Connecting to {host} as {user}...")

# Try connecting without specifying the user in the connection string explicitly if postgres is being used elsewhere
# Actually, psycopg2 should use the user passed.
try:
    conn = psycopg2.connect(
        dsn=f"user='{user}' password='{password}' host='{host}' port='{port}' dbname='{dbname}' sslmode='{sslmode}'"
    )
    cur = conn.cursor()
    cur.execute("SELECT 1")
    print(f"Result: {cur.fetchone()}")
    cur.close()
    conn.close()
    print("Connection successful")
except Exception as e:
    print(f"Connection failed: {e}")
