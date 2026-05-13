<p align="center">
  <img src="logo.png" width="120" alt="Ascendia Logo"/>
</p>

# Ascendia Academic Institution Philippines
## IT Asset Management System
### MSIT 631 Advanced Systems Design and Implementation

---

## Project Overview

A complete enterprise-grade IT Asset Management System built for Ascendia Academic Institution Philippines using Snipe-IT as the core platform, extended with AI-assisted maintenance scoring, polyglot database persistence, a fully interactive live dashboard, and a mobile QR scanner.

**Institution:** Ascendia Academic Institution Philippines  
**Developer:** Darwin Mari (darwin.admin)  
**Date:** May 2026  
**GitHub:** https://github.com/darwinmariph-blip/ascendia-ams

---

## 🚀 Quick Start

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

## 📊 Dashboard Features

| Page | Features |
|---|---|
| **Dashboard** | Live metrics, device health chart, clickable metric cards, recent activity |
| **Assets** | Full inventory, search/filter, checkout, checkin, maintenance tickets, location update, clickable rows with detail modal |
| **Telemetry** | Live InfluxDB health data, filter by critical/warning/healthy, clickable rows |
| **Staff** | Full staff directory, clickable rows with detail modal |
| **QR Labels** | Generate & print QR labels, asset lookup, clickable cards with detail modal |

---

## 🗄️ Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Core ITAM | Snipe-IT v8.4.1 | Asset lifecycle management |
| Web Server | Apache/Valet + PHP 8.5 | Hosts Snipe-IT |
| Primary DB | MySQL | Core assets, users, locations (D1) |
| Document Store | MongoDB | Maintenance docs, assignments, audit (D2) |
| Time-Series DB | InfluxDB 3.9 | Device telemetry, health scores (D3) |
| Graph DB | NetworkX + MongoDB | Relationship maps (D4) |
| Cache + Events | Redis 8.6 | Sessions, event streaming |
| AI Service | Python + FastAPI | NLP maintenance risk scoring |
| Dashboard | React (HTML) | Live interactive web UI |
| Mobile QR | HTML5 + JS | Asset scanning on mobile |

---

## 📦 Current Data

| Item | Count |
|---|---|
| Total Assets | 66 (AAI-2026-00001 to AAI-2026-00111) |
| Staff | 16 across 7 departments |
| Departments | 7 |
| Locations | 6 (QC-MAIN hierarchy) |
| Software Licenses | 3 (MS Office 365, Adobe CC, Windows 11 Education) |
| Telemetry Readings | 500+ |
| Maintenance Tickets | 5 (1 High, 1 Medium) |
| Audit Events | 30+ |

---

## 🖥️ Assets by Category

| Category | Count | Location |
|---|---|---|
| Laptops (Dell Latitude, MacBook Pro) | 5 | IT Office, Lab 1 |
| Desktops (Acer Aspire, HP EliteDesk) | 35 | Lab 1, Offices |
| Monitors (Dell UltraSharp) | 2 | IT Office |
| Projectors (Epson EB-X51) | 3 | Classrooms |
| Printers (HP LaserJet, Canon) | 4 | Offices |
| Network Equipment (Cisco, Ubiquiti) | 5 | IT Office, Main |
| UPS (APC) | 3 | IT Office |
| Tablets (iPad, Wacom) | 4 | IT Office, Classroom |
| Scanners (Epson DS-530) | 1 | Registrar |
| Audio Equipment (Logitech) | 1 | Classroom 101 |
| Security (Hikvision) | 3 | Main Campus |

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

## 📋 Custom Fields in Snipe-IT

| Field | Column | Purpose |
|---|---|---|
| AI Priority Score | `_snipeit_ai_priority_score_2` | NLP maintenance urgency |
| PO Number | `_snipeit_po_number_3` | Links asset to purchase order |
| Maintenance Notes | `_snipeit_maintenance_notes_4` | Issue description for AI scoring |
| Last Audit Date | `_snipeit_last_audit_date_5` | Annual audit tracking |

---

## ⚖️ Business Rules

| Rule | Description |
|---|---|
| BR001 | Assets only assigned to official employees — no students |
| BR002 | No checkout to inactive/terminated staff |
| BR003 | High AI priority → auto Maintenance-High status |
| BR004 | Asset movement must update within 24 hours |
| BR005 | Retired assets must have disposal note + evidence gates |

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
| `fastapi_service.py` | REST API (15 endpoints) |
| `reporting.py` | Full cross-database report |
| `security_network.py` | Network topology + security docs |
| `add_school_assets.py` | Adds 57 realistic school assets |
| `proxy.py` | CORS proxy for dashboard |
| `dashboard.html` | Live React dashboard (5 pages) |
| `mobile_qr.html` | Mobile QR scanner |
| `backup.sh` | Automated backup script |
| `start.sh` | System startup script |
| `docker-compose.yml` | Future production deployment |

---

## 🔒 Security

| Control | Status |
|---|---|
| RBAC | ✅ 16 staff with role-based permissions |
| Audit Logging | ✅ Full before/after trail in MongoDB |
| API Token Auth | ✅ Bearer token, never exposed in code |
| Database Isolation | ✅ API-only access pattern |
| Password Policy | ✅ Strong passwords enforced |
| Backup | ✅ Daily 2AM + Weekly Sunday 3AM |
| Event Streaming | ✅ Redis Streams event bus |
| HTTPS | ⚠️ HTTP locally — certbot SSL for production |

---

## 💾 Backup Schedule

```
Daily  : 2:00 AM  — MySQL + MongoDB + project files
Weekly : Sunday 3:00 AM — Full system backup
Location: ~/ascendia-ams/backups/ (keeps last 7)
```

---

## 🏗️ Architecture Coverage

| Document | Coverage |
|---|---|
| TO-BE Business Architecture | ✅ 100% |
| TO-BE Data Architecture (7 Deliverables) | ✅ 100% |
| TO-BE Application Architecture | ✅ 100% |
| Technology Architecture | ✅ 100% |

---

*Ascendia Academic Institution Philippines — IT Asset Management System*  
*Implemented by Group 1 — MSIT 631 Advanced Systems Design and Implementation*
