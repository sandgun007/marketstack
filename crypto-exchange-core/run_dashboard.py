#!/usr/bin/env python3
"""
Simple HTTP server for serving the trading dashboard
Runs on a separate port from the API server
"""
import http.server
import socketserver
import os
import webbrowser
from threading import Thread

PORT = 8080
DASHBOARD_FILE = 'dashboard.html'

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = f'/{DASHBOARD_FILE}'
        return super().do_GET()

def run_server():
    """Start HTTP server"""
    Handler = DashboardHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("\n" + "="*70)
        print("TRADING DASHBOARD SERVER")
        print("="*70)
        print(f"\n📊 Dashboard running on: http://localhost:{PORT}")
        print(f"\n⚠️  Make sure API server is running separately:")
        print(f"   Terminal 1: python3 run_gateway.py")
        print(f"   Terminal 2: python3 run_dashboard.py")
        print(f"\n✅ Dashboard will auto-connect to API at http://localhost:8000")
        print(f"\nPress CTRL+C to stop server\n")

        # Try to open in browser
        try:
            webbrowser.open(f'http://localhost:{PORT}')
            print(f"🌐 Attempting to open dashboard in browser...\n")
        except:
            print(f"📖 To view dashboard, open: http://localhost:{PORT}\n")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Dashboard server stopped")

if __name__ == "__main__":
    run_server()
