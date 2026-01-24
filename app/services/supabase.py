from typing import Optional
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("Supabase environment variables not set")

        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

    return _supabase_client
