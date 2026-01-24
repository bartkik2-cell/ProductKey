import base64
import hashlib
import hmac
from app.config import SHOPIFY_WEBHOOK_SECRET


def verify_shopify_webhook(raw_body: bytes, hmac_header: str | None) -> bool:
    if not hmac_header:
        return False

    digest = hmac.new(
        SHOPIFY_WEBHOOK_SECRET.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).digest()

    generated_hmac = base64.b64encode(digest).decode()

    return hmac.compare_digest(generated_hmac, hmac_header)
