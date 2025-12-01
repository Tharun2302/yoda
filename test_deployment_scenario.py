"""
Test script to simulate deployment HTTP scenario locally.
This helps test getUserMedia errors that occur in deployment (HTTP) vs localhost.
Proxies API calls to Flask backend on port 8002.
"""
import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import sys

PORT = 8003  # Different port to avoid conflicts
BACKEND_URL = 'http://127.0.0.1:8002'  # Flask backend

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests - proxy API calls to backend"""
        # Check if this is an API call
        if self.path.startswith('/voice/') or self.path.startswith('/chat/') or self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            # Serve static files
            self.serve_static_file()
    
    def do_POST(self):
        """Handle POST requests - proxy API calls to backend"""
        if self.path.startswith('/voice/') or self.path.startswith('/chat/') or self.path.startswith('/api/'):
            self.proxy_to_backend()
        else:
            self.send_error(404, "Not Found")
    
    def proxy_to_backend(self):
        """Proxy request to Flask backend"""
        try:
            # Get request body if POST
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length) if content_length > 0 else None
            
            # Parse path and query string
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query = parsed_path.query
            
            # Build backend URL
            backend_url = f"{BACKEND_URL}{path}"
            if query:
                backend_url += f"?{query}"
            
            # Create request to backend
            req = urllib.request.Request(backend_url, data=post_data, method=self.command)
            
            # Copy headers (except Host)
            for header, value in self.headers.items():
                if header.lower() not in ['host', 'connection']:
                    req.add_header(header, value)
            
            # Make request to backend
            with urllib.request.urlopen(req, timeout=30) as response:
                # Get response data
                response_data = response.read()
                
                # Send response
                self.send_response(response.getcode())
                
                # Copy response headers
                for header, value in response.headers.items():
                    if header.lower() not in ['connection', 'transfer-encoding']:
                        self.send_header(header, value)
                
                # Add CORS headers
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                
                self.end_headers()
                self.wfile.write(response_data)
                
        except urllib.error.HTTPError as e:
            # Forward HTTP errors
            error_body = e.read()
            self.send_response(e.code)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(error_body)
        except Exception as e:
            # Handle other errors
            print(f"[Proxy Error] {e}")
            self.send_error(502, f"Bad Gateway: {str(e)}")
    
    def serve_static_file(self):
        """Serve static files normally"""
        # Use parent class to serve file
        try:
            # Call parent do_GET which handles file serving
            super().do_GET()
        except Exception as e:
            print(f"[File Serve Error] {e}")
            self.send_error(404, "File Not Found")
    
    def end_headers(self):
        # Add CORS headers to all responses
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

def get_local_ip():
    """Get local IP address (not localhost)"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to a remote address (doesn't actually connect)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

if __name__ == '__main__':
    # Change to project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Get local IP (not localhost)
    local_ip = get_local_ip()
    
    # Start HTTP server (not HTTPS, simulating deployment)
    Handler = MyHTTPRequestHandler
    
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("=" * 60)
        print("DEPLOYMENT SCENARIO TEST SERVER")
        print("=" * 60)
        print(f"\n⚠️  This server runs on HTTP (not HTTPS) to simulate deployment")
        print(f"   This will trigger getUserMedia security errors")
        print(f"\n📡 Server running on:")
        print(f"   http://{local_ip}:{PORT}/index.html")
        print(f"   http://127.0.0.1:{PORT}/index.html")
        print(f"\n🔍 What to test:")
        print(f"   1. Open http://{local_ip}:{PORT}/index.html in your browser")
        print(f"   2. Click 'Voice On' button")
        print(f"   3. You should see: 'Voice mode requires a secure connection (HTTPS)'")
        print(f"   4. This simulates the deployment HTTP scenario")
        print(f"\n💡 IMPORTANT:")
        print(f"   1. Make sure Flask backend is running on port 8002 first!")
        print(f"   2. API calls will go to: http://127.0.0.1:8002")
        print(f"   3. This test is specifically for getUserMedia error handling")
        print(f"\n⏹️  Press Ctrl+C to stop")
        print("=" * 60)
        print()
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")

