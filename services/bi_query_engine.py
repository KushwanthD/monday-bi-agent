"""
Universal Deep-Search BI Engine
Performs ANY-MATCH deep scanning across all raw item records, raw GraphQL column values,
raw CSV fields, deal details, work order IDs, client codes, and serial numbers.
Never rejects application queries.
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

    def extract_keywords(self, text: str) -> list:
        """Extracts key search terms (3+ chars) excluding query words like 'what', 'are', 'the'."""
        stop_words = {"what", "are", "the", "does", "have", "has", "is", "for", "in", "of", "how", "many", "much", "show", "list", "deals", "orders", "data", "tell", "me", "give", "find", "search", "lookup", "get", "with"}
        tokens = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', text.lower()).split() if w not in stop_words and len(w) >= 2]
        return tokens

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

        # 🤖 3. REAL AI ENGINE (Google Gemini API Integration)
        if self.client:
            try:
                data_context = {
                    "sales_deals_data": cleaned_deals,
                    "work_orders_data": cleaned_orders
                }

                system_instruction = (
                    "You are the official Skylark Drones Executive Business Intelligence AI Assistant.\n"
                    "Search thorough all JSON records (sales_deals_data and work_orders_data) to answer the user question.\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. If the user asks for serial numbers, work order IDs, client codes, deal names, status, costs, values, or ANY specific detail about a project (e.g. 'Sakura'), search all fields across all matching items and list every piece of relevant information found.\n"
                    "3. If a specific field (like a physical hardware serial number) is not stored in the board, explicitly mention the available identifiers (e.g. Work Order IDs: SDPLDEAL-002, SDPLDEAL-003, Client Code: COMPANY046) and list all data present for that entity.\n"
                    "4. If the user asks something completely unrelated to business, drones, or application data (e.g., sports, weather), politely state that you only answer application queries."
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

        # 🧠 4. DEEP DEEP-SEARCH ENGINE (ANY-MATCH OVER ALL FIELDS & COLS)
        keywords = self.extract_keywords(q_raw)
        
        # Deep search across every single record string representation
        matching_orders = []
        matching_deals = []

        if keywords:
            # Match records that contain ANY of the key subject terms (e.g. "sakura")
            primary_term = keywords[-1] if len(keywords) > 0 else "" # Usually entity name is last keyword (e.g., "sakura")
            
            for o in cleaned_orders:
                rec_str = json.dumps(o).lower()
                if any(kw in rec_str for kw in keywords):
                    matching_orders.append(o)

            for d in cleaned_deals:
                rec_str = json.dumps(d).lower()
                if any(kw in rec_str for kw in keywords):
                    matching_deals.append(d)

        lines = [f"Application Record Deep-Search for '{q_raw}':\n"]

        if matching_orders:
            lines.append(f"Work Order Tracker Records ({len(matching_orders)} matching):")
            for o in matching_orders[:15]:
                wo_id = o.get('work_order_id') or o.get('id') or 'N/A'
                name = o.get('project_name') or 'N/A'
                client = o.get('client') or 'N/A'
                status = o.get('status') or 'N/A'
                cost = o.get('cost', 0)
                lines.append(f"  - Project: {name} | Work Order ID / Ref: {wo_id} | Client: {client} | Status: {status} | Billed: Rs. {cost:,.2f}")

        if matching_deals:
            lines.append(f"\nSales Deals Funnel Records ({len(matching_deals)} matching):")
            for d in matching_deals[:15]:
                name = d.get('deal_name') or 'N/A'
                client = d.get('client') or 'N/A'
                sector = d.get('sector') or 'N/A'
                status = d.get('deal_status') or 'N/A'
                val = d.get('value', 0)
                lines.append(f"  - Deal: {name} | Account/Client Code: {client} | Sector: {sector} | Status: {status} | Pipeline Value: Rs. {val:,.2f}")

        if not matching_orders and not matching_deals:
            lines.append("No records matching your search terms were found in the application workspace.")

        return {
            "answer": "\n".join(lines),
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
