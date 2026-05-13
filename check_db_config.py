import os
from dotenv import load_dotenv
from database_supabase import DatabaseConfig

load_dotenv('.env.supabase')
config = DatabaseConfig()

print(f"db_type: {config.db_type}")
print(f"host: {config.host}")
print(f"port: {config.port}")
print(f"user: {config.user}")
print(f"database: {config.database}")
print(f"sslmode: {getattr(config, 'sslmode', 'N/A')}")
