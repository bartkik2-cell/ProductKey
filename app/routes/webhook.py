# /api/webhook.py
# Standalone Shopify webhook handler for Vercel

from http.server import BaseHTTPRequestHandler
import json
import hmac
import hashlib
import base64
import os
import secrets
import string
from datetime import datetime, timedelta

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        """Set response headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
    
    def _send_json(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data).encode())
    
    def verify_shopify_hmac(self, body, hmac_header):
        """Verify Shopify webhook HMAC signature"""
        if not hmac_header:
            return False
        
        secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET", "").encode('utf-8')
        if not secret:
            print("⚠️ SHOPIFY_WEBHOOK_SECRET not set")
            return False
        
        # Calculate expected HMAC
        calculated_hmac = base64.b64encode(
            hmac.new(secret, body, hashlib.sha256).digest()
        ).decode('utf-8')
        
        # Compare with provided HMAC (constant-time comparison)
        return hmac.compare_digest(calculated_hmac, hmac_header)
    
    def generate_license_key(self):
        """Generate a random license key in format XXXX-XXXX-XXXX-XXXX"""
        characters = string.ascii_uppercase + string.digits
        segments = [
            ''.join(secrets.choice(characters) for _ in range(4))
            for _ in range(4)
        ]
        return '-'.join(segments)
    
    def create_license_in_db(self, license_key, customer_email, customer_name, order_id, product_name):
        """Create license record in Supabase"""
        try:
            from supabase import create_client
            
            SUPABASE_URL = os.environ.get("SUPABASE_URL")
            SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
            
            if not SUPABASE_URL or not SUPABASE_KEY:
                print("❌ Supabase credentials not set")
                return None
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            expiry_date = datetime.utcnow() + timedelta(days=365)
            
            # Insert license into database
            response = supabase.table("licenses").insert({
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
                "activated_devices": []
            }).execute()
            
            print(f"✅ License created: {license_key}")
            
            return {
                "license_key": license_key,
                "expiry_date": expiry_date.isoformat()
            }
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None
    
    def check_existing_license(self, order_id):
        """Check if license already exists for this order"""
        try:
            from supabase import create_client
            
            SUPABASE_URL = os.environ.get("SUPABASE_URL")
            SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
            
            supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            
            response = supabase.table("licenses").select("*").eq("order_id", order_id).execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"❌ Error checking existing license: {e}")
            return None
    
    def send_license_email(self, to_email, customer_name, license_key, order_id, expiry_date):
        """Send license key email via SendGrid"""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
            
            SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
            FROM_EMAIL = os.environ.get("FROM_SENDER_EMAIL")
            
            if not SENDGRID_API_KEY or not FROM_EMAIL:
                print("⚠️ SendGrid credentials not set")
                return False
            
            html = f"""
            <div style="font-family:Arial,sans-serif; max-width:600px; margin:auto; padding:20px;">
                <h2 style="color:#333;">Thank you for your purchase, {customer_name}!</h2>
                
                <p style="font-size:16px; color:#666;">Your HandMidi license key is ready:</p>
                
                <div style="background:#667eea; color:white; padding:20px; 
                            font-family:monospace; font-size:24px; text-align:center; 
                            border-radius:8px; margin:20px 0; letter-spacing:2px;">
                    {license_key}
                </div>
                
                <div style="background:#f5f5f5; padding:15px; border-radius:8px; margin:20px 0;">
                    <p style="margin:5px 0;"><strong>Order ID:</strong> {order_id}</p>
                    <p style="margin:5px 0;"><strong>Expires:</strong> {expiry_date[:10]}</p>
                    <p style="margin:5px 0;"><strong>Device Limit:</strong> 1 device</p>
                </div>
                
                <h3 style="color:#333; margin-top:30px;">How to Activate:</h3>
                <ol style="color:#666; line-height:1.8;">
                    <li>Download and install HandMidi</li>
                    <li>Launch the application</li>
                    <li>Enter your license key when prompted</li>
                    <li>Start creating music!</li>
                </ol>
                
                <hr style="border:none; border-top:1px solid #ddd; margin:30px 0;">
                
                <p style="font-size:14px; color:#999;">
                    Need help? Contact us at <strong>{FROM_EMAIL}</strong>
                </p>
            </div>
            """
            
            message = Mail(
                from_email=FROM_EMAIL,
                to_emails=to_email,
                subject="Your HandMidi License Key",
                html_content=html
            )
            
            sg = SendGridAPIClient(SENDGRID_API_KEY)
            sg.send(message)
            
            print(f"✅ Email sent to: {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Email error: {e}")
            return False
    
    def do_POST(self):
        """Handle Shopify webhook"""
        try:
            print("🟢 Shopify Webhook Hit")
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            raw_body = self.rfile.read(content_length)
            
            # Get HMAC header
            hmac_header = self.headers.get('X-Shopify-Hmac-Sha256')
            
            # Verify Shopify signature
            if not self.verify_shopify_hmac(raw_body, hmac_header):
                print("❌ Invalid Shopify signature")
                return self._send_json({"error": "Invalid signature"}, 401)
            
            # Parse JSON data
            data = json.loads(raw_body.decode('utf-8'))
            
            # Extract customer info
            customer_email = (
                data.get("email") 
                or data.get("customer", {}).get("email")
            )
            
            if not customer_email:
                print("⚠️ No customer email found")
                return self._send_json({"status": "no_email"}, 400)
            
            customer_name = data.get("customer", {}).get("first_name", "Customer")
            order_id = str(data.get("id"))
            
            # Get product name from line items
            line_items = data.get("line_items", [])
            product_name = line_items[0].get("name", "HandMidi License") if line_items else "HandMidi License"
            
            print(f"📧 Processing order {order_id} for {customer_email}")
            
            # Check if license already exists for this order
            existing = self.check_existing_license(order_id)
            if existing:
                print(f"⚠️ License already exists for order {order_id}")
                return self._send_json({
                    "status": "already_processed",
                    "license_key": existing.get("license_key")
                })
            
            # Generate new license key
            license_key = self.generate_license_key()
            print(f"🔑 Generated key: {license_key}")
            
            # Save to database
            license_data = self.create_license_in_db(
                license_key=license_key,
                customer_email=customer_email,
                customer_name=customer_name,
                order_id=order_id,
                product_name=product_name
            )
            
            if not license_data:
                print("❌ Failed to create license in database")
                return self._send_json({"error": "database_error"}, 500)
            
            # Send email with license key
            email_sent = self.send_license_email(
                to_email=customer_email,
                customer_name=customer_name,
                license_key=license_key,
                order_id=order_id,
                expiry_date=license_data["expiry_date"]
            )
            
            if not email_sent:
                print("⚠️ Email failed but license was created")
            
            print(f"✅ Webhook processed successfully for order {order_id}")
            
            return self._send_json({
                "status": "success",
                "order_id": order_id,
                "license_key": license_key,
                "email_sent": email_sent
            })
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return self._send_json({"error": "invalid_json"}, 400)
        
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            import traceback
            traceback.print_exc()
            return self._send_json({"error": "internal_error"}, 500)
    
    def do_GET(self):
        """Handle GET request (for testing)"""
        return self._send_json({
            "message": "Shopify webhook endpoint is active",
            "method": "POST only"
        })
