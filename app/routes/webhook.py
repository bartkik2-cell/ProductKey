from fastapi import APIRouter, Request, Header
from app.services.shopify import verify_shopify_webhook
from app.services.sendgrid import send_email
from app.services.license import create_license, get_license_by_order
from app.config import FROM_SENDER_EMAIL, TO_EMAIL

router = APIRouter()


@router.post("/shopify-webhook")
async def shopify_webhook(
    request: Request,
    x_shopify_hmac_sha256: str = Header(None),
    x_shopify_topic: str = Header(None),
):
    print("🟢 Shopify Webhook Hit")

    raw_body = await request.body()

    if not verify_shopify_webhook(raw_body, x_shopify_hmac_sha256):
        print("❌ Invalid Shopify signature")
        return {"error": "Invalid signature"}

    data = await request.json()

    customer_email = (
        data.get("email")
        or data.get("customer", {}).get("email")
        or TO_EMAIL
    )

    if not customer_email:
        print("⚠️ No customer email")
        return {"status": "no email"}

    customer_name = data.get("customer", {}).get("first_name", "Customer")
    order_id = str(data.get("id"))

    # ✅ Prevent duplicate license
    existing_license = get_license_by_order(order_id)
    if existing_license:
        print(f"⚠️ License already exists for order {order_id}")
        return {"status": "already_processed"}

    # ✅ Generate license
    try:
        license_data = create_license(
            customer_email=customer_email,
            customer_name=customer_name,
            order_id=order_id,
            product_name=data.get("line_items", [{}])[0].get(
                "name", "Software License"
            ),
        )
    except Exception as e:
        print("❌ License generation failed:", str(e))
        return {"error": "license_failed"}

    formatted_key = license_data["license_key"]
    expiry_date = license_data["expiry_date"]

    # ✅ Prepare email (after license success)
    html = f"""
    <div style="font-family:Arial,sans-serif; max-width:600px; margin:auto;">
        <h2>Thank you for your purchase, {customer_name}!</h2>

        <p>Your license key:</p>
        <div style="background:#667eea; color:white; padding:20px;
                    font-family:monospace; font-size:20px; text-align:center;">
            {formatted_key}
        </div>

        <p><strong>Order ID:</strong> {order_id}</p>
        <p><strong>Expires:</strong> {expiry_date[:10]}</p>

        <p>If you need help, contact <strong>{FROM_SENDER_EMAIL}</strong></p>
    </div>
    """

    try:
        send_email(
            to_email=customer_email,
            from_email=FROM_SENDER_EMAIL,
            subject="Your License Key",
            html=html,
        )
        print("✅ Email sent:", customer_email)
    except Exception as e:
        print("❌ Email failed:", str(e))

    # ✅ Shopify-safe response
    return {"status": "ok"}
