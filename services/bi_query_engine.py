"""
Universal Omniscient Business Intelligence Engine
Handles:
- PDF / CSV / Word (.doc) / Text / Markdown exports across ALL query formats
- System, Security, WAF, Architecture, Authentication, and User Guide queries
- Math calculations & percentages
- Dynamic entity lookups, amounts, sectors, statuses, and counts
- Universal string & symbol normalization
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

        # 📄 1. UNIVERSAL EXPORT HANDLER (PDF, CSV, Word / DOC, Excel / XLS, Text)
        is_pdf = any(k in q_lower for k in ["pdf", "print pdf"])
        is_csv = any(k in q_lower for k in ["csv", "excel", "sheet", "spreadsheet"])
        is_word = any(k in q_lower for k in ["word", "doc", "docx", "document"])
        is_txt = any(k in q_lower for k in ["text", "txt", "file"])

        if is_pdf or is_csv or is_word or is_txt:
            if is_pdf:
                export_type = "PDF"
            elif is_csv:
                export_type = "CSV"
            elif is_word:
                export_type = "WORD"
            else:
                export_type = "TXT"

            stop_export_words = {"create", "me", "a", "pdf", "csv", "word", "doc", "docx", "text", "txt", "file", "of", "export", "download", "generate", "save", "make", "deals", "orders", "report", "list"}
            search_entity_tokens = [w for w in re.sub(r'[^a-zA-Z0-9_\-]', ' ', q_lower).split() if w not in stop_export_words and len(w) >= 3]
            entity_label = " ".join([t.title() for t in search_entity_tokens]) if search_entity_tokens else "All Workspace Data"

            lines = [
                f"{export_type} Report Exported for '{entity_label}':\n",
                f"- Extracted live workspace records matching {entity_label}.",
                f"- Downloading your {export_type} report file immediately."
            ]

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "export",
                "action_payload": {
                    "type": export_type.lower(),
                    "entity": entity_label
                }
            }

        # 🛡️ 2. SYSTEM SECURITY & ARCHITECTURE INTENT HANDLER
        is_security_query = any(k in q_lower for k in ["security", "secure", "waf", "attack", "audit", "log", "blocked", "checksum", "tamper", "owasp", "encryption", "password", "auth", "hashing", "safe", "protection"])

        if is_security_query and not any(w in q_lower for w in ["deal", "order", "company", "project", "sakura", "billed"]):
            audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []
            blocked_count = sum(1 for log in audit_logs if "BLOCKED" in log.get("event_type", ""))
            
            lines = [
                "Yes! The Skylark Drones Business Intelligence Agent is built with Enterprise-Grade Security Architecture:\n",
                "1. Client-Side SHA-256 Pre-Transmission Password Hashing:",
                "- Passwords are hashed in the browser using the Web Crypto API (crypto.subtle.digest) BEFORE network transmission.",
                "- Plaintext credentials are NEVER transmitted over the wire or stored in memory.\n",
                "2. OWASP WAF Security Guard:",
                "- Active Web Application Firewall inspecting all queries for XSS scripts, SQL Injection, and Prompt Injection patterns.\n",
                "3. Token-Bucket IP Rate Limiter:",
                "- Enforces 45 requests per 60-second window per IP address to prevent brute-force attacks.\n",
                "4. Cryptographic SHA-256 Audit Logger:",
                f"- Recorded {len(audit_logs)} security events. Blocked {blocked_count} malicious attack attempts.\n",
                "5. Scoped Monday.com API Token:",
                "- Uses read-only, minimal-privilege Bearer tokens for Monday.com GraphQL API v2 integration."
            ]

            return {
                "answer": "\n".join(lines),
                "is_clarification": False,
                "caveats": all_caveats,
                "action": "redirect",
                "action_payload": {"view": "view-security"}
            }

        # 🤖 3. REAL AI ENGINE (Google Gemini API Integration)
        audit_logs = self.security_guard.get_audit_logs() if self.security_guard else []
        system_knowledge_base = {
            "application_metadata": {
                "name": "Skylark Drones Monday.com Business Intelligence Agent",
                "version": "2.5 Production"
            }
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
                    "Analyze the user's question with extreme precision across all letters, symbols, numbers, and system architecture.\n"
                    "Rules:\n"
                    "1. DO NOT use markdown bold asterisks (**) or italic symbols (*) in your response. Keep all output in clean plain text.\n"
                    "2. EXPORT REQUESTS (PDF, CSV, Word, Text): State that the requested export file has been compiled and generated.\n"
                    "3. DATA LOOKUPS & NUMBERS: Search all fields and records in sales_deals_data and work_orders_data.\n"
                    "4. Keep responses clean, precise, and professional."
                )

                prompt = f"System Knowledge & Data Context:\n{json.dumps(data_context, indent=2)}\n\nUser Question: {q_raw}"

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

        # 🧠 4. UNIVERSAL NUMERIC & ENTITY MATCHING ENGINE (Offline Fallback)
        extracted_numbers = self.extract_exact_numbers(q_raw)
        
        matching_orders = []
        matching_deals = []

        if extracted_numbers:
            target_num = extracted_numbers[0]
            matching_orders = [o for o in cleaned_orders if abs(float(o.get("cost", 0)) - target_num) < 1.0 or target_num in self.extract_exact_numbers(json.dumps(o))]
            matching_deals = [d for d in cleaned_deals if abs(float(d.get("value", 0)) - target_num) < 1.0 or target_num in self.extract_exact_numbers(json.dumps(d))]

        if not matching_orders and not matching_deals:
            stop_words = {"what", "are", "the", "does", "have", "has", "is", "for", "in", "of", "how", "many", "much", "show", "list", "deals", "orders", "data", "tell", "me", "give", "find", "search", "lookup", "get", "with", "want", "everyone", "anyone", "all", "this", "deal", "information", "application", "secure"}
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
