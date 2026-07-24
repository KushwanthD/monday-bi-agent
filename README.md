# Skylark Drones — Monday.com Business Intelligence Agent

> **A full-stack, real-time executive BI dashboard** powered by Monday.com GraphQL API v2, featuring OWASP-grade security, SHA-256 client-side authentication, and a natural language query engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)
![Security](https://img.shields.io/badge/Security-OWASP%20WAF%20%2B%20SHA--256-red)
![API](https://img.shields.io/badge/Monday.com-GraphQL%20API%20v2-blueviolet)

## Overview

🌐 **Live Deployment Link:** [https://monday-bi-agent-j1c0.onrender.com/](https://monday-bi-agent-j1c0.onrender.com/)

The **Skylark Drones Monday BI Agent** is a cyberpunk-styled, glassmorphic executive intelligence portal that:

- Connects **live** to your Monday.com workspace via GraphQL API v2
- Dynamically discovers all boards, groups, and items (up to 500 items per request)
- Provides a **natural language BI assistant** for querying revenue, deal stages, client codes, and flight operations
- Enforces enterprise-grade security: SHA-256 pre-transmission hashing, OWASP WAF, and tamper-evident audit logs
- Auto-syncs every **15 seconds** to reflect real-time Monday.com changes

---

## Features

| Feature | Description |
|---|---|
| 🤖 **AI BI Assistant** | Natural language queries across Deals Funnel & Work Orders |
| 📊 **Live Board Viewer** | Dynamic discovery of all Monday.com boards and group tabs |
| 🎯 **Compound Filters** | Simultaneous Sector + Status + Stage + Search (AND logic) |
| 📋 **Leadership Briefings** | Auto-generated executive summaries for C-suite reviews |
| 🔐 **SHA-256 Login** | Client-side Web Crypto API hashing — plaintext never sent over network |
| 🛡️ **OWASP WAF** | Prompt injection detection, XSS sanitization, IP rate limiting |
| 📜 **SHA-256 Audit Log** | Tamper-evident cryptographic event log for all auth and queries |
| ⚡ **15s TTL Cache** | Sub-second response times with background Monday.com live sync |
| ↗️ **Monday.com Deep Links** | Direct "Open Board in Monday.com" navigation from any view |

---

## Security Architecture

```
Browser (Client)
    │
    ├─ Password entered
    ├─ SHA-256 hash computed via Web Crypto API (crypto.subtle.digest)
    ├─ Plaintext NEVER sent over the network
    └─ Only SHA-256 hex digest transmitted in POST body
          │
          ▼
Python HTTP Server
    ├─ OWASP WAF: prompt injection / XSS / SQLi pattern detection
    ├─ Token-bucket IP rate limiter (60 req/min per IP)
    ├─ SHA-256 credential comparison (stored hash vs transmitted hash)
    ├─ Tamper-evident SHA-256 audit log for every event
    └─ Read-only Monday.com Bearer token (strictly scoped)
```

---

## Project Structure

```
monday-bi-agent/
│
├── server.py                  # HTTP server, all API routes, SHA-256 auth
├── config.json                # API key & board IDs (gitignored — see config.example.json)
├── config.example.json        # Safe config template for new deployments
│
├── public/                    # Frontend (served at localhost:3000)
│   ├── index.html             # Main UI: Login Portal, Dashboard, All Views
│   ├── style.css              # Glassmorphism, dark theme, cyberpunk styles
│   └── app.js                 # SHA-256 login, filters, live polling, board discovery
│
├── services/
│   ├── monday_client.py       # Monday.com GraphQL API v2 + 15s TTL in-memory cache
│   ├── bi_query_engine.py     # Natural language BI query engine
│   ├── data_resilience.py     # Data cleaning, field normalization, schema resolution
│   └── leadership_update.py   # Executive briefing text generator
│
└── middleware/
    └── security_guard.py      # OWASP WAF, rate limiter, SHA-256 audit logger
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- A [Monday.com](https://monday.com) account with API access
- Your Monday.com **Personal API Token** from *Profile → Developers → API*

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/KushwanthD/monday-bi-agent.git
cd monday-bi-agent

# 2. Copy the config template
cp config.example.json config.json

# 3. Edit config.json with your Monday.com API token and board ID
#    (see Configuration section below)
```

### Configuration

Edit `config.json`:

```json
{
  "monday_api_key": "YOUR_MONDAY_PERSONAL_API_TOKEN_HERE",
  "deals_board_id": "",
  "work_orders_board_id": "YOUR_BOARD_ID_HERE"
}
```

> **How to find your API token:** Monday.com → Profile picture → Developers → My Access Tokens → Copy token

### Run the Server

```bash
python server.py
```

Then open your browser at: **`http://localhost:3000`**

---

## Login Credentials

> The following demo credentials are hardcoded for this deployment.

| Field | Value |
|---|---|
| **Username** | `Skylark` |
| **Password** | `Drones` |

> ⚠️ The password is hashed client-side via SHA-256 before transmission. The server only stores and compares the hash — never the plaintext.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Server health check & Monday.com connection status |
| `GET` | `/api/monday/boards` | Fetch all boards, groups, and items from Monday.com |
| `GET` | `/api/security/audit` | Retrieve SHA-256 tamper-evident audit log |
| `POST` | `/api/auth/login` | SHA-256 credential authentication |
| `POST` | `/api/query` | Natural language BI query engine |
| `POST` | `/api/leadership-update` | Generate executive leadership briefing |

---

## Dashboard Views

| View | Description |
|---|---|
| 💬 **Executive Chat BI** | KPI cards + natural language AI assistant |
| 📊 **Monday.com Boards** | Live table viewer with compound filters |
| 📋 **Leadership Briefing** | Formatted executive markdown briefing |
| 🛡️ **Security & WAF Audit** | SHA-256 audit log table |
| ℹ️ **System Architecture** | Full feature and security guide |

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, stdlib `http.server` |
| **Frontend** | Vanilla HTML5, CSS3, JavaScript (ES2022) |
| **API** | Monday.com GraphQL API v2 |
| **Authentication** | SHA-256 (Web Crypto API, client-side pre-hashing) |
| **Security** | OWASP WAF, Token-Bucket Rate Limiter, Tamper-Evident Audit Log |
| **Styling** | Glassmorphism, CSS Variables, JetBrains Mono + Outfit fonts |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Kushwanth D** — [GitHub](https://github.com/KushwanthD)

> Built for Skylark Drones — Executive BI Intelligence Portal
