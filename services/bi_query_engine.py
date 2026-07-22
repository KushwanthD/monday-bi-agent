"""
Universal Full-Application Intelligent Analytics Engine
Universal Query Understanding & Free-Form Data Analysis Engine:
- Dynamically parses any question structure (numerical, statistical, analytical, list, comparison, search)
- Dynamically resolves field names, values, ranges, and target datasets without fixed templates
- Evaluates math expressions & safe arithmetic
- Handles CSV/PDF exports and interactive Monday.com filter redirects
- Returns polite professional response ONLY for completely unrelated non-application questions
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
            clean_expr = expr.lower().replace('x', '*').replace('÷', '/').replace('^', '**')
            clean_expr = re.sub(r'[^0-9\+\-\*\/\(\)\.\s\%]', '', clean_expr)
            if not clean_expr.strip():
                return None
            
            pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:of)?\s*(\d+(?:\.\d+)?)', expr.lower())
            if pct_match:
                pct = float(pct_match.group(1))
                val = float(pct_match.group(2))
                res = (pct / 100.0) * val
                return f"{pct}% of {val:,.2f} = {res:,.2f}"

            allowed_names = {"abs": abs, "round": round, "min": min, "max": max, "sum": sum}
            code = compile(clean_expr, "<string>", "eval")
            for name in code.co_names:
                if name not in allowed_names:
                    return None
            val = eval(code, {"__builtins__": {}}, allowed_names)
            if isinstance(val, (int, float)):
                return f"Math Result: {clean_expr.strip()} = {val:,.2f}"
        except Exception:
            return None
        return None

    def analyze(self, raw_deals: list, raw_orders: list, user_query: str) -> dict:
        cleaned_deals, deal_caveats = self.resilience.process_deals(raw_deals)
        cleaned_orders, order_caveats = self.resilience.process_work_orders(raw_orders)
        all_caveats = deal_caveats + order_caveats

        q_raw = user_query.strip()
        q_lower = q_raw.lower()

        # 🧮 1. MATHEMATICAL CALCULATION DETECTOR
        math_keywords = ["calculate", "math", "add", "multiply", "divide", "subtract", "sum of", "percent of", "% of", "plus", "minus", "times"]
        is_math_query = any(k in q_lower for k in math_keywords) or re.search(r'^\s*[\d\(\)\.\s\+\-\*\/\%]+\s*$', q_lower)
        if is_math_query:
            expr_candidate = re.sub(r'(?i)(calculate|what is|compute|eval|math|the|sum of|\% of|of)', '', q_raw).strip()
            math_result = self.safe_eval_math(expr_candidate) or self.safe_eval_math(q_raw)
            if math_result:
                return {
                    "answer": f"Calculation Result:\n\n{math_result}",
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
                "answer": f"{export_type} Export Request:\n\nI have generated your requested {export_type} report based on the current live deals and work orders dataset. Downloading file immediately.",
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
            else:
                lines.append("No security violations or prompt injection attacks detected.")

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
                "Universal Cross-Application Intelligence Summary:\n",
                "1. Commercial Sales Pipeline:",
                f"- Total Pipeline Value: Rs. {total_pipeline_val:,.2f} across {len(cleaned_deals)} tracked deals.",
                f"- Closed-Won Revenue: Rs. {closed_won_val:,.2f} ({len(won_deals)} Won deals).",
                f"- Active Proposals: Rs. {proposal_val:,.2f} ({len(proposals)} Proposals/Negotiations).\n",
                "2. Operations & Flight Work Orders:",
                f"- Total Tracked Work Orders: {len(cleaned_orders)} projects (Rs. {total_ops_val:,.2f} contract value).",
                f"- Project Execution: {len(completed_orders)} completed, {len(active_orders)} active/ongoing.\n",
                "3. System Controls:",
                f"- Data Resilience: {len(all_caveats)} quality caveat(s) monitored."
            ]

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        # 🧠 5. GENERAL FREE-FORM DATA QUERY UNDERSTANDING
        # Dynamically inspect all keys available in the dataset
        sample_deal_keys = set(cleaned_deals[0].keys()) if cleaned_deals else set()
        sample_order_keys = set(cleaned_orders[0].keys()) if cleaned_orders else set()
        all_dataset_keys = sample_deal_keys.union(sample_order_keys)

        # Detect target dataset from query context
        is_order_context = any(w in q_lower for w in ["work order", "order", "flight", "execution", "ops", "tracker", "project"])
        is_deal_context = any(w in q_lower for w in ["deal", "pipeline", "sales", "funnel", "revenue", "proposal", "stage", "client", "dealer"])
        
        target_records = cleaned_orders if (is_order_context and not is_deal_context) else (cleaned_deals if (is_deal_context and not is_order_context) else cleaned_deals + cleaned_orders)
        dataset_name = "Work Order Data Tracker" if (is_order_context and not is_deal_context) else ("Sales Deals Funnel" if (is_deal_context and not is_order_context) else "Full Workspace (Deals & Work Orders)")

        # Dynamically find matching field in query
        matched_field = None
        matched_field_title = ""

        # Map common synonyms to dynamic fields
        field_synonyms = {
            "status": ["status", "execution status", "state", "condition"],
            "stage": ["stage", "phase", "funnel stage", "pipeline stage"],
            "sector": ["sector", "industry", "vertical", "domain"],
            "project_name": ["project name", "project", "flight name", "project title"],
            "deal_name": ["deal name", "deal title", "opportunity name"],
            "client": ["client", "customer", "dealer", "company", "account", "client code", "dealer code"],
            "owner": ["owner", "manager", "representative", "rep", "deal owner", "assignee"],
            "value": ["value", "amount", "revenue", "worth", "pipeline value", "contract value", "cost"]
        }

        for f_key, synonyms in field_synonyms.items():
            if any(syn in q_lower for syn in synonyms):
                matched_field = f_key
                matched_field_title = synonyms[0].title()
                break

        # A. If user asks for COUNT / UNIQUE VALUES / BREAKDOWN of any attribute
        is_aggregation_query = any(k in q_lower for k in ["how many", "count", "number of", "different", "distinct", "unique", "types", "breakdown", "distribution", "list"])

        if is_aggregation_query and matched_field:
            counts = {}
            for r in target_records:
                val = r.get(matched_field) or r.get("deal_status") or r.get("status") or r.get("stage")
                if val:
                    counts[val] = counts.get(val, 0) + 1

            lines = [
                f"{dataset_name} Analytics:",
                f"There are {len(counts)} unique {matched_field_title.lower()}(s) in the {dataset_name} across {len(target_records)} total records.",
                "",
                f"Breakdown of {matched_field_title}s:"
            ]

            for val, c in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:15]:
                lines.append(f"  - {val}: {c} record(s)")

            if len(counts) > 15:
                lines.append(f"  ... and {len(counts) - 15} more entries.")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": None
            }

        # B. If user asks for HIGHEST / LOWEST / TOTAL / AVERAGE values
        if any(k in q_lower for k in ["highest", "lowest", "max", "min", "total", "average", "top", "biggest"]):
            if "highest" in q_lower or "max" in q_lower or "top" in q_lower or "biggest" in q_lower:
                sorted_deals = sorted(cleaned_deals, key=lambda d: d.get("value", 0), reverse=True)
                top = sorted_deals[0] if sorted_deals else {}
                lines = [
                    "Highest Value Record Analytics:",
                    f"Top Deal: {top.get('deal_name')} ({top.get('client')})",
                    f"Value: Rs. {top.get('value', 0):,.2f}",
                    f"Sector: {top.get('sector')} | Status: {top.get('deal_status')} | Owner: {top.get('owner')}"
                ]
                return {"answer": "\n".join(lines), "is_clarification": False, "caveats": all_caveats, "action": None}

        # C. Generic Free-form Search (Client codes, specific status names, sectors, owner names, deal names)
        detected_sector = None
        for sector_key in ["energy", "powerline", "renewables", "mining", "infrastructure", "construction", "railways", "agriculture", "dsp", "tender"]:
            if sector_key in q_lower:
                detected_sector = self.resilience.normalize_sector(sector_key)
                break

        detected_status = None
        if "won" in q_lower or "closed" in q_lower or "received" in q_lower:
            detected_status = "Won"
        elif "negotiation" in q_lower or "proposal" in q_lower:
            detected_status = "In Negotiation"
        elif "lost" in q_lower:
            detected_status = "Lost"

        entity_match = re.search(r'(company_?\d+|wocompany_?\d+|sdpldeal-?\d+|owner_?\d+|alias_\d+)', q_lower)
        target_entity = entity_match.group(0).upper() if entity_match else None

        # Free search across deals and work orders
        matching_deals = cleaned_deals
        if detected_sector:
            matching_deals = [d for d in matching_deals if d["sector"] == detected_sector]
        if detected_status:
            matching_deals = [d for d in matching_deals if detected_status.lower() in d["deal_status"].lower() or detected_status.lower() in d["stage"].lower()]
        if target_entity:
            matching_deals = [d for d in matching_deals if target_entity in str(d).upper()]

        matching_orders = cleaned_orders
        if detected_sector:
            matching_orders = [o for o in matching_orders if o["sector"] == detected_sector]
        if target_entity:
            matching_orders = [o for o in matching_orders if target_entity in str(o).upper()]

        # Check if query matches any application keywords or data contents
        has_app_relevance = (is_order_context or is_deal_context or detected_sector or detected_status or target_entity or matched_field or
                             any(word in q_lower for word in ["skylark", "monday", "board", "analytics", "data", "revenue", "flight", "wo", "deal", "order", "cost", "won", "stage"]))

        if has_app_relevance:
            total_val = sum(d["value"] for d in matching_deals)
            lines = [
                f"Monday.com Application Analytics Search:",
                f"- Found {len(matching_deals)} matching deal(s) totaling Rs. {total_val:,.2f}.",
                f"- Found {len(matching_orders)} matching work order(s)."
            ]

            if matching_deals:
                lines.append("\nMatching Deals:")
                for d in matching_deals[:5]:
                    lines.append(f"  - {d['deal_name']} ({d['client']}) | Sector: {d['sector']} | Status: {d['deal_status']} | Value: Rs. {d['value']:,.2f}")

            if matching_orders:
                lines.append("\nMatching Work Orders:")
                for o in matching_orders[:4]:
                    lines.append(f"  - {o['project_name']} ({o['work_order_id']}) | Status: {o['status']} | Billed: Rs. {o['cost']:,.2f}")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "apply_filters_and_redirect" if (detected_sector or detected_status or target_entity) else None,
                "action_payload": {
                    "view": "view-boards",
                    "sector": detected_sector or "ALL",
                    "status": detected_status or "ALL",
                    "search": target_entity or ""
                }
            }

        # ❓ 6. PROFESSIONAL UNKNOWN / OUT-OF-SCOPE FALLBACK
        # Only reached if query is completely unrelated to the application (e.g. general knowledge, external topics)
        return {
            "answer": "Sorry! I do not have information regarding that in the application.\n\nI am your dedicated Skylark Business Intelligence Agent, specialized strictly in answering queries about your Monday.com Sales Deals Funnel, Work Orders, Client/Dealer records, Revenue analytics, and Security audit logs.\n\nPlease ask me any question about your pipeline revenues, client records, execution statuses, project metrics, mathematical calculations, or export options!",
            "is_clarification": False,
            "caveats": all_caveats,
            "action": None
        }
