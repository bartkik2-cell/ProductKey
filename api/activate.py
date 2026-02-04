# /api/activate.py
# Production version with Supabase integration

from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add parent directory to path to import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from app.services.supabase import get_supabase_client
except ImportError:
    # Fallback for testing
    get_supabase_client = None

class handler(BaseHTTPRequestHandler):
    def _set_headers(self, status_code=200):
        """Set response headers with CORS"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def _send_json(self, data, status_code=200):
        """Send JSON response"""
        self._set_headers(status_code)
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self._set_headers(200)
    
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            key = data.get('key', '').strip()
            device_id = data.get('device_id', '').strip()
            
            # Validate inputs
            if not key or not device_id:
                print("[Activate] Missing key or device_id")
                return self._send_json({
                    'error': 'License key and device ID are required'
                }, 400)
            
            # Validate license key format (XXXX-XXXX-XXXX-XXXX = 19 chars with dashes)
            # Remove dashes for validation
            key_no_dashes = key.replace('-', '')
            if len(key_no_dashes) != 16 or not key_no_dashes.isalnum():
                print(f"[Activate] Invalid key format: {key}")
                return self._send_json({
                    'error': 'Invalid license key format'
                }, 400)
            
            print(f"[Activate] Key: {key}, Device: {device_id}")
            
            # Get Supabase client
            if not get_supabase_client:
                print("[Activate] ERROR: Supabase client not available")
                return self._send_json({
                    'error': 'Database connection not available'
                }, 500)
            
            supabase = get_supabase_client()
            
            # 1. Look up license in database
            response = supabase.table('licenses').select('*').eq('license_key', key).execute()
            
            if not response.data or len(response.data) == 0:
                print(f"[Activate] Key not found: {key}")
                return self._send_json({
                    'error': 'License key not found'
                }, 404)
            
            license_record = response.data[0]
            
            # 2. Check if license is active (not revoked/expired)
            is_activated = license_record.get('is_activated', False)
            device_limit = license_record.get('device_limit', 1)
            activation_count = license_record.get('activation_count', 0)
            
            # 3. Get current activated devices (stored as JSON array or comma-separated string)
            activated_devices = license_record.get('activated_devices', [])
            if isinstance(activated_devices, str):
                activated_devices = [d.strip() for d in activated_devices.split(',') if d.strip()]
            elif activated_devices is None:
                activated_devices = []
            
            print(f"[Activate] Current devices: {activated_devices}")
            print(f"[Activate] Device limit: {device_limit}")
            
            # 4. Check if this device is already activated
            if device_id in activated_devices:
                print(f"[Activate] Device already activated: {device_id}")
                return self._send_json({
                    'success': True,
                    'message': 'Device already activated',
                    'device_id': device_id,
                    'devices_used': len(activated_devices),
                    'devices_remaining': device_limit - len(activated_devices)
                }, 200)
            
            # 5. Check device limit
            if len(activated_devices) >= device_limit:
                print(f"[Activate] Max devices reached for key: {key}")
                return self._send_json({
                    'error': 'Maximum devices reached for this license',
                    'current': len(activated_devices),
                    'max': device_limit
                }, 409)
            
            # 6. Add device to license
            activated_devices.append(device_id)
            
            # Update database
            from datetime import datetime
            update_data = {
                'activated_devices': activated_devices,
                'is_activated': True,
                'activation_count': activation_count + 1
            }
            
            # Set activated_at timestamp only on first activation
            if not is_activated:
                update_data['activated_at'] = datetime.utcnow().isoformat()
            
            supabase.table('licenses').update(update_data).eq('license_key', key).execute()
            
            print(f"[Activate] Device activated successfully: {device_id}")
            print(f"[Activate] Total devices for key {key}: {len(activated_devices)}")
            
            return self._send_json({
                'success': True,
                'message': 'License activated successfully',
                'device_id': device_id,
                'devices_used': len(activated_devices),
                'devices_remaining': device_limit - len(activated_devices),
                'license_info': {
                    'customer_email': license_record.get('customer_email'),
                    'product_name': license_record.get('product_name'),
                    'expiry_date': license_record.get('expiry_date'),
                    'created_at': license_record.get('created_at')
                }
            }, 200)
            
        except json.JSONDecodeError as e:
            print(f"[Activate] JSON decode error: {e}")
            return self._send_json({
                'error': 'Invalid JSON in request body'
            }, 400)
        
        except Exception as e:
            print(f"[Activate] Error: {e}")
            import traceback
            traceback.print_exc()
            return self._send_json({
                'error': 'Internal server error',
                'detail': str(e)
            }, 500)
    
    def do_GET(self):
        """GET method not allowed"""
        return self._send_json({
            'error': 'Method not allowed. Use POST to activate a license.'
        }, 405)