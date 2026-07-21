# 📄 Executive Decision Log & Technical Justification

**Project:** Skylark Drones — Monday.com Business Intelligence Agent  
**Role:** Full-Stack & Cybersecurity Engineering Assessment  
**Author:** Candidate  

---

## 1. Key Assumptions Made

1. **Board Schema & Entity Relationships:**
   - Assumed two primary operational boards exist in monday.com: **Deals** (Sales pipeline) and **Work Orders** (Execution & Flight logs).
   - Assumed that *Work Orders* can reference *Deals* via a shared `Deal ID` key (e.g., `D-101`), enabling cross-board joins while also supporting standalone ad-hoc operational flights.

2. **Data Messiness & Real-World Inconsistency:**
   - Real-world monday.com board exports contain messy data: casing discrepancies in sector tags (e.g., `ENERGY`, `energy sector`, `Energy`), varying date string formats (`YYYY-MM-DD`, `MM/DD/YYYY`, `May 18 2026`), missing deal values, and missing flight completion dates.
   - Assumed the BI agent must handle all raw data resiliently by applying automated normalization rather than failing or returning empty outputs.

3. **Read-Only API Scoping:**
   - Assumed Monday.com connection should operate strictly in **Read-Only mode** to adhere to the Principle of Least Privilege, preventing accidental board mutations during BI analysis.

---

## 2. Technical & Security Trade-Offs Chosen

| Component | Choice Made | Alternatives Considered | Rationale & Trade-Off |
| :--- | :--- | :--- | :--- |
| **API Integration** | Direct **Monday.com GraphQL API v2** + Local Resilient Fallback | Model Context Protocol (MCP) Server | Direct GraphQL API provides fine-grained parameter control, strict error handling, and zero protocol overhead for high-frequency queries. Fallback dataset ensures 100% demo availability. |
| **Backend Runtime** | Python 3 Standard Library HTTP Engine | Node.js / Express / External Frameworks | Eliminates external npm dependency supply chain risks, ensures zero zero-day vulnerabilities in third-party packages, and delivers ultra-fast startup with built-in OWASP security headers. |
| **Data Normalization** | In-Memory Streaming Resilience Engine | Persistent SQL Database (PostgreSQL / SQLite) | Avoids database sync lag and storage overhead. Computes clean normalized data on-the-fly during dynamic Monday.com board queries. |
| **Security Architecture** | Custom WAF Guard (`security_guard.py`) | No Input Sanitization / Basic Regex | Protects against LLM Prompt Injection attacks, XSS script tags, and DoS rate limit abuse before queries reach the analytics engine. |

---

## 3. Interpretation of "Leadership Updates" (Optional Requirement)

We interpreted **"Leadership Updates"** as an automated executive briefing tool that synthesizes cross-board metrics into a formatted C-suite report.

### Implementation:
- Implemented via a dedicated `/api/leadership-update` backend service and a one-click **"⚡ Leadership Update"** console trigger.
- **Executive Output Structure:**
  1. **Commercial Highlights:** Total pipeline value, closed-won revenue, active proposals in negotiation, and leading revenue sector.
  2. **Operations & Execution:** Completed drone flight missions, active flights in progress, operational expenditure, and correlation between closed deals & active work orders.
  3. **Strategic Recommendations:** Key focus areas and pilot resource allocation warnings.
  4. **Data Integrity Audit:** Transparent list of data caveats and missing value notifications.

---

## 4. What We Would Do Differently With More Time

1. **Persistent Caching & Webhooks:**
   - Implement monday.com Webhook listeners to invalidate local query caches instantly when board column values change.
2. **Multi-LLM Hybrid Orchestration:**
   - Add direct API integration with Claude 3.5 / Gemini Pro for advanced natural-language nuance parsing alongside our fast deterministic BI engine.
3. **Role-Based Access Control (RBAC):**
   - Implement JWT-based executive authentication to restrict sensitive financial metrics based on user clearance level.

---

## 5. Security & Defense-in-Depth Summary

- **OWASP Compliance:** Implemented CSP, HSTS, `X-Frame-Options: DENY`, and Content-Type sniffing protection.
- **Input Guarding:** HTML entity escaping and regex pattern matching to block prompt injection vectors.
- **Tamper-Evident Logging:** SHA-256 hash checksums attached to all security audit entries.
- **Token Security:** Environment variable isolation (`MONDAY_API_TOKEN`) preventing client-side leakages.
