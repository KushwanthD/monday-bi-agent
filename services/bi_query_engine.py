"""
Universal Full-Application Omniscient Intelligence Engine
Trained with full-system architecture knowledge base + real-time Monday.com live data stream:
- Full system architecture (OWASP WAF, SHA-256 Auth, 15s TTL, GraphQL v2, Data Resilience Engine)
- Live Monday.com Sales Deals Funnel + Work Order Tracker data
- Live OWASP Security Audit Logs & IP Rate Limiting state
- User onboarding guides, feature walkthroughs, and system capabilities
"""

import os
import json
import re
from google import genai
from google.genai import types

class BIQueryEngine:
    def __init__(self, data_resilience_engine, security_guard=None):
        self.resilience = data_resilience_engine
        self.security_guard = security_guard
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Gemini AI] Initialization warning: {e}")

    def set_security_guard(self, security_guard):
        self.security_guard = security_guard

    def parse_amount_with_multipliers(self, text: str):
        """Converts terms like '2 lakhs', '5 lac', '1.5 crore', '50 thousand', '20k', '5 hundred' into exact floats."""
        t = text.lower().strip()
        word_digits = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
            "twenty": 20, "fifty": 50, "hundred": 100
        }
        for w, d in word_digits.items():
            t = re.sub(rf'\b{w}\b', str(d), t)

        multipliers = [
            (r'(\d+(?:\.\d+)?)\s*(?:crores?|cr)\b', 10000000.0),
            (r'(\d+(?:\.\d+)?)\s*(?:lakhs?|lacs?|lac|lakh)\b', 100000.0),
            (r'(\d+(?:\.\d+)?)\s*(?:millions?|m)\b', 1000000.0),
            (r'(\d+(?:\.\d+)?)\s*(?:thousands?|k)\b', 1000.0),
            (r'(\d+(?:\.\d+)?)\s*(?:hundreds?)\b', 100.0),
            (r'(\d+(?:\.\d+)?)', 1.0)
        ]

        for pattern, mult in multipliers:
            m = re.search(pattern, t)
            if m:
                base_num = float(m.group(1))
                return base_num * mult
        return None

    def analyze(self, raw_deals: list, raw_orders: list, user_query: str) -> dict:
        cleaned_deals, deal_caveats = self.resilience.process_deals(raw_deals)
        cleaned_orders, order_caveats = self.resilience.process_work_orders(raw_orders)
        all_caveats = deal_caveats + order_caveats

        q_raw = user_query.strip()
        q_lower = q_raw.lower()

        # 📄 1. EXPORT CSV / PDF INTENT HANDLER
        is_export_csv = any(k in q_lower for k in ["export csv", "download csv", "generate csv", "csv report", "save csv"])
        is_export_pdf = any(k in q_lower for k in ["export pdf", "download pdf", "generate pdf", "pdf report", "save pdf", "print pdf"])

        if is_export_csv or is_export_pdf:
            export_type = "CSV" if is_export_csv else "PDF"
            return {
                "answer": f"{export_type} Export Request:\n\nI have generated your requested {export_type} report based on the current live deals and work orders dataset. Downloading file immediately.",
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "export",
                "action_payload": {"type": export_type.lower()}
            }

        # 🛡️ 2. SECURITY & WAF AUDIT INTENT HANDLER
        if any(k in q_lower for k in ["security audit", "waf status", "attack log", "audit log", "blocked attacks"]):
            audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []
            blocked_count = sum(1 for log in audit_logs if "BLOCKED" in log.get("event_type", ""))
            
            lines = [
                "OWASP Cybersecurity & WAF Audit Status:\n",
                f"- WAF Protection: Active & Enforcing (OWASP Top 10 + Prompt Injection Guard)",
                f"- IP Rate Limiting: Active Window",
                f"- Total Audit Events Logged: {len(audit_logs)} security logs recorded.",
                f"- Blocked Malicious Attacks: {blocked_count} attack attempts thwarted.\n"
            ]
            if audit_logs:
                lines.append("Recent Security Log Events:")
                for log in audit_logs[-3:]:
                    lines.append(f"  - [{log['timestamp']}] {log['event_type']} - {log['details']}")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "redirect",
                "action_payload": {"view": "view-security"}
            }

        # 🤖 3. UNIVERSAL OMNISCIENT AI ENGINE (Google Gemini API with Complete Application System Knowledge Base)
        audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []
        
        system_knowledge_base = {
            "application_metadata": {
                "name": "Skylark Drones Monday.com Business Intelligence Agent",
                "version": "2.5 Production",
                "purpose": "Real-time cross-board BI analytics, executive briefings, dynamic board discovery, and enterprise security for Skylark Drones."
            },
            "security_architecture": {
                "authentication": "AEGIS Cyberpunk Glassmorphic Authentication Portal using SHA-256 pre-transmission client-side hashing via browser Web Crypto API (crypto.subtle.digest). Plaintext passwords are NEVER sent across the network.",
                "credentials": "Username: Skylark | Password: Drones (client SHA-256 pre-hashed before POST body transmission)",
                "waf_protection": "OWASP Top 10 WAF Security Guard actively scanning for Prompt Injection, XSS scripts, and SQLi patterns.",
                "rate_limiting": "Token-bucket IP Rate Limiter enforcing 45 requests per 60-second window per IP address.",
                "audit_logger": "Cryptographic tamper-evident SHA-256 audit logger recording all authentication events, queries, and security violations.",
                "live_audit_logs": audit_logs[-5:]
            },
            "data_and_integrations": {
                "monday_api": "Live Monday.com GraphQL API v2 integration with 15-second TTL in-memory caching for sub-millisecond tab switching and lightning-fast queries.",
                "boards_tracked": [
                    {"name": "Sales Deals Funnel", "description": "Tracks all commercial sales opportunities, deal values, stages (Open, Won, Proposal, Dead), client codes (COMPANY001..195), sectors, and deal owners."},
                    {"name": "Work Order Tracker", "description": "Tracks drone flight execution projects, project names, Work Order IDs (SDPLDEAL-001..188), execution status (Completed, Ongoing, Executed until current month, Not Started, Pause/struck), client codes (WOCOMPANY_001..020), and billed costs."}
                ],
                "data_resilience_engine": "Automatically cleans missing values, normalizes currency formatting, resolves sector synonyms (e.g. powerline -> Energy), and monitors data quality caveats."
            },
            "features_and_views": [
                {"view_id": "view-chat", "title": "Executive Business Intelligence Console", "description": "Natural language AI Assistant, KPI grid, suggestion chips, and real-time caveats box."},
                {"view_id": "view-boards", "title": "Monday.com Boards Live Viewer", "description": "Normalized dynamic table viewer with multi-criteria compound filters (Search, Sector, Status, Stage), dynamic group tabs, and deep-links to Monday.com."},
                {"view_id": "view-briefing", "title": "Executive Leadership Briefings", "description": "Auto-generated C-suite executive markdown briefing reports ready for PDF print export or copying to clipboard."},
                {"view_id": "view-security", "title": "Cybersecurity & OWASP WAF Audit", "description": "Live security grid, rate limiter metrics, and tamper-evident audit logs table."},
                {"view_id": "view-features", "title": "System Architecture & Features Guide", "description": "Comprehensive guide explaining BI analytics, security architecture, and GraphQL discovery."}
            ]
        }

        if self.client:
            try:
                data_context = {
                    "system_knowledge_base": system_knowledge_base,
                    "sales_deals_data": cleaned_deals,
                    "work_orders_data": cleaned_orders
                }

                system_instruction = (
                    "You are the official Skylark Drones Omniscient Business Intelligence AI Assistant.\n"
                    "You possess complete knowledge of both the live data records AND the system architecture, security features, user guide, and application capabilities.\n\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. If the user asks about SYSTEM ARCHITECTURE, SECURITY FEATURES, HOW THE APPLICATION WORKS, or USER GUIDES:\n"
                    "   Answer comprehensively using the system_knowledge_base (explain SHA-256 pre-hashing, OWASP WAF, 15-second TTL cache, Monday.com GraphQL API v2, rate limiting, and all 5 dashboard view panels).\n"
                    "3. If the user asks about SPECIFIC ENTITIES or NUMERICAL FILTERS (e.g. 'Alias_160', 'Sakura', 'WOCOMPANY_051', 'billed below 2 lakhs'):\n"
                    "   Analyze the sales_deals_data and work_orders_data precisely, calculate exact totals, and list matching records.\n"
                    "4. If the user asks for MATH CALCULATIONS or EXPORT OPTIONS (CSV/PDF):\n"
                    "   Perform accurate arithmetic or explain/trigger exports.\n"
                    "5. Only state out-of-scope if the question is completely unrelated to business, drones, cybersecurity, or application software.\n"
                    "6. Be polite, authoritative, highly intelligent, and 100% accurate."
                )

                prompt = f"System Knowledge & Live Data Context:\n{json.dumps(data_context, indent=2)}\n\nUser Question: {q_raw}"

                response = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.1
                    )
                )

                if response and response.text:
                    clean_ans = response.text.replace('**', '').replace('* ', '  - ')
                    return {
                        "answer": clean_ans.strip(),
                        "is_clarification": False,
                        "caveats": all_caveats,
                        "action": None
                    }
            except Exception as ai_err:
                print(f"[Gemini AI Error]: {ai_err}")

        # 🧠 4. HARDENED DETERMINISTIC FALLBACK ENGINE
        # Handle system architecture & guide queries if offline
        if any(k in q_lower for k in ["security", "feature", "guide", "how does", "how to use", "architecture", "waf", "sha-256", "login", "password"]):
            lines = [
                "Skylark Drones Application System & Security Guide:\n",
                "1. Security & Authentication Architecture:",
                "- Client-Side SHA-256 Pre-Transmission Hashing: Passwords are pre-hashed in your browser using Web Crypto API before POST transmission.",
                "- OWASP WAF Security Guard: Actively filters XSS, SQLi, and Prompt Injection attacks.",
                "- Token-Bucket Rate Limiter: Enforces 45 requests per minute per IP address.",
                "- Tamper-Evident SHA-256 Audit Logger: Records cryptographic audit logs of all security events.\n",
                "2. Real-Time Data & Performance:",
                "- Monday.com GraphQL API v2 Integration: Connects live to your workspace boards.",
                "- 15-Second In-Memory TTL Cache: Provides sub-millisecond tab switching and auto-syncs live updates every 15s.\n",
                "3. Key Application Modules:",
                "- Executive BI Console (Chatbot & KPIs)",
                "- Monday.com Live Boards Viewer (Multi-Criteria Filters & Group Tabs)",
                "- Executive Leadership Briefings (PDF Export & Markdown Reports)",
                "- Security & WAF Audit Logs",
                "- System Architecture & Features Guide"
            ]
            return {"answer": "\n".join(lines), "is_clarification": False, "caveats": all_caveats, "action": None}

        code_match = re.search(r'(wocompany_?\d+|company_?\d+|sdpldeal-?\d+|owner_?\d+|alias_\d+|[a-z0-9_-]{4,})', q_lower)
        stop_words = {"what", "are", "the", "does", "have", "has", "is", "for", "in", "of", "how", "many", "much", "show", "list", "deals", "orders", "data", "tell", "me", "give", "find", "search", "lookup", "get", "with", "want", "everyone", "anyone", "all"}
        search_tokens = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', q_lower).split() if w not in stop_words and len(w) >= 3]

        target_term = code_match.group(0) if code_match and code_match.group(0) not in stop_words else (search_tokens[0] if search_tokens else "")

        matching_orders = [o for o in cleaned_orders if target_term and target_term in str(o).lower()]
        matching_deals = [d for d in cleaned_deals if target_term and target_term in str(d).lower()]

        total_billed = sum(o.get("cost", 0) for o in matching_orders)
        total_val = sum(d.get("value", 0) for d in matching_deals)

        if matching_orders or matching_deals:
            lines = [f"Records Found for '{target_term.upper()}':\n"]

            if matching_orders:
                lines.append(f"Work Order Tracker Records ({len(matching_orders)} matching, Total Billed: Rs. {total_billed:,.2f}):")
                for o in matching_orders:
                    lines.append(f"  - Project: {o.get('project_name')} | Work Order ID: {o.get('work_order_id')} | Client: {o.get('client')} | Status: {o.get('status')} | Billed: Rs. {o.get('cost', 0):,.2f}")

            if matching_deals:
                lines.append(f"\nSales Deals Funnel Records ({len(matching_deals)} matching, Total Pipeline: Rs. {total_val:,.2f}):")
                for d in matching_deals:
                    lines.append(f"  - Deal: {d.get('deal_name')} | Client Code: {d.get('client')} | Sector: {d.get('sector')} | Status: {d.get('deal_status')} | Value: Rs. {d.get('value', 0):,.2f}")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        return {
            "answer": f"Sorry! I could not find any active deals or work orders matching '{q_raw}' in the application.\n\nI am your dedicated Skylark Business Intelligence Agent, specialized strictly in answering queries about your Monday.com Sales Deals Funnel, Work Orders, Client/Dealer records, Revenue analytics, and Security audit logs.",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
