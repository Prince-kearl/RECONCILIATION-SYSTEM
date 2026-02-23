"""Lightweight Supabase HTTP client using requests library.

This avoids the heavyweight supabase SDK and uses direct HTTP calls
to Supabase's PostgREST API for database operations.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv('.env.supabase')


class SupabaseClient:
    """Simple HTTP-based Supabase client."""
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not (self.service_role_key or self.anon_key):
            raise RuntimeError('SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/ANON_KEY not set in .env.supabase')
        
        # Use service role key (more permissions) for backend; fall back to anon key
        self.api_key = self.service_role_key or self.anon_key
    
    def _headers(self):
        """Standard headers for Supabase API calls."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'apikey': self.api_key,
        }
    
    def select(self, table: str, columns: str = '*', **filters):
        """SELECT from a table.
        
        Args:
            table: table name
            columns: comma-separated column list (default: '*')
            **filters: optional WHERE filters (e.g., id=1)
        
        Returns:
            dict with 'status', 'data', 'error'
        """
        url = f'{self.url}/rest/v1/{table}'
        params = {'select': columns}
        
        # Add filters as query params (simplified; use eq=value for equality)
        for key, val in filters.items():
            params[key] = f'eq.{val}'
        
        try:
            resp = requests.get(url, headers=self._headers(), params=params, timeout=10)
            return {
                'status': resp.status_code,
                'data': resp.json() if resp.status_code == 200 else None,
                'error': resp.text if resp.status_code >= 400 else None,
            }
        except Exception as e:
            return {'status': 500, 'data': None, 'error': str(e)}
    
    def insert(self, table: str, data: dict):
        """INSERT into a table.
        
        Args:
            table: table name
            data: dict of column:value pairs
        
        Returns:
            dict with 'status', 'data', 'error'
        """
        url = f'{self.url}/rest/v1/{table}'
        try:
            resp = requests.post(url, headers=self._headers(), json=data, timeout=10)
            return {
                'status': resp.status_code,
                'data': resp.json() if resp.status_code in (200, 201) else None,
                'error': resp.text if resp.status_code >= 400 else None,
            }
        except Exception as e:
            return {'status': 500, 'data': None, 'error': str(e)}
    
    def update(self, table: str, data: dict, id_value):
        """UPDATE a table row by id.
        
        Args:
            table: table name
            data: dict of column:value pairs to update
            id_value: value of id column to match
        
        Returns:
            dict with 'status', 'data', 'error'
        """
        url = f'{self.url}/rest/v1/{table}?id=eq.{id_value}'
        try:
            resp = requests.patch(url, headers=self._headers(), json=data, timeout=10)
            return {
                'status': resp.status_code,
                'data': resp.json() if resp.status_code == 200 else None,
                'error': resp.text if resp.status_code >= 400 else None,
            }
        except Exception as e:
            return {'status': 500, 'data': None, 'error': str(e)}
    
    def delete(self, table: str, id_value):
        """DELETE a table row by id.
        
        Args:
            table: table name
            id_value: value of id column to match
        
        Returns:
            dict with 'status', 'data', 'error'
        """
        url = f'{self.url}/rest/v1/{table}?id=eq.{id_value}'
        try:
            resp = requests.delete(url, headers=self._headers(), timeout=10)
            return {
                'status': resp.status_code,
                'data': resp.json() if resp.status_code == 200 else None,
                'error': resp.text if resp.status_code >= 400 else None,
            }
        except Exception as e:
            return {'status': 500, 'data': None, 'error': str(e)}


# Global client instance
_client = None


def get_client() -> SupabaseClient:
    """Get or create the global Supabase client."""
    global _client
    if _client is None:
        _client = SupabaseClient()
    return _client


def select_from_table(table: str, columns: str = '*'):
    """Convenience function to select from a table."""
    return get_client().select(table, columns)
