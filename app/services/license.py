import secrets
import string
from datetime import datetime, timedelta
from app.services.supabase import get_supabase_client


def generate_license_key() -> str:
    characters = string.ascii_uppercase + string.digits
    return "-".join(
        "".join(secrets.choice(characters) for _ in range(4))
        for _ in range(4)
    )


def create_license(
    customer_email: str,
    customer_name: str,
    order_id: str,
    product_name: str = "Software License",
) -> dict:
    license_key = generate_license_key()
    expiry_date = datetime.utcnow() + timedelta(days=365)

    response = (
        get_supabase_client()
        .table("licenses")
        .insert(
            {
                "license_key": license_key,
                "customer_email": customer_email,
                "customer_name": customer_name,
                "order_id": order_id,
                "product_name": product_name,
                "is_activated": False,
                "activated_at": None,
                "expiry_date": expiry_date.isoformat(),
                "created_at": datetime.utcnow().isoformat(),
                "device_limit": 1,
                "activation_count": 0,
            }
        )
        .execute()
    )

    return {
        "license_key": license_key,
        "license_id": response.data[0]["id"] if response.data else None,
        "expiry_date": expiry_date.isoformat(),
    }


def get_license_by_order(order_id: str) -> dict | None:
    response = (
        get_supabase_client()
        .table("licenses")
        .select("*")
        .eq("order_id", order_id)
        .execute()
    )

    return response.data[0] if response.data else None
