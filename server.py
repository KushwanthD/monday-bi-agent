"""
Skylark Drones — Monday BI Agent HTTP Server
Includes OWASP WAF Security Guard, Rate Limiting, Audit Logging, and SHA-256 Password Authentication.
"""

import os
import json
import time
import urllib.parse
import urllib.request
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler

from services.monday_client import MondayClient
from services.data_resilience import DataResilienceEngine
from services.bi_query_engine import BIQueryEngine
from middleware.security_guard import SecurityGuard

# Initialize Core Services
monday_client = MondayClient()
resilience_engine = DataResilienceEngine()
security_guard = SecurityGuard()
query_engine = BIQueryEngine(resilience_engine, security_guard)

# SHA-256 Expected Credentials
EXPECTED_USERNAME = "Skylark"
EXPECTED_PASS_HASH = hashlib.sha256("Drones".encode("utf-8")).hexdigest()
VALID_SESSION_TOKEN = "skylark_sec_session_" + hashlib.sha256("Skylark_Drones_Auth_Secret".encode("utf-8")).hexdigest()[:16]

class BIAgentHandler(BaseHTTPRequestHandler):
    def _set_security_headers(self, status_code=200, content_type="application/json"):
        headers = security_guard.get_security_headers()
        self.send_response(status_code)
        for h_key, h_val in headers.items():
            self.send_header(h_key, h_val)
        self.send_header("Content-Type", content_type)
        self.end_headers()
    
    def do_HEAD(self):
        self._set_security_headers(200, "text/html")



    def do_GET(self):
        client_ip = self.client_address[0]
        if not security_guard.check_rate_limit(client_ip):
            self._set_security_headers(429)
            self.wfile.write(json.dumps({"error": "Rate limit exceeded. Try again in a minute."}).encode("utf-8"))
            return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/health":
            self._set_security_headers(200)
            res = {
                "status": "healthy",
                "monday_connected": monday_client.is_configured(),
                "mode": "Live Monday.com GraphQL" if monday_client.is_configured() else "Local Resilient Dataset Preview",
                "security_status": "Active (OWASP WAF + Rate Limiter + SHA-256 Auth + Audit Logger)"
            }
            self.wfile.write(json.dumps(res).encode("utf-8"))
            return

        elif path == "/api/security/audit":
            self._set_security_headers(200)
            self.wfile.write(json.dumps({"audit_logs": security_guard.audit_log}).encode("utf-8"))
            return

        elif path == "/api/monday/boards":
            try:
                all_workspace_boards = monday_client.fetch_all_workspace_boards()
                raw_deals = monday_client.load_deals_data()
                raw_orders = monday_client.load_work_orders_data()
                
                cleaned_deals, deal_caveats = resilience_engine.process_deals(raw_deals)
                cleaned_orders, order_caveats = resilience_engine.process_work_orders(raw_orders)
                
                res = {
                    "deals": cleaned_deals,
                    "work_orders": cleaned_orders,
                    "caveats": deal_caveats + order_caveats,
                    "all_boards": all_workspace_boards
                }
                self._set_security_headers(200)
                self.wfile.write(json.dumps(res, indent=2).encode("utf-8"))
            except Exception as e:
                self._set_security_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # Static file serving for Frontend UI
        else:
            public_dir = os.path.join(os.path.dirname(__file__), "public")
            filepath = os.path.normpath(os.path.join(public_dir, path.lstrip("/")))

            if path == "/" or not os.path.exists(filepath) or os.path.isdir(filepath):
                filepath = os.path.join(public_dir, "index.html")

            # Determine content type
            if filepath.endswith(".html"):
                ct = "text/html; charset=utf-8"
            elif filepath.endswith(".css"):
                ct = "text/css; charset=utf-8"
            elif filepath.endswith(".js"):
                ct = "application/javascript; charset=utf-8"
            elif filepath.endswith(".png"):
                ct = "image/png"
            elif filepath.endswith(".svg"):
                ct = "image/svg+xml"
            else:
                ct = "text/plain; charset=utf-8"

            try:
                with open(filepath, "rb") as f:
                    content = f.read()
                self._set_security_headers(200, content_type=ct)
                self.wfile.write(content)
            except Exception as e:
                self._set_security_headers(404)
                self.wfile.write(json.dumps({"error": f"File not found: {str(e)}"}).encode("utf-8"))

    def do_POST(self):
        client_ip = self.client_address[0]
        if not security_guard.check_rate_limit(client_ip):
            self._set_security_headers(429)
            self.wfile.write(json.dumps({"error": "Rate limit exceeded. Try again in a minute."}).encode("utf-8"))
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body_json = {}
        if content_length > 0:
            body_bytes = self.rfile.read(content_length)
            try:
                body_json = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._set_security_headers(400)
                self.wfile.write(json.dumps({"error": "Invalid JSON body payload"}).encode("utf-8"))
                return

        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/auth/login":
            uname = str(body_json.get("username", "")).strip()
            pass_hash = str(body_json.get("password_hash", "")).strip().lower()

            if uname == EXPECTED_USERNAME and pass_hash == EXPECTED_PASS_HASH:
                security_guard.log_audit("AUTHENTICATION_SUCCESS", f"User '{uname}' authenticated via SHA-256.")
                self._set_security_headers(200)
                self.wfile.write(json.dumps({
                    "status": "authenticated",
                    "token": VALID_SESSION_TOKEN,
                    "username": uname,
                    "message": "Authentication successful"
                }).encode("utf-8"))
            else:
                security_guard.log_audit("AUTHENTICATION_FAILURE", f"Failed login attempt for username: '{uname}'")
                self._set_security_headers(401)
                self.wfile.write(json.dumps({
                    "error": "Invalid username or password.",
                    "details": "Authentication failed. Verify credentials."
                }).encode("utf-8"))
            return

        elif path == "/api/query":
            raw_query = body_json.get("query", "")
            
            # WAF prompt injection & XSS check
            if security_guard.detect_prompt_injection(raw_query):
                self._set_security_headers(400)
                self.wfile.write(json.dumps({
                    "error": "Query blocked by WAF Security Guard.",
                    "details": "Malicious prompt injection or unsafe script pattern detected."
                }).encode("utf-8"))
                return

            clean_query = security_guard.sanitize_input(raw_query)
            security_guard.log_audit("QUERY_EXECUTED", f"Query: '{clean_query[:60]}...'")

            raw_deals = monday_client.load_deals_data()
            raw_orders = monday_client.load_work_orders_data()
            
            result = query_engine.analyze(raw_deals, raw_orders, clean_query)
            
            self._set_security_headers(200)
            self.wfile.write(json.dumps(result).encode("utf-8"))
            return

        elif path == "/api/leadership-update":
            security_guard.log_audit("LEADERSHIP_UPDATE_GENERATED", "Generated executive briefing update.")
            raw_deals = monday_client.load_deals_data()
            raw_orders = monday_client.load_work_orders_data()
            
            result = query_engine.analyze(raw_deals, raw_orders, "full summary of everything including pipeline revenue closed won negotiations and flight operations")
            briefing_text = result.get("answer", "Unable to generate briefing.")
            
            self._set_security_headers(200)
            self.wfile.write(json.dumps({"markdown": briefing_text}).encode("utf-8"))
            return

        else:
            self._set_security_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

def run_server(port=3000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, BIAgentHandler)
    print(f"[Server] Skylark Drones BI Agent Server running at http://localhost:{port}")
    print(f"[Security] OWASP WAF Security Guard & SHA-256 Auth Active")
    print(f"[Monday API] Live Monday.com Connected: {monday_client.is_configured()}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    run_server(port)
