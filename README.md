<p align="center">
  <img src="logo.png" width="120" alt="Ascendia Logo"/>
</p>

# Ascendia Academic Institution Philippines
## IT Asset Management System
### MSIT 631 Advanced Systems Design and Implementation

---

## 🌐 Live Deployment

**The system is deployed live on Google Cloud Platform — accessible 24/7, no local machine needed.**

| Service | URL |
|---|---|
| **Dashboard** | http://136.110.27.21:8888/dashboard.html |
| **Snipe-IT** | http://136.110.27.21:8090 |
| **Mobile QR Scanner** | http://136.110.27.21:8888/mobile_qr.html |
| **FastAPI Docs** | http://136.110.27.21:8080/docs |

**Login Credentials:**
| Username | Password | Role |
|---|---|---|
| `darwin.admin` | `Ascendia@2026!` | IT Admin (All 12 pages) |
| `groupmate.admin` | `Ascendia@2026!` | IT Admin (All 12 pages) |

> **Browser note:** Chrome, Brave, and Firefox are fully supported. Safari users should disable "Prevent cross-site tracking" in Privacy settings for full functionality.

---

## 🚀 Local Quick Start (Mac development environment)

```bash
# 1. Start all services
brew services start mysql mongodb-community influxdb redis
cd ~/Sites/snipe-it && valet start

# 2. Start proxy (keep terminal open)
cd ~/ascendia-ams && python3 proxy.py

# 3. Open dashboard
# http://localhost:8888/dashboard.html

# 4. Open mobile QR scanner
# http://localhost:8888/mobile_qr.html

# 5. Open API docs (optional)
# python3 fastapi_service.py → http://localhost:8080/docs
```

---

## ☁️ Cloud Infrastructure (Google Cloud Platform)

| Component | Details |
|---|---|
| **VM Instance** | ascendia-server (e2-micro, asia-southeast1-a, Singapore) |
| **OS** | Ubuntu 26.04 LTS |
| **External IP** | 136.110.27.21 |
| **Containerization** | Docker Compose — 6 containers |
| **Proxy Service** | systemd service (ascendia-proxy.service) — auto-restarts on crash/reboot |

**Docker containers running on the server:**
| Container | Image | Port |
|---|---|---|
| ascendia_snipeit | snipe/snipe-it:latest | 8090 → 80 |
| ascendia_api | ascendia-ams-fastapi | 8080 |
| ascendia_mysql | mysql:8.0 | 3307 → 3306 |
| ascendia_mongodb | mongo:6 | 27018 → 27017 |
| ascendia_redis | redis:7-alpine | 6380 → 6379 |
| ascendia_influxdb | influxdb:2.7 | 8181 → 8086 |

**Proxy systemd service** (auto-starts on server reboot):
```bash
sudo systemctl status ascendia-proxy
sudo systemctl restart ascendia-proxy
```

---

## 📊 Dashboard Pages (12 pages)

| Page | Features |
|---|---|
| **Dashboard** | Live metrics, device health chart, clickable metric cards, recent activity |
| **Assets** | Full inventory (363 assets), search/filter, checkout, checkin, maintenance tickets, location update, clickable rows with detail modal |
| **Telemetry** | Live InfluxDB health data, filter by critical/warning/healthy, clickable rows |
| **Staff** | Full directory, clickable rows with detail modal, + Staff button |
| **Requests** | Submit maintenance, asset request, and transfer requests |
| **Licenses** | Software license tracking, seat usage, utilization bars, expiry alerts |
| **Audit Trail** | Full audit history with actor, before/after, timestamp, filter by type |
| **Analytics** | 4 tabs — Overview, Timeline (2023-2026), Cost Intelligence (depreciation), Predictions (maintenance forecasts & budget) |
| **Disposal** | Retirement workflow with 4 evidence gates |
| **Acknowledgments** | Digital checkout acknowledgment tracking |
| **LMS Schedule** | Class schedules, active/upcoming/done/tomorrow view, lab readiness checks |
| **QR Labels** | Generate & print QR labels, asset lookup, clickable cards with detail modal |

---

## 🔐 Login & Security

| Layer | Description |
|---|---|
| **Login page** | Validates username exists in Snipe-IT and account is active |
| **Role-based navigation** | Shows only pages allowed for the user's role (derived from job title) |
| **Proxy server** | Forwards API requests using a master Bearer token — never exposed to the browser |

**Role access matrix:**
| Role | Pages |
|---|---|
| IT Admin | All 12 pages |
| IT Asset Manager | 10 pages (no Staff) |
| Faculty | Dashboard, Requests, Acknowledgments, LMS Schedule |
| Finance | Dashboard, Requests, Licenses, Analytics, Disposal |
| Staff | Dashboard, Requests, LMS Schedule |

See `Ascendia_AMS_Credentials.docx` for the full list of 17 accounts.

---

## 🗄️ Technology Stack (Polyglot Persistence)

| Component | Technology | Purpose |
|---|---|---|
| Core ITAM | Snipe-IT v8.6.2 | Asset lifecycle management |
| D1 — Relational | MySQL 8.0 | Core assets, users, locations |
| D2 — Document | MongoDB 6 | Maintenance docs, audit events, LMS schedules, finance records |
| D3 — Time-Series | InfluxDB 2.7 | Device telemetry, health scores (3 years of monthly data) |
| D4 — Graph | NetworkX + MongoDB | Asset relationship maps |
| D5 — Cache/Events | Redis 7 | Sessions, event streaming |
| AI Service | Python + FastAPI | NLP maintenance risk scoring |
| Dashboard | React (in-browser Babel) | Live interactive web UI — 12 pages, role-based |
| Mobile QR | HTML5 + JS | Asset scanning on mobile browsers |

---

## 📦 Current Data (3-Year Dataset)

| Item | Count |
|---|---|
| Total Assets | **363** (acquired 2023–2026) |
| Staff | 17 across 7 departments |
| Departments | 7 |
| Locations | 6 (QC-MAIN hierarchy) |
| Suppliers | 13 |
| Software Licenses | 11 |
| Total Inventory Value | **₱13M+** |
| Audit Events | 843+ |
| Maintenance Tickets | 14 |
| Finance Records | 4 (one per year, 2023–2026) |
| Telemetry Readings | Monthly per asset since purchase date |

**Asset acquisition by year:**
| Year | Assets | Spend |
|---|---|---|
| 2023 | 116 | ₱5.5M |
| 2024 | 117 | ₱6.8M |
| 2025 | 63 | ₱3.9M |
| 2026 | 58 | ₱1.4M |

---

## 📈 Analytics — Cost Intelligence & Predictions

The Analytics page covers 4 dimensions for graduate-level analysis:

1. **Overview** — category, AI priority, location, vendor distribution
2. **Timeline** — 3-year acquisition trend with year-over-year spend comparison
3. **Cost Intelligence** — straight-line 5-year depreciation, book value vs. depreciated value per acquisition batch
4. **Predictions** — maintenance forecasts (assets 3+ years old or High AI priority), replacement forecasts (4+ years old), 2027–2028 budget estimates, asset age distribution

---

## 👥 Staff Directory

| Employee # | Name | Role | Department |
|---|---|---|---|
| EMP-00001 | Maria Santos | Faculty | College of Computer Studies |
| EMP-00002 | Jose Reyes | IT Technician | IT Support |
| EMP-00003 | Ana Cruz | Registrar Staff | Registrar's Office |
| EMP-00004 | Juan Dela Cruz | Finance Officer | Finance |
| EMP-00005 | Liza Mendoza | Faculty | College of Computer Studies |
| EMP-00006 | Roberto Garcia | IT Asset Manager | IT Support |
| EMP-00007 | Patricia Lim | HR Officer | Human Resources |
| EMP-00008 | Miguel Torres | Department Chair | College of Computer Studies |
| EMP-00009 | Carlos Reyes | Department Head | College of Computer Studies |
| EMP-00010 | Sandra Bautista | Finance Controller | Finance |
| EMP-00011 | Ramon Villanueva | Facilities Manager | Property Office |
| EMP-00012 | Elena Gomez | IT Support Manager | IT Support |
| EMP-00013 | Marco Fernandez | Network Administrator | Network Administration |
| EMP-00014 | Diana Santos | HR Director | Human Resources |
| EMP-00015 | Felix Aquino | Procurement Manager | Property Office |

---

## ⚖️ Business Rules

| Rule | Description |
|---|---|
| BR001 | Assets only assigned to official employees — no students |
| BR002 | No checkout to inactive/terminated staff |
| BR003 | High AI priority → auto Maintenance-High status |
| BR004 | Asset movement must update within 24 hours |
| BR005 | Retired assets must have disposal note + 4 evidence gates |

---

## 🗂️ Project Files

| File | Purpose |
|---|---|
| `snipeit_client.py` | Core Snipe-IT API client |
| `hris_sync.py` | HRIS user synchronization |
| `procurement_intake.py` | PO → asset auto-creation |
| `ai_priority_scorer.py` | NLP maintenance risk scoring |
| `mongodb_integration.py` | D2 NoSQL maintenance documents |
| `influxdb_telemetry.py` | D3 time-series device health |
| `graph_db.py` | D4 graph relationship maps |
| `integration_layer.py` | Redis, audit, notifications, licenses, disposal |
| `complete_remaining.py` | Digital checkout, transfers, LMS, Finance ERP, KPIs |
| `event_streaming.py` | Redis Streams event bus |
| `fastapi_service.py` | REST API (15+ endpoints) |
| `reporting.py` | Full cross-database report |
| `security_network.py` | Network topology + security docs |
| `add_300_assets.py` | Adds 3-year batch of assets (2023–2026) |
| `add_3year_telemetry.py` | Generates 3 years of telemetry, audit & finance data |
| `sync_watcher.py` | Real-time sync watcher (30s polling) |
| `proxy.py` | CORS proxy + static file server for dashboard |
| `dashboard.html` | Live React dashboard (12 pages, login & RBAC) |
| `mobile_qr.html` | Mobile QR scanner |
| `backup.sh` | Automated backup script |
| `start.sh` | Local system startup script |
| `docker-compose.yml` | Cloud/production deployment |
| `SETUP_MAC.txt` / `SETUP_WINDOWS.txt` | Step-by-step QA installation guides |

---

## 🔒 Security

| Control | Status |
|---|---|
| RBAC | ✅ 17 staff with role-based permissions |
| Audit Logging | ✅ Full before/after trail in MongoDB (843+ events) |
| API Token Auth | ✅ Bearer token, never exposed to browser |
| Database Isolation | ✅ API-only access pattern |
| Password Policy | ✅ Strong passwords enforced |
| Backup | ✅ Daily automated backups |
| Event Streaming | ✅ Redis Streams event bus |
| Process Resilience | ✅ systemd auto-restart for proxy service |
| HTTPS | ⚠️ HTTP only — SSL via certbot is the documented next step for production |

---

## 🏗️ Architecture Coverage

| Document | Coverage |
|---|---|
| TO-BE Business Architecture | ✅ 100% |
| TO-BE Data Architecture (7 Deliverables) | ✅ 100% |
| TO-BE Application Architecture | ✅ 100% |
| Technology Architecture | ✅ 100% |
| C4 Model (Context/Container/Component/Code) | ✅ 100% |

---

## 📝 Known Limitations & Future Improvements

- Password verification on dashboard login checks username/activation only; full password hash verification requires an OAuth2 integration with Snipe-IT
- HTTPS/SSL not yet configured — documented as the next production step (certbot + domain name)
- Safari requires disabling "Prevent cross-site tracking" due to cross-origin session cookies between dashboard (port 8888) and Snipe-IT (port 8090)
- Camera-based QR scanning requires HTTPS (browser security policy) — Manual entry tab works on HTTP
- Proxy password protection (`PROXY_PASSWORD`) planned but not yet implemented

---

*Ascendia Academic Institution Philippines — IT Asset Management System*
*Implemented by Group 1 — MSIT 631 Advanced Systems Design and Implementation*
