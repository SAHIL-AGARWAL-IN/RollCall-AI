import streamlit as st


from supabase import create_client, Client

import time
from supabase import create_client, Client

class SupabaseClientWrapper:
    def __init__(self):
        self._client = None
        self._last_used = 0
        
    def get_client(self) -> Client:
        now = time.time()
        # If client is not created or has been idle for more than 30 seconds,
        # recreate it to avoid stale keep-alive connection disconnects from Supabase.
        if self._client is None or (now - self._last_used) > 30:
            self._client = create_client(
                st.secrets["SUPABASE_URL"],
                st.secrets["SUPABASE_KEY"]
            )
        self._last_used = now
        return self._client

    def __getattr__(self, name):
        client = self.get_client()
        self._last_used = time.time()
        return getattr(client, name)

supabase = SupabaseClientWrapper()