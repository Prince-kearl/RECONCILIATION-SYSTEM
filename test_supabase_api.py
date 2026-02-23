"""Test script for Supabase HTTP (PostgREST) access using the service role key.

Usage:
  source venv/bin/activate
  pip install requests python-dotenv   (already in requirements.txt)
  # Create a simple table in Supabase SQL editor:
  # CREATE TABLE public.health_check (id serial PRIMARY KEY, message text);
  # INSERT INTO public.health_check (message) VALUES ('ok');
  python test_supabase_api.py
"""

from supabase_client import select_from_table
import json


def main():
    print('\n' + '='*70)
    print('Testing Supabase HTTP API Connection')
    print('='*70)
    
    print('\n📊 Querying table `health_check`...')
    try:
        result = select_from_table('health_check')
        print(f'Status code: {result["status"]}')
        if result['status'] == 200:
            print('✅ HTTP API Connection Successful!')
            print(f'Data: {json.dumps(result["data"], indent=2)}')
        else:
            print(f'❌ Error ({result["status"]}): {result["error"]}')
    except Exception as e:
        print(f'❌ Exception: {e}')
    
    print('\n' + '='*70 + '\n')


if __name__ == '__main__':
    main()
