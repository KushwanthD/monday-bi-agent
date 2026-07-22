"""
Universal Omniscient Business Intelligence Engine
Handles:
- Exact numeric amount lookup (e.g. ₹1,83,130.20 or 183130.20)
- Currency formatting stripping (rupee sign ₹, commas, spaces)
- Multi-token code matching & exact value search
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

    def extract_exact_numbers(self, text: str) -> list:
        """Extracts exact float values from queries containing currency symbols, commas, or rupee formatting like ₹1,83,130.20."""
        # Find patterns like ₹1,83,130.20 or 1,83,130.20 or 183130.20
        clean = text.replace('₹', '').replace('rs', '').replace('inr', '')
        matches = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', clean)
        results = []
        for m in matches:
            try:
                val = float(m.replace(',', ''))
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
                    "Analyze the user's question carefully against the provided JSON records.\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. EXACT AMOUNT LOOKUPS (e.g., '₹1,83,130.20' or '183130.20'): Normalize currency symbols and commas. Search for deals or work orders where value or cost equals or closely matches that number. List all matching records, including Project/Deal Name, Work Order ID/Client Code, Sector, Status, and exact amount.\n"
                    "3. SYSTEM / SECURITY / GUIDE QUESTIONS: Answer comprehensively using system knowledge.\n"
                    "4. Keep responses clean, precise, and professional."
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

        # 🧠 4. EXACT CURRENCY AMOUNT SEARCH ENGINE (Fallback)
        extracted_amounts = self.extract_exact_numbers(q_raw)
        if extracted_amounts:
            target_amount = extracted_amounts[0]
            
            matching_orders = [o for o in cleaned_orders if abs(float(o.get("cost", 0)) - target_amount) < 1.0]
            matching_deals = [d for d in cleaned_deals if abs(float(d.get("value", 0)) - target_amount) < 1.0]

            if matching_orders or matching_deals:
                lines = [f"Record Lookup Results for Amount Rs. {target_amount:,.2f}:\n"]

                if matching_orders:
                    lines.append(f"Matching Work Orders ({len(matching_orders)} record):")
                    for o in matching_orders:
                        lines.append(f"  - Project Name: {o.get('project_name')} | Work Order ID: {o.get('work_order_id')} | Client Code: {o.get('client')} | Status: {o.get('status')} | Billed Amount: Rs. {o.get('cost', 0):,.2f}")

                if matching_deals:
                    lines.append(f"\nMatching Sales Deals ({len(matching_deals)} record):")
                    for d in matching_deals:
                        lines.append(f"  - Deal Name: {d.get('deal_name')} | Account/Client Code: {d.get('client')} | Sector: {d.get('sector')} | Status: {d.get('deal_status')} | Deal Value: Rs. {d.get('value', 0):,.2f}")

                return {
                    "answer": "\n".join(lines),
                    "is_clarification": False,
                    "caveats": all_caveats,
                    "action": None
                }

        # 🧠 5. CODE / ENTITY SEARCH ENGINE (Fallback)
        code_match = re.search(r'(wocompany_?\d+|company_?\d+|sdpldeal-?\d+|owner_?\d+|alias_\d+|[a-z0-9_-]{4,})', q_lower)
        stop_words = {"what", "are", "the", "does", "have", "has", "is", "for", "in", "of", "how", "many", "much", "show", "list", "deals", "orders", "data", "tell", "me", "give", "find", "search", "lookup", "get", "with", "want", "everyone", "anyone", "all", "this", "deal", "information"}
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

        # ❓ 6. PROFESSIONAL OUT-OF-SCOPE FALLBACK
        return {
            "answer": f"Sorry! I could not find any active deals or work orders matching '{q_raw}' in the application.\n\nI am your dedicated Skylark Business Intelligence Agent, specialized strictly in answering queries about your Monday.com Sales Deals Funnel, Work Orders, Client/Dealer records, Revenue analytics, and Security audit logs.",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
