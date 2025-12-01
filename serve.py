"""
Simple HTTP server to serve the HTML file
Run this script to serve index.html on http://localhost:8000
"""
import http.server
import socketserver
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # HIPAA Compliance: Restrict CORS to localhost only (development)
        # In production, use HTTPS and restrict to specific domains
        origin = self.headers.get('Origin', '')
        allowed_origins = ['http://localhost:8000', 'http://127.0.0.1:8000', '']
        
        if origin in allowed_origins or origin.startswith('http://localhost') or origin.startswith('http://127.0.0.1'):
            self.send_header('Access-Control-Allow-Origin', origin if origin else '*')
        else:
            # Reject unauthorized origins
            self.send_header('Access-Control-Allow-Origin', 'null')
        
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # HIPAA Compliance: Add security headers
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('X-XSS-Protection', '1; mode=block')
        super().end_headers()

    def log_message(self, format, *args):
        # Suppress default logging
        pass

if __name__ == "__main__":
    # Change to the directory where this script is located
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}/")
        print(f"Open http://localhost:{PORT}/index.html in your browser")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")

