from supabase import Client, create_client

from .config import get_settings


def get_public_client() -> Client:
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_anon_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_ANON_KEY must be configured")

    return create_client(settings.supabase_url, settings.supabase_anon_key)


def get_admin_client() -> Client:
    settings = get_settings()

    if not settings.supabase_url or not settings.supabase_service_role_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be configured")

    return create_client(settings.supabase_url, settings.supabase_service_role_key)
