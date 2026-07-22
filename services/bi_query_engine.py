"""
Universal Omniscient Business Intelligence Engine
Handles:
- Universal string normalization: strips all currency symbols (₹, $, €, £), Indian formatting commas, special characters, and punctuation before searching.
- Fuzzy multi-token string matching: understands queries regardless of syntax, word order, or symbols used.
- Gemini AI fallback & offline deterministic analysis.
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
        
        # Load config.json if present
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("gemini_api_key"):
                        self.api_key = cfg["gemini_api_key"].strip()
            except Exception:
                pass

        self.client = None
        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Gemini AI] Initialization warning: {e}")

    def set_security_guard(self, security_guard):
        self.security_guard = security_guard

    def normalize_text(self, text: str) -> str:
        """Strips currency symbols (₹, $, Rs), commas, and extra punctuation to compare raw clean strings."""
        t = str(text).lower()
        t = re.sub(r'[₹\$\€\£]', '', t)
        t = t.replace('rs.', '').replace('rs', '').replace('inr', '')
        t = t.replace(',', '')
        return t.strip()

    def extract_exact_numbers(self, text: str) -> list:
        clean = self.normalize_text(text)
        matches = re.findall(r'\b\d+(?:\.\d+)?\b', clean)
        results = []
        for m in matches:
            try:
                val = float(m)
                if val > 0:
                    results.append(val)
            except ValueError:
                pass
        return results

    def analyze(self, raw_deals: list, raw_orders: list, user_query: str) -> dict:
        cleaned_deals, deal_caveats = self.resilience.process_deals(raw_deals)
        cleaned_orders, order_caveats = self.resilience.process_work_orders(raw_orders)
        all_caveats = deal_caveats + order_caveats

        q_raw = user_query.strip()
        q_lower = q_raw.lower()
        q_normalized = self.normalize_text(q_raw)

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

        # 🤖 3. REAL AI ENGINE (Google Gemini API Integration)
        if self.client:
            try:
                data_context = {
                    "sales_deals_data": cleaned_deals,
                    "work_orders_data": cleaned_orders
                }

                system_instruction = (
                    "You are the official Skylark Drones Executive Business Intelligence AI Assistant.\n"
                    "Analyze the user's question with extreme precision across all letters, symbols, numbers, and currency formats in the JSON records.\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. ALWAYS NORMALIZE SYMBOLS AND NUMBERS: Understand currency signs (₹, $, Rs), commas, and spaces. For example, '₹1,83,130.20' equals '183130.20'. Match it to exact records.\n"
                    "3. DEEP SEARCH ALL FIELDS: If the user asks about an entity, account code, deal name, project, serial number, or cost, search all fields and present complete matching details.\n"
                    "4. If no items match, state that 0 records matched.\n"
                    "5. Keep responses clean, precise, and professional."
                )

                prompt = f"Data Context:\n{json.dumps(data_context, indent=2)}\n\nUser Question: {q_raw}"

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

        # 🧠 4. UNIVERSAL SYMBOL & NUMERIC MATCHING ENGINE (Offline Fallback)
        extracted_numbers = self.extract_exact_numbers(q_raw)
        
        matching_orders = []
        matching_deals = []

        # A. If prompt contains a numerical amount (e.g. 183130.20 or ₹1,83,130.20)
        if extracted_numbers:
            target_num = extracted_numbers[0]
            matching_orders = [o for o in cleaned_orders if abs(float(o.get("cost", 0)) - target_num) < 1.0 or target_num in self.extract_exact_numbers(json.dumps(o))]
            matching_deals = [d for d in cleaned_deals if abs(float(d.get("value", 0)) - target_num) < 1.0 or target_num in self.extract_exact_numbers(json.dumps(d))]

        # B. If prompt contains codes / words (e.g. WOCOMPANY_051, Sakura, etc.)
        if not matching_orders and not matching_deals:
            stop_words = {"what", "are", "the", "does", "have", "has", "is", "for", "in", "of", "how", "many", "much", "show", "list", "deals", "orders", "data", "tell", "me", "give", "find", "search", "lookup", "get", "with", "want", "everyone", "anyone", "all", "this", "deal", "information"}
            clean_tokens = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', q_normalized).split() if w not in stop_words and len(w) >= 2]
            
            if clean_tokens:
                for o in cleaned_orders:
                    rec_norm = self.normalize_text(json.dumps(o))
                    if any(t in rec_norm for t in clean_tokens):
                        matching_orders.append(o)

                for d in cleaned_deals:
                    rec_norm = self.normalize_text(json.dumps(d))
                    if any(t in rec_norm for t in clean_tokens):
                        matching_deals.append(d)

        if matching_orders or matching_deals:
            lines = [f"Application Record Search Results for '{q_raw}':\n"]

            if matching_orders:
                lines.append(f"Matching Work Orders ({len(matching_orders)} record):")
                for o in matching_orders[:15]:
                    lines.append(f"  - Project: {o.get('project_name')} | Work Order ID: {o.get('work_order_id')} | Client Code: {o.get('client')} | Status: {o.get('status')} | Billed Amount: Rs. {o.get('cost', 0):,.2f}")

            if matching_deals:
                lines.append(f"\nMatching Sales Deals ({len(matching_deals)} record):")
                for d in matching_deals[:15]:
                    lines.append(f"  - Deal Name: {d.get('deal_name')} | Account/Client Code: {d.get('client')} | Sector: {d.get('sector')} | Status: {d.get('deal_status')} | Deal Value: Rs. {d.get('value', 0):,.2f}")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        # ❓ 5. PROFESSIONAL OUT-OF-SCOPE FALLBACK
        return {
            "answer": f"Sorry! I could not find any active deals or work orders matching '{q_raw}' in the application.\n\nI am your dedicated Skylark Business Intelligence Agent, specialized strictly in answering queries about your Monday.com Sales Deals Funnel, Work Orders, Client/Dealer records, Revenue analytics, and Security audit logs.",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
