import os


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


# Shopify
SHOPIFY_WEBHOOK_SECRET = require_env("SHOPIFY_WEBHOOK_SECRET")

# SendGrid
SENDGRID_API_KEY = require_env("SENDGRID_API_KEY")
FROM_SENDER_EMAIL = require_env("FROM_SENDER_EMAIL")

# Optional fallback email
TO_EMAIL = os.getenv("TO_EMAIL")

# Supabase
SUPABASE_URL = require_env("SUPABASE_URL")
SUPABASE_KEY = require_env("SUPABASE_KEY")


# import os

# SHOPIFY_WEBHOOK_SECRET = os.getenv("SHOPIFY_WEBHOOK_SECRET")
# SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
# FROM_SENDER_EMAIL = os.getenv("FROM_SENDER_EMAIL")
# TO_EMAIL = os.getenv("TO_EMAIL")
