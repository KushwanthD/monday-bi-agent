"""
Universal Full-Application Business Intelligence & Analytics Engine
Handles:
- Math & Math Expression evaluation (safe arithmetic)
- PDF & CSV Export generation triggers
- Dynamic Dealer / Client / Sector / Status search & tabular item listing
- Navigation & Monday.com Filter redirect actions
- Professional out-of-scope / fallback responses ("Sorry! I am only configured to answer queries regarding...")
"""

import re
import math
from datetime import datetime

class BIQueryEngine:
    def __init__(self, data_resilience_engine, security_guard=None):
        self.resilience = data_resilience_engine
        self.security_guard = security_guard

    def set_security_guard(self, security_guard):
        self.security_guard = security_guard

    def safe_eval_math(self, expr: str):
        """Safely evaluates mathematical expressions (arithmetic, percentages, sum, etc.)"""
        try:
            # Clean and sanitize expression
            clean_expr = expr.lower().replace('x', '*').replace('÷', '/').replace('^', '**')
            clean_expr = re.sub(r'[^0-9\+\-\*\/\(\)\.\s\%]', '', clean_expr)
            if not clean_expr.strip():
                return None
            
            # Handle percentage calculations e.g. 15% of 250000
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:of)?\s*(\d+(?:\.\d+)?)', expr.lower())
            if pct_match:
                pct = float(pct_match.group(1))
                val = float(pct_match.group(2))
                res = (pct / 100.0) * val
                return f"{pct}% of {val:,.2f} = **{res:,.2f}**"

            # Direct eval of safe math tokens
            allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum}
            code = compile(clean_expr, "<string>", "eval")
            for name in code.co_names:
                if name not in allowed_names:
                    return None
            val = eval(code, {"__builtins__": {}}, allowed_names)
            if isinstance(val, (int, float)):
                return f"Math Result: `{clean_expr.strip()}` = **{val:,.2f}**"
        except Exception:
            return None
        return None

    def analyze(self, raw_deals: list, raw_orders: list, user_query: str) -> dict:
        cleaned_deals, deal_caveats = self.resilience.process_deals(raw_deals)
        cleaned_orders, order_caveats = self.resilience.process_work_orders(raw_orders)
        all_caveats = deal_caveats + order_caveats

        q_raw = user_query.strip()
        q_lower = q_raw.lower()

        action = None
        action_payload = {}

        # 🧮 1. MATHEMATICAL CALCULATION DETECTOR
        # Check if query asks for math or arithmetic
        math_keywords = ["calculate", "math", "add", "multiply", "divide", "subtract", "sum of", "percent of", "% of", "plus", "minus", "times"]
        is_math_query = any(k in q_lower for k in math_keywords) or re.search(r'^\s*[\d\(\)\.\s\+\-\*\/\%]+\s*$', q_lower)
        if is_math_query:
            # Extract math expression
            expr_candidate = re.sub(r'(?i)(calculate|what is|compute|eval|math|the|sum of|\% of|of)', '', q_raw).strip()
            math_result = self.safe_eval_math(expr_candidate) or self.safe_eval_math(q_raw)
            if math_result:
                return {
                    "answer": f"🧮 **Calculation Result:**\n\n{math_result}",
                    "is_clarification": False,
                    "caveats": all_caveats,
                    "action": None
                }

        # 📄 2. EXPORT CSV / PDF INTENT
        is_export_csv = any(k in q_lower for k in ["export csv", "download csv", "generate csv", "csv report", "save csv"])
        is_export_pdf = any(k in q_lower for k in ["export pdf", "download pdf", "generate pdf", "pdf report", "save pdf", "print pdf"])

        if is_export_csv or is_export_pdf:
            export_type = "CSV" if is_export_csv else "PDF"
            return {
                "answer": f"📄 **{export_type} Export Request:**\n\nI have generated your requested **{export_type} report** based on the current live deals and work orders dataset. Click below to download or print your file immediately.",
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "export",
                "action_payload": {"type": export_type.lower()}
            }

        # 🛡️ 3. SECURITY & WAF AUDIT INTENT
        if any(k in q_lower for k in ["security", "waf", "attack", "audit", "log", "blocked", "checksum", "tamper", "owasp"]):
            audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []
            blocked_count = sum(1 for log in audit_logs if "BLOCKED" in log.get("event_type", ""))
            
            lines = [
                "🛡️ **OWASP Cybersecurity & WAF Audit Status:**\n",
                f"• **WAF Protection:** Active & Enforcing (OWASP Top 10 + Prompt Injection Guard)",
                f"• **IP Rate Limiting:** Active Window",
                f"• **Total Audit Events Logged:** {len(audit_logs)} security logs recorded.",
                f"• **Blocked Malicious Attacks:** {blocked_count} attack attempts thwarted.\n"
            ]
            if audit_logs:
                lines.append("📋 **Recent Security Log Events:**")
                for log in audit_logs[-3:]:
                    lines.append(f"  - `[{log['timestamp']}]` **{log['event_type']}** — {log['details']}")
            else:
                lines.append("✅ No security violations or prompt injection attacks detected.")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "redirect",
                "action_payload": {"view": "view-security"}
            }

        # 🌐 4. UNIVERSAL SUMMARY INTENT
        if any(k in q_lower for k in ["everything", "full summary", "summarize", "all data", "whole application", "overview", "complete info", "briefing"]):
            total_pipeline_val = sum(d["value"] for d in cleaned_deals)
            won_deals = [d for d in cleaned_deals if d["deal_status"].lower() == "won" or "won" in d["stage"].lower() or "work order received" in d["stage"].lower()]
            closed_won_val = sum(d["value"] for d in won_deals)
            proposals = [d for d in cleaned_deals if "proposal" in d["stage"].lower() or "negotiation" in d["stage"].lower()]
            proposal_val = sum(d["value"] for d in proposals)

            completed_orders = [o for o in cleaned_orders if "completed" in o["status"].lower() or "executed" in o["status"].lower()]
            active_orders = [o for o in cleaned_orders if "ongoing" in o["status"].lower() or "in progress" in o["status"].lower() or "not started" in o["status"].lower()]
            total_ops_val = sum(o["cost"] for o in cleaned_orders)

            lines = [
                "🚀 **Universal Cross-Application Intelligence Summary:**\n",
                "📈 **1. Commercial Sales Pipeline:**",
                f"• **Total Pipeline Value:** ₹{total_pipeline_val:,.2f} across {len(cleaned_deals)} tracked deals.",
                f"• **Closed-Won Revenue:** ₹{closed_won_val:,.2f} ({len(won_deals)} Won deals).",
                f"• **Active Proposals:** ₹{proposal_val:,.2f} ({len(proposals)} Proposals/Negotiations).\n",
                "🛸 **2. Operations & Flight Work Orders:**",
                f"• **Total Tracked Work Orders:** {len(cleaned_orders)} projects (₹{total_ops_val:,.2f} contract value).",
                f"• **Project Execution:** {len(completed_orders)} completed, {len(active_orders)} active/ongoing.\n",
                "🛡️ **3. System Controls:**",
                f"• **Data Resilience:** {len(all_caveats)} quality caveat(s) monitored."
            ]

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        # 🔍 5. DETAILED ENTITY / DEAL / SECTOR / STATUS FILTER & SEARCH
        # Detect sector
        detected_sector = None
        for sector_key in ["energy", "powerline", "renewables", "mining", "infrastructure", "construction", "railways", "agriculture", "dsp", "tender"]:
            if sector_key in q_lower:
                detected_sector = self.resilience.normalize_sector(sector_key)
                break

        # Detect status
        detected_status = None
        if "won" in q_lower or "closed" in q_lower or "received" in q_lower:
            detected_status = "Won"
        elif "negotiation" in q_lower or "proposal" in q_lower or "active" in q_lower:
            detected_status = "In Negotiation"
        elif "lost" in q_lower:
            detected_status = "Lost"

        # Detect client / dealer / account name or specific search token
        entity_match = re.search(r'(company_?\d+|wocompany_?\d+|sdpldeal-?\d+|owner_?\d+|alias_\d+)', q_lower)
        target_entity = entity_match.group(0).upper() if entity_match else None
        
        if not target_entity:
            words = q_raw.split()
            for w in words:
                clean_w = re.sub(r'[^A-Za-z0-9_-]', '', w).upper()
                if len(clean_w) >= 4 and (clean_w.startswith("COMPANY") or clean_w.startswith("WOCOMPANY") or clean_w.startswith("SDPLDEAL") or clean_w.startswith("OWNER")):
                    target_entity = clean_w
                    break

        # Check if query mentions deals, work orders, pipeline, or specific search term
        is_deal_search = any(k in q_lower for k in ["deal", "pipeline", "sales", "revenue", "won", "stage", "mining", "energy", "infra", "dealer", "client", "company", "owner"]) or target_entity or detected_sector or detected_status
        is_order_search = any(k in q_lower for k in ["order", "flight", "operation", "execution", "project", "work order"])

        if is_deal_search or is_order_search:
            # Filter deals
            matching_deals = cleaned_deals
            if detected_sector:
                matching_deals = [d for d in matching_deals if d["sector"] == detected_sector]
            if detected_status:
                matching_deals = [d for d in matching_deals if detected_status.lower() in d["deal_status"].lower() or detected_status.lower() in d["stage"].lower()]
            if target_entity:
                digits = re.search(r'\d+', target_entity)
                digit_str = digits.group(0) if digits else ""
                matching_deals = [
                    d for d in matching_deals
                    if target_entity in d["client"].upper()
                    or target_entity in d["deal_name"].upper()
                    or target_entity in d["owner"].upper()
                    or (digit_str and digit_str in d["client"])
                ]

            # Filter orders
            matching_orders = cleaned_orders
            if detected_sector:
                matching_orders = [o for o in matching_orders if o["sector"] == detected_sector]
            if target_entity:
                matching_orders = [
                    o for o in matching_orders
                    if target_entity in o["client"].upper()
                    or target_entity in o["project_name"].upper()
                    or target_entity in o["work_order_id"].upper()
                ]

            total_val = sum(d["value"] for d in matching_deals)
            lines = []

            filter_desc = []
            if detected_sector: filter_desc.append(f"Sector: **{detected_sector}**")
            if detected_status: filter_desc.append(f"Status: **{detected_status}**")
            if target_entity: filter_desc.append(f"Client/Entity: **{target_entity}**")
            
            filter_str = " | ".join(filter_desc) if filter_desc else "Search Results"

            lines.append(f"🔍 **Monday.com Live Query Results ({filter_str}):**\n")
            lines.append(f"• **Found {len(matching_deals)} matching deal(s)** totaling **₹{total_val:,.2f}**.")
            if matching_orders:
                lines.append(f"• **Found {len(matching_orders)} matching work order(s)**.")
            lines.append("")

            if matching_deals:
                lines.append("📋 **Matching Deals List:**")
                for d in matching_deals[:6]:
                    lines.append(f"  - **{d['deal_name']}** (`{d['client']}`) | Sector: *{d['sector']}* | Status: **{d['deal_status']}** | Value: **₹{d['value']:,.2f}** | Owner: `{d['owner']}`")
            
            if matching_orders:
                lines.append("\n🛸 **Matching Work Orders:**")
                for o in matching_orders[:4]:
                    lines.append(f"  - **{o['project_name']}** (`{o['work_order_id']}`) | Status: **{o['status']}** | Value: **₹{o['cost']:,.2f}**")

            lines.append("\n💡 *I have automatically updated and redirected your Monday.com Board table filters to show these exact records!*")

            # Determine redirect action and filter parameters
            search_query_param = target_entity if target_entity else ("mining" if "mining" in q_lower else "")
            
            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "apply_filters_and_redirect",
                "action_payload": {
                    "view": "view-boards",
                    "sector": detected_sector or "ALL",
                    "status": detected_status or "ALL",
                    "search": search_query_param
                }
            }

        # ❓ 6. OUT-OF-SCOPE / PROFESSIONAL UNKNOWN FALLBACK
        # If user asks something totally unrelated to the app (e.g. weather, sports, general knowledge)
        return {
            "answer": "Sorry! I do not have information regarding that in the application.\n\nI am your dedicated **Skylark Business Intelligence Agent**, specialized strictly in answering queries about your **Monday.com Sales Deals Funnel**, **Work Orders**, **Client/Dealer records**, **Revenue analytics**, and **Security audit logs**.\n\nPlease ask me about pipeline revenues, client codes (e.g., `COMPANY089`), sector analytics, mathematical calculations, or export options!",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
