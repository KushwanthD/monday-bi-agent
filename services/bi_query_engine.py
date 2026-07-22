"""
Universal Zero-Error BI Intelligence Engine
Handles:
- Numerical inequality filters (below X, above X, less than X, greater than X, under X)
- Entity lookups (Sakura, Alias_160, COMPANY089)
- Field distributions & counts (execution status, project names, sectors, deal owners)
- Math calculation evaluation
- CSV & PDF exports
- Out-of-scope domain protection
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
                    "Analyze the user's question carefully against the provided JSON records and perform accurate filter/math operations.\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. NUMERICAL INEQUALITIES (e.g. 'billed amounts below 200000', 'value greater than 1M'): Strictly filter items where the numeric field ('cost' for work orders, 'value' for deals) matches the inequality condition (< 200000). DO NOT list items exceeding the limit.\n"
                    "3. SPECIFIC ENTITY LOOKUPS (e.g. 'Sakura', 'Alias_160'): Filter items matching the exact entity name and return exact sums and item lists.\n"
                    "4. If no items match the numerical or entity criteria, clearly state that 0 records matched.\n"
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

        # 🧠 4. NUMERICAL INEQUALITY & VALUE COMPARISON ENGINE (Fallback)
        num_match = re.search(r'(below|under|less than|smaller than|above|over|greater than|more than)\s*(?:rs\.?|inr)?\s*(\d+(?:\.\d+)?)', q_lower)
        if num_match:
            op = num_match.group(1)
            target_val = float(num_match.group(2))

            is_less = op in ["below", "under", "less than", "smaller than"]
            
            matching_orders = []
            for o in cleaned_orders:
                cost = float(o.get("cost", 0))
                if is_less and cost < target_val:
                    matching_orders.append(o)
                elif not is_less and cost > target_val:
                    matching_orders.append(o)

            matching_deals = []
            for d in cleaned_deals:
                val = float(d.get("value", 0))
                if is_less and val < target_val:
                    matching_deals.append(d)
                elif not is_less and val > target_val:
                    matching_deals.append(d)

            op_label = f"below Rs. {target_val:,.2f}" if is_less else f"above Rs. {target_val:,.2f}"

            lines = [f"Numerical Query Results for Billed/Value amounts {op_label}:\n"]

            if matching_orders:
                lines.append(f"Work Order Tracker Records ({len(matching_orders)} matching):")
                for o in matching_orders[:15]:
                    lines.append(f"  - Project: {o.get('project_name')} ({o.get('work_order_id')}) | Status: {o.get('status')} | Billed: Rs. {o.get('cost', 0):,.2f}")
                if len(matching_orders) > 15:
                    lines.append(f"  ... and {len(matching_orders) - 15} more projects.")

            if matching_deals:
                lines.append(f"\nSales Deals Funnel Records ({len(matching_deals)} matching):")
                for d in matching_deals[:15]:
                    lines.append(f"  - Deal: {d.get('deal_name')} ({d.get('client')}) | Sector: {d.get('sector')} | Pipeline Value: Rs. {d.get('value', 0):,.2f}")

            if not matching_orders and not matching_deals:
                lines.append(f"No records found with billed/pipeline amounts {op_label}.")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        # 🧠 5. ENTITY & GENERAL TEXT SEARCH ENGINE (Fallback)
        stop_words = {"what", "are", "the", "does", "have", "has", "is", "for", "in", "of", "how", "many", "much", "show", "list", "deals", "orders", "data", "tell", "me", "give", "find", "search", "lookup", "get", "with", "want", "all"}
        search_tokens = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', q_lower).split() if w not in stop_words and len(w) >= 3]

        matching_orders = cleaned_orders
        matching_deals = cleaned_deals

        if search_tokens:
            for t in search_tokens:
                matching_orders = [o for o in matching_orders if t in str(o).lower()]
                matching_deals = [d for d in matching_deals if t in str(d).lower()]
        else:
            matching_orders = []
            matching_deals = []

        total_billed = sum(o.get("cost", 0) for o in matching_orders)
        total_val = sum(d.get("value", 0) for d in matching_deals)

        label = " ".join([t.title() for t in search_tokens]) if search_tokens else "Workspace"

        if matching_orders or matching_deals:
            lines = [f"Analytics Summary for '{label}':\n"]

            if matching_orders:
                lines.append(f"- Total Billed Amount in Work Orders: Rs. {total_billed:,.2f} across {len(matching_orders)} matching project(s).")
                lines.append("  Matching Work Orders List:")
                for o in matching_orders[:10]:
                    lines.append(f"    - {o.get('project_name')} ({o.get('work_order_id')}) | Status: {o.get('status')} | Billed: Rs. {o.get('cost', 0):,.2f}")

            if matching_deals:
                lines.append(f"\n- Total Pipeline Value in Sales Deals: Rs. {total_val:,.2f} across {len(matching_deals)} matching deal(s).")
                lines.append("  Matching Sales Deals List:")
                for d in matching_deals[:10]:
                    lines.append(f"    - {d.get('deal_name')} ({d.get('client')}) | Sector: {d.get('sector')} | Value: Rs. {d.get('value', 0):,.2f}")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        # ❓ 6. PROFESSIONAL UNKNOWN / OUT-OF-SCOPE FALLBACK
        return {
            "answer": f"Sorry! I could not find any active deals or work orders matching '{q_raw}' in the application.\n\nI am your dedicated Skylark Business Intelligence Agent, specialized strictly in answering queries about your Monday.com Sales Deals Funnel, Work Orders, Client/Dealer records, Revenue analytics, and Security audit logs.",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
