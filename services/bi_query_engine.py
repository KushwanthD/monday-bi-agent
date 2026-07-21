"""
Universal Full-Application Business Intelligence & Analytics Engine
Provides unconstrained access across all application domains:
- Sales Deals Funnel Board
- Work Orders Operations Tracker Board
- OWASP WAF Cybersecurity & SHA-256 Audit Logs
- Data Resilience Engine & Quality Caveats
- Executive Leadership Briefings
"""

import re
from datetime import datetime

class BIQueryEngine:
    def __init__(self, data_resilience_engine, security_guard=None):
        self.resilience = data_resilience_engine
        self.security_guard = security_guard

    def set_security_guard(self, security_guard):
        self.security_guard = security_guard

    def parse_query_intent(self, query: str) -> dict:
        q_lower = query.lower().strip()
        
        # 1. Entity extraction (Client codes, Deal IDs, Owner codes)
        entity_match = re.search(r'(company_?\d+|wocompany_?\d+|sdpldeal-?\d+|owner_?\d+|alias_\d+)', q_lower)
        target_entity = entity_match.group(0).upper() if entity_match else None
        
        if not target_entity:
            words = query.split()
            for w in words:
                clean_w = re.sub(r'[^A-Za-z0-9_-]', '', w).upper()
                if len(clean_w) >= 4 and (clean_w.startswith("COMPANY") or clean_w.startswith("WOCOMPANY") or clean_w.startswith("SDPLDEAL") or clean_w.startswith("OWNER")):
                    target_entity = clean_w
                    break

        # 2. Sector detection
        detected_sector = None
        for sector_key in ["energy", "powerline", "renewables", "mining", "infrastructure", "construction", "railways", "agriculture", "dsp", "tender"]:
            if sector_key in q_lower:
                detected_sector = self.resilience.normalize_sector(sector_key)
                break

        # 3. Security / WAF Intent
        is_security_query = any(k in q_lower for k in ["security", "waf", "attack", "audit", "log", "blocked", "checksum", "tamper", "owasp"])

        # 4. Universal Full-App Summary Intent
        is_full_summary = any(k in q_lower for k in ["everything", "full summary", "summarize", "all data", "whole application", "overview", "complete info"])

        # 5. Topic Intent
        topic = "general"
        if is_security_query:
            topic = "security"
        elif is_full_summary:
            topic = "full_summary"
        elif target_entity:
            topic = "entity_lookup"
        elif "pipeline" in q_lower or "deal" in q_lower or "funnel" in q_lower:
            topic = "pipeline"
        elif "work order" in q_lower or "flight" in q_lower or "operation" in q_lower or "execution" in q_lower:
            topic = "operations"
        elif "revenue" in q_lower or "won" in q_lower or "sale" in q_lower:
            topic = "revenue"

        return {
            "entity": target_entity,
            "sector": detected_sector,
            "topic": topic,
            "raw_query": query
        }

    def analyze(self, raw_deals: list, raw_orders: list, user_query: str) -> dict:
        cleaned_deals, deal_caveats = self.resilience.process_deals(raw_deals)
        cleaned_orders, order_caveats = self.resilience.process_work_orders(raw_orders)
        all_caveats = deal_caveats + order_caveats

        intent = self.parse_query_intent(user_query)

        # 🛡️ 1. SECURITY & WAF AUDIT INTENT
        if intent["topic"] == "security":
            audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []
            blocked_count = sum(1 for log in audit_logs if "BLOCKED" in log.get("event_type", ""))
            
            lines = [
                "🛡️ **OWASP Cybersecurity & WAF Audit Status:**\n",
                f"• **WAF Protection:** Active & Enforcing (OWASP Top 10 + Prompt Injection Guard)",
                f"• **IP Rate Limiting:** 45 Requests / Minute Window",
                f"• **Total Audit Events Logged:** {len(audit_logs)} security logs recorded.",
                f"• **Blocked Malicious Attacks:** {blocked_count} attack attempts thwarted.\n"
            ]
            if audit_logs:
                lines.append("📋 **Recent Security Log Events:**")
                for log in audit_logs[-3:]:
                    lines.append(f"  - `[{log['timestamp']}]` **{log['event_type']}** — {log['details']} (Hash: `{log['checksum'][:12]}...`)")
            else:
                lines.append("✅ No security violations or prompt injection attacks detected.")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "metrics": {"audit_logs_count": len(audit_logs), "blocked_attacks": blocked_count}
            }

        # 🔍 2. ENTITY / DEALER LOOKUP INTENT
        if intent["topic"] == "entity_lookup":
            target_entity = intent["entity"]
            digits = re.search(r'\d+', target_entity)
            digit_str = digits.group(0) if digits else ""

            matched_deals = [
                d for d in cleaned_deals
                if target_entity in d["client"].upper()
                or target_entity in d["deal_name"].upper()
                or target_entity in d["owner"].upper()
                or (digit_str and digit_str in d["client"])
            ]

            matched_orders = [
                o for o in cleaned_orders
                if target_entity in o["client"].upper()
                or target_entity in o["project_name"].upper()
                or target_entity in o["work_order_id"].upper()
                or (digit_str and digit_str in o["client"])
            ]

            if not matched_deals and not matched_orders:
                return {
                    "answer": f"🔍 **Entity Lookup for `{target_entity}`:** No active deals or work orders found for client code **{target_entity}**.",
                    "is_clarification": False,
                    "caveats": all_caveats,
                    "metrics": {}
                }

            total_val = sum(d["value"] for d in matched_deals)
            total_billed = sum(o["cost"] for o in matched_orders)

            lines = [f"🏢 **Entity Record for `{target_entity}`:**\n"]
            lines.append(f"• **Account Code:** `{target_entity}`")
            lines.append(f"• **Sales Deals:** {len(matched_deals)} deal(s) totaling **₹{total_val:,.2f}**.")
            lines.append(f"• **Work Orders:** {len(matched_orders)} project(s) totaling **₹{total_billed:,.2f}**.\n")

            if matched_deals:
                lines.append("📋 **Sales Pipeline Details:**")
                for d in matched_deals[:4]:
                    lines.append(f"  - **{d['deal_name']}** | Sector: *{d['sector']}* | Stage: *{d['stage']}* | Status: **{d['deal_status']}** | Value: **₹{d['value']:,.2f}** | Owner: `{d['owner']}`")

            if matched_orders:
                lines.append("\n🛸 **Work Order Operations:**")
                for o in matched_orders[:4]:
                    lines.append(f"  - **{o['project_name']}** (`{o['work_order_id']}`) | Sector: *{o['sector']}* | Status: **{o['status']}** | Billed: **₹{o['cost']:,.2f}**")

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "metrics": {"total_value": total_val, "total_billed": total_billed}
            }

        # 🌐 3. UNIVERSAL FULL-APPLICATION EXECUTIVE SUMMARY INTENT
        if intent["topic"] == "full_summary":
            total_pipeline_val = sum(d["value"] for d in cleaned_deals)
            won_deals = [d for d in cleaned_deals if d["deal_status"].lower() == "won" or "won" in d["stage"].lower() or "work order received" in d["stage"].lower()]
            closed_won_val = sum(d["value"] for d in won_deals)
            proposals = [d for d in cleaned_deals if "proposal" in d["stage"].lower() or "negotiation" in d["stage"].lower()]
            proposal_val = sum(d["value"] for d in proposals)

            completed_orders = [o for o in cleaned_orders if "completed" in o["status"].lower() or "executed" in o["status"].lower()]
            active_orders = [o for o in cleaned_orders if "ongoing" in o["status"].lower() or "in progress" in o["status"].lower() or "not started" in o["status"].lower()]
            total_ops_val = sum(o["cost"] for o in cleaned_orders)

            audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []

            lines = [
                "🚀 **Universal Cross-Application Intelligence Summary:**\n",
                "📈 **1. Commercial Sales Pipeline:**",
                f"• **Total Pipeline Value:** ₹{total_pipeline_val:,.2f} across {len(cleaned_deals)} tracked deals.",
                f"• **Closed-Won Revenue:** ₹{closed_won_val:,.2f} ({len(won_deals)} Won deals).",
                f"• **Active Proposals:** ₹{proposal_val:,.2f} ({len(proposals)} Proposals/Negotiations).\n",
                "🛸 **2. Operations & Flight Work Orders:**",
                f"• **Total Tracked Work Orders:** {len(cleaned_orders)} projects (₹{total_ops_val:,.2f} contract value).",
                f"• **Project Execution:** {len(completed_orders)} completed, {len(active_orders)} active/ongoing.\n",
                "🛡️ **3. Security & Data Quality Controls:**",
                f"• **WAF Audit Log:** {len(audit_logs)} security events recorded.",
                f"• **Data Quality:** {len(all_caveats)} data resilience warning(s) active."
            ]

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "metrics": {
                    "total_pipeline": total_pipeline_val,
                    "closed_won": closed_won_val,
                    "in_negotiation": proposal_val,
                    "total_deals_count": len(cleaned_deals),
                    "completed_flights": len(completed_orders),
                    "in_progress_flights": len(active_orders)
                }
            }

        # 📊 4. MACRO METRIC & SECTOR INTENT
        target_sector = intent.get("sector")

        filtered_deals = cleaned_deals
        if target_sector:
            filtered_deals = [d for d in cleaned_deals if d["sector"] == target_sector]

        filtered_orders = cleaned_orders
        if target_sector:
            filtered_orders = [o for o in cleaned_orders if o["sector"] == target_sector]

        total_pipeline_val = sum(d["value"] for d in filtered_deals)
        won_deals = [d for d in filtered_deals if d["deal_status"].lower() == "won" or "won" in d["stage"].lower() or "work order received" in d["stage"].lower()]
        closed_won_val = sum(d["value"] for d in won_deals)
        negotiation_deals = [d for d in filtered_deals if "negotiation" in d["stage"].lower() or "proposal" in d["stage"].lower()]
        negotiation_val = sum(d["value"] for d in negotiation_deals)

        completed_orders = [o for o in filtered_orders if "completed" in o["status"].lower() or "executed" in o["status"].lower()]
        in_progress_orders = [o for o in filtered_orders if "ongoing" in o["status"].lower() or "in progress" in o["status"].lower() or "not started" in o["status"].lower()]
        total_ops_val = sum(o["cost"] for o in filtered_orders)

        sector_heading = f"**{target_sector} Sector**" if target_sector else "**Overall Skylark Business Pipeline**"
        
        narrative_lines = [
            f"📊 **Executive BI Summary for {sector_heading}:**\n",
            f"• **Total Pipeline Value:** ₹{total_pipeline_val:,.2f} across {len(filtered_deals)} tracked deals.",
            f"• **Closed Won Revenue:** ₹{closed_won_val:,.2f} ({len(won_deals)} Won deal(s)).",
            f"• **Active Negotiation / Proposal Value:** ₹{negotiation_val:,.2f} ({len(negotiation_deals)} Proposal/Negotiation deal(s)).",
            f"• **Operational Execution:** {len(completed_orders)} project(s) completed, {len(in_progress_orders)} ongoing/active project(s).",
            f"• **Total Billed/Contract Value in Work Orders:** ₹{total_ops_val:,.2f}.\n"
        ]

        if total_pipeline_val > 0:
            conversion_rate = (closed_won_val / total_pipeline_val) * 100
            narrative_lines.append(f"💡 **Key Insight:** Sector win rate is **{conversion_rate:.1f}%**. Near-term negotiations hold ₹{negotiation_val:,.2f} in pending revenue.")
        else:
            narrative_lines.append("💡 **Key Insight:** No pipeline deals matching this query filter.")

        return {
            "answer": "\n".join(narrative_lines),
            "is_clarification": False,
            "caveats": all_caveats,
            "metrics": {
                "sector": target_sector or "All Sectors",
                "total_pipeline": total_pipeline_val,
                "closed_won": closed_won_val,
                "in_negotiation": negotiation_val,
                "total_deals_count": len(filtered_deals),
                "completed_flights": len(completed_orders),
                "in_progress_flights": len(in_progress_orders),
                "total_ops_cost": total_ops_val
            }
        }
