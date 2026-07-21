"""
Security Guard & WAF Middleware for Monday.com BI Agent
Implements OWASP defenses: Input Sanitization, Prompt Injection Detection, Rate Limiting, and Security Audit Logging.
"""

import html
import re
import time
import hashlib

class SecurityGuard:
    def __init__(self, max_requests_per_minute=30):
        self.max_requests = max_requests_per_minute
        self.rate_limit_store = {}
        self.audit_log = []
        
        # Threat patterns for prompt injection & malicious queries
        self.injection_patterns = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"system\s+prompt\s+override",
            r"<script.*?>.*?</script>",
            r"javascript:",
            r"drop\s+table",
            r"union\s+select",
            r"eval\(",
            r"exec\(",
            r"__import__"
        ]

    def check_rate_limit(self, client_ip: str) -> bool:
        """Rate limiting per IP address"""
        now = time.time()
        window_start = now - 60
        
        # Clean expired timestamps
        timestamps = self.rate_limit_store.get(client_ip, [])
        timestamps = [t for t in timestamps if t > window_start]
        
        if len(timestamps) >= self.max_requests:
            self.log_audit("RATE_LIMIT_EXCEEDED", f"IP {client_ip} exceeded rate limit.")
            return False
            
        timestamps.append(now)
        self.rate_limit_store[client_ip] = timestamps
        return True

    def sanitize_input(self, text: str) -> str:
        """Sanitizes input strings against XSS and script injections"""
        if not text:
            return ""
        # Strip excessive control characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F]', '', text)
        # HTML entity escape
        escaped = html.escape(cleaned)
        return escaped.strip()

    def detect_prompt_injection(self, query: str) -> bool:
        """Detects malicious prompt injection vectors"""
        query_lower = query.lower()
        for pattern in self.injection_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                self.log_audit("PROMPT_INJECTION_DETECTED", f"Blocked pattern '{pattern}' in query: '{query[:50]}...'")
                return True
        return False

    def log_audit(self, event_type: str, details: str):
        """Creates a tamper-evident audit log entry"""
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "event_type": event_type,
            "details": details
        }
        # Hash checksum for audit integrity
        raw_str = f"{entry['timestamp']}|{entry['event_type']}|{entry['details']}"
        entry["checksum"] = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()[:16]
        self.audit_log.append(entry)
        if len(self.audit_log) > 100:
            self.audit_log.pop(0)

    def get_audit_logs(self) -> list:
        """Returns recorded security audit logs"""
        return self.audit_log

    def get_security_headers(self) -> dict:
        """OWASP recommended HTTP security headers"""
        return {
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
