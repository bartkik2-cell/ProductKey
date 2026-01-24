# /api/activate.py
# SIMPLE TEST VERSION - Replace with database version for production

from http.server import BaseHTTPRequestHandler
import json

# Valid keys
VALID_KEYS = {
    '21EZ5E9N8BXR1UEY': {
        'active': True,
        'maxDevices': 3
    },
}

# In-memory device storage (resets on deployment)
# WARNING: This won't persist! Use a real database for production
activated_devices = {}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            key = data.get('key')
            device_id = data.get('device_id')
            
            if not key or not device_id:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'License key and device ID are required'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            print(f"[Activate] Key: {key}, Device: {device_id}")
            
            # 1. Check if key exists
            license_data = VALID_KEYS.get(key)
            
            if not license_data:
                print(f"[Activate] Key not found: {key}")
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'License key not found'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # 2. Check if license is active
            if not license_data.get('active'):
                print(f"[Activate] Key inactive: {key}")
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'License key is inactive'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # 3. Initialize devices list for this key if not exists
            global activated_devices
            if key not in activated_devices:
                activated_devices[key] = []
            
            # 4. Check if device is already activated
            if device_id in activated_devices[key]:
                print(f"[Activate] Device already activated: {device_id}")
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'success': True,
                    'message': 'Device already activated',
                    'device_id': device_id
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # 5. Check device limit
            max_devices = license_data.get('maxDevices', 3)
            if len(activated_devices[key]) >= max_devices:
                print(f"[Activate] Max devices reached for key: {key}")
                self.send_response(409)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'error': 'Maximum devices reached for this license',
                    'current': len(activated_devices[key]),
                    'max': max_devices
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # 6. Add device to license
            activated_devices[key].append(device_id)
            
            print(f"[Activate] Device activated successfully: {device_id}")
            print(f"[Activate] Total devices for key {key}: {len(activated_devices[key])}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'success': True,
                'message': 'License activated successfully',
                'device_id': device_id,
                'devices_used': len(activated_devices[key]),
                'devices_remaining': max_devices - len(activated_devices[key])
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"[Activate] Error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'error': 'Internal server error',
                'detail': str(e)
            }
            self.wfile.write(json.dumps(response).encode())
    
    def do_GET(self):
        self.send_response(405)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'error': 'Method not allowed'}
        self.wfile.write(json.dumps(response).encode())
