# /api/validate.py
# SIMPLE TEST VERSION - Replace with database version for production

from http.server import BaseHTTPRequestHandler
import json

# Hardcoded valid keys for testing
VALID_KEYS = {
    '21EZ5E9N8BXR1UEY': {
        'active': True,
        'maxDevices': 3,
        'createdAt': '2026-01-24'
    },
    # Add more test keys here
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            key = data.get('key')
            
            if not key:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'License key is required'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            print(f"[Validate] Checking key: {key}")
            
            # Check if key exists
            license_data = VALID_KEYS.get(key)
            
            if not license_data:
                print(f"[Validate] Key not found: {key}")
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    'error': 'License key not found',
                    'detail': 'Not Found'
                }
                self.wfile.write(json.dumps(response).encode())
                return
            
            # Check if license is active
            if not license_data.get('active'):
                print(f"[Validate] Key inactive: {key}")
                self.send_response(403)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'error': 'License key is inactive'}
                self.wfile.write(json.dumps(response).encode())
                return
            
            print(f"[Validate] Key valid: {key}")
            
            # Return success
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {
                'valid': True,
                'key': key,
                'maxDevices': license_data.get('maxDevices'),
                'createdAt': license_data.get('createdAt')
            }
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            print(f"[Validate] Error: {e}")
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
