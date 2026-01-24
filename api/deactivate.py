# /api/deactivate.py
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

# Shared with activate.py in real implementation
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
            
            print(f"[Deactivate] Key: {key}, Device: {device_id}")
            
            # Check if key exists
            if key not in VALID_KEYS:
                print(f"[Deactivate] Key not found: {key}")
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'License key not found'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Check if key has any devices
            global activated_devices
            if key not in activated_devices or len(activated_devices[key]) == 0:
                print(f"[Deactivate] No devices for key: {key}")
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'Device not found for this license'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Find and remove device
            if device_id not in activated_devices[key]:
                print(f"[Deactivate] Device not found: {device_id}")
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'Device not found for this license'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            activated_devices[key].remove(device_id)
            
            print(f"[Deactivate] Device deactivated: {device_id}")
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'success': True,
                'message': 'License deactivated successfully',
                'device_id': device_id
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"[Deactivate] Error: {e}")
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
