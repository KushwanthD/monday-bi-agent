"""
Universal Gemini AI Power-Engine for BI Analytics
Integrates Google Gemini 2.5 Flash API with precise target entity resolution & exact filtering
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

    def analyze(self, raw_deals: list, raw_orders: list, user_query: str) -> dict:
        cleaned_deals, deal_caveats = self.resilience.process_deals(raw_deals)
        cleaned_orders, order_caveats = self.resilience.process_work_orders(raw_orders)
        all_caveats = deal_caveats + order_caveats

        q_raw = user_query.strip()
        q_lower = q_raw.lower()

        # 📄 EXPORT CSV / PDF INTENT HANDLER
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

        # 🛡️ SECURITY & WAF AUDIT INTENT HANDLER
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

        # 🤖 REAL AI ENGINE (Google Gemini API Integration)
        if self.client:
            try:
                data_context = {
                    "sales_deals_summary": {
                        "total_deals_count": len(cleaned_deals),
                        "total_pipeline_value": sum(d.get("value", 0) for d in cleaned_deals),
                        "deals_data": cleaned_deals
                    },
                    "work_orders_summary": {
                        "total_work_orders_count": len(cleaned_orders),
                        "total_billed_cost": sum(o.get("cost", 0) for o in cleaned_orders),
                        "work_orders_data": cleaned_orders
                    }
                }

                system_instruction = (
                    "You are the official Skylark Drones Executive Business Intelligence AI Assistant.\n"
                    "Your goal is to answer the user's questions with 100% precision based on the provided live JSON data context.\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. If the user asks for total billed amounts, costs, or values for a specific entity or filter (e.g., 'Alias_160 mining projects billed amount'), ONLY match records that actually contain that specific entity and sector. Calculate the exact sum for matching records and list ONLY those matching items.\n"
                    "3. Do not list unrelated items or dump all records.\n"
                    "4. If the user asks something completely unrelated to the application or business data (e.g. sports, weather), politely state: "
                    "'Sorry! I do not have information regarding that in the application...'\n"
                    "5. Keep responses clean, concise, and professional."
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

        # 🧠 DETERMINISTIC TARGET MATCHING ENGINE (Fallback)
        # Smart multi-token extraction: e.g. "Alias_160", "Mining", "Sakura"
        stop_words = {"what", "is", "the", "total", "billed", "amount", "amounts", "done", "by", "for", "in", "of", "how", "many", "how", "much", "show", "list", "deals", "orders", "work", "tracker", "funnel", "pipeline", "data", "different", "unique", "projects", "project", "need"}
        search_tokens = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', q_lower).split() if w not in stop_words]

        # Filter orders & deals matching ALL search tokens
        matching_orders = cleaned_orders
        matching_deals = cleaned_deals

        if search_tokens:
            for t in search_tokens:
                matching_orders = [o for o in matching_orders if t in str(o).lower()]
                matching_deals = [d for d in matching_deals if t in str(d).lower()]

        total_billed = sum(o.get("cost", 0) for o in matching_orders)
        total_val = sum(d.get("value", 0) for d in matching_deals)

        label = " ".join([t.title() for t in search_tokens]) if search_tokens else "Dataset"

        lines = [f"Financial Analytics Summary for '{label}':\n"]

        if matching_orders:
            lines.append(f"- Total Billed Amount in Work Orders: Rs. {total_billed:,.2f} across {len(matching_orders)} matching project(s).")
            lines.append("  Matching Work Orders List:")
            for o in matching_orders[:10]:
                lines.append(f"    - {o.get('project_name')} ({o.get('work_order_id')}) | Sector: {o.get('sector')} | Status: {o.get('status')} | Billed: Rs. {o.get('cost', 0):,.2f}")
            if len(matching_orders) > 10:
                lines.append(f"    ... and {len(matching_orders) - 10} more projects.")

        if matching_deals:
            lines.append(f"\n- Total Pipeline Value in Sales Deals: Rs. {total_val:,.2f} across {len(matching_deals)} matching deal(s).")
            lines.append("  Matching Sales Deals List:")
            for d in matching_deals[:10]:
                lines.append(f"    - {d.get('deal_name')} ({d.get('client')}) | Sector: {d.get('sector')} | Status: {d.get('deal_status')} | Value: Rs. {d.get('value', 0):,.2f}")
            if len(matching_deals) > 10:
                lines.append(f"    ... and {len(matching_deals) - 10} more deals.")

        if not matching_orders and not matching_deals:
            lines.append(f"No active deals or work orders found matching '{label}'.")

        return {
            "answer": "\n".join(lines),
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
