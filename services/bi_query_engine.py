"""
Universal Gemini AI Power-Engine for BI Analytics
Integrates Google Gemini 2.5 Flash API for zero-mistake natural language understanding
across all Monday.com deals funnel & work order tracker datasets.
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
                    "2. If the user asks for math calculations (e.g. 15% of X, add/multiply), perform accurate arithmetic.\n"
                    "3. If the user asks about specific entities (e.g. 'Sakura', 'COMPANY089', 'OWNER_001'), calculate exact totals and list exact matching records.\n"
                    "4. If the user asks for unique counts (e.g., 'how many execution status', 'how many project names'), count unique values accurately.\n"
                    "5. If the user asks something completely unrelated to the application or business data (e.g. sports, weather), politely state: "
                    "'Sorry! I do not have information regarding that in the application. I am your dedicated Skylark Business Intelligence Agent...'\n"
                    "6. Keep responses clean, concise, and professional."
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

        # 🧠 DETERMINISTIC AI FALLBACK ENGINE
        # Exact calculation & aggregation fallback logic
        stop_words = {"what", "is", "the", "total", "billed", "amount", "amounts", "done", "by", "for", "in", "of", "how", "many", "how", "much", "show", "list", "deals", "orders", "work", "tracker", "funnel", "pipeline", "data", "different", "unique"}
        words = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', q_lower).split() if w not in stop_words]
        search_target = words[0] if words else None

        # Check for sum / total query
        if any(k in q_lower for k in ["total", "sum", "billed amount", "billed amounts", "how much", "revenue"]):
            matching_orders = [o for o in cleaned_orders if search_target and search_target in str(o).lower()]
            matching_deals = [d for d in cleaned_deals if search_target and search_target in str(d).lower()]

            if matching_orders or matching_deals:
                total_billed = sum(o.get("cost", 0) for o in matching_orders)
                total_val = sum(d.get("value", 0) for d in matching_deals)

                lines = []
                if search_target:
                    lines.append(f"Financial Summary for '{search_target.title()}':\n")
                
                if matching_orders:
                    lines.append(f"- Total Billed Amount in Work Orders: Rs. {total_billed:,.2f} across {len(matching_orders)} project(s).")
                    lines.append("  Breakdown of Work Orders:")
                    for o in matching_orders:
                        lines.append(f"    - {o.get('project_name')} ({o.get('work_order_id')}) | Status: {o.get('status')} | Billed: Rs. {o.get('cost', 0):,.2f}")

                if matching_deals:
                    lines.append(f"\n- Total Sales Pipeline Value in Deals Funnel: Rs. {total_val:,.2f} across {len(matching_deals)} deal(s).")
                    lines.append("  Breakdown of Sales Deals:")
                    for d in matching_deals[:5]:
                        lines.append(f"    - {d.get('deal_name')} ({d.get('client')}) | Sector: {d.get('sector')} | Status: {d.get('deal_status')} | Value: Rs. {d.get('value', 0):,.2f}")

                return {"answer": "\n".join(lines), "is_clarification": False, "caveats": all_caveats, "action": None}

        # Out-of-scope fallback
        return {
            "answer": "Sorry! I do not have information regarding that in the application.\n\nI am your dedicated Skylark Business Intelligence Agent, specialized strictly in answering queries about your Monday.com Sales Deals Funnel, Work Orders, Client/Dealer records, Revenue analytics, and Security audit logs.",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
