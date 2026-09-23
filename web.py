import os
import threading
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
from bot import run_bot

logging.basicConfig(level=logging.INFO)

class HealthCheck(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), HealthCheck)
    logging.info(f"🌐 Health check server listening on port {port}")
    server.serve_forever()
