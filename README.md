# Ascendia Academic Institution Philippines
## IT Asset Management System — Project Documentation
### MSIT Capstone — Technology Architecture Implementation

---

## Project Overview

This project implements the complete TO-BE IT Asset Management System for Ascendia Academic Institution Philippines using Snipe-IT as the core platform, extended with custom integrations across all four polyglot databases, AI-assisted maintenance scoring, and a live web dashboard.

**Institution:** Ascendia Academic Institution Philippines  
**System:** IT Asset Management Transformation Using Snipe-IT  
**Developer:** Darwin Mari  
**Date:** May 2026  

---

## Architecture Documents Implemented

| Document | Coverage |
|---|---|
| TO-BE Business Architecture | 100% |
| TO-BE Data Architecture (7 Deliverables) | 100% |
| TO-BE Application Architecture | 100% |
| Technology Architecture | 100% |

---

## Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Core ITAM Platform | Snipe-IT v8.4.1 | Asset lifecycle management |
| Web Server | Apache/Valet + PHP 8.5 | Hosts Snipe-IT application |
| Primary Database | MySQL | Core transactional data (D1) |
| Document Store | MongoDB | Maintenance docs, assignments (D2) |
| Time-Series DB | InfluxDB 3.9 | Device telemetry, health (D3) |
| Graph Database | NetworkX + MongoDB | Relationship maps (D4) |
| Cache + Events | Redis 8.6 | Sessions, event streaming |
| AI Service | Python + FastAPI | Maintenance risk scoring |
| QR Tracking | HTML5 + JS | Asset scanning and labels |
| Dashboard | React (HTML) | Live management interface |
| Version Control | GitHub | Source code management |

---

## System Files

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
| `proxy.py` | CORS proxy for dashboard |
| `dashboard.html` | Live React dashboard (5 pages) |
| `mobile_qr.html` | Mobile QR scanner |
| `backup.sh` | Automated backup script |
| `start.sh` | System startup script |
| `docker-compose.yml` | Future production deployment |

---

## Data in System

| Item | Count |
|---|---|
| Assets | 9 (AAI-2026-00001 to AAI-2026-00009) |
| Staff | 16 across 7 departments |
| Departments | 7 |
| Locations | 6 (QC-MAIN hierarchy) |
| Purchase Orders | 3 (₱541,000 total value) |
| Maintenance Tickets | 5 (1 High, 1 Medium) |
| Software Licenses | 2 (MS Office 365, Adobe CC) |
| Audit Events | 28+ |
| Telemetry Readings | 261 |
| LMS Schedules | 3 classes |
| Finance Records | 9 assets with depreciation |
| KPI Snapshots | 1 |

---

## Staff Directory

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

## Business Rules Implemented

| Rule | Description | Enforcement |
|---|---|---|
| BR001 | Assets only assigned to official employees | System + Process |
| BR002 | No checkout to inactive/terminated staff | System enforced |
| BR003 | High AI priority → Maintenance-High status | System enforced |
| BR004 | Asset movement must update within 24 hours | Process enforced |
| BR005 | Retired assets must have disposal note | System enforced |

---

## Polyglot Persistence Implementation

| Store | Technology | Collections/Tables | Data |
|---|---|---|---|
| D1 SQL | MySQL (Snipe-IT) | assets, users, departments, locations, status_labels, asset_maintenances | 9 assets, 16 users |
| D2 NoSQL | MongoDB | maintenance_tickets, assignment_history, disposal_records, notifications, audit_events, software_licenses, digital_checkouts, asset_transfers, lms_schedules, finance_records, analytics_kpis, graph_relationships | 100+ documents |
| D3 Time-Series | InfluxDB | device_telemetry, maintenance_alerts | 261 readings |
| D4 Graph | NetworkX + MongoDB | graph_relationships | 31 nodes, 17 edges |
| Cache/Events | Redis | cache:assets, cache:users, sessions, ascendia:events stream | 10+ events |

---

## Custom Fields in Snipe-IT

| Field | DB Column | Type | Purpose |
|---|---|---|---|
| AI Priority Score | _snipeit_ai_priority_score_2 | List (High/Medium/Low/Unscored) | NLP maintenance urgency |
| PO Number | _snipeit_po_number_3 | Alpha-Numeric | Links asset to purchase order |
| Maintenance Notes | _snipeit_maintenance_notes_4 | Textarea | Issue description for AI scoring |
| Last Audit Date | _snipeit_last_audit_date_5 | Text (DATE) | Annual audit tracking |

---

## API Endpoints (FastAPI — localhost:8080)

| Method | Endpoint | Description |
|---|---|---|
| GET | / | System info |
| GET | /health | Health check |
| GET | /assets | All assets (cached) |
| GET | /assets/{tag} | Asset by tag |
| GET | /users | All users (cached) |
| GET | /maintenance/tickets | All tickets |
| POST | /maintenance/tickets | Create + auto-score ticket |
| GET | /maintenance/tickets/open | Open tickets only |
| GET | /audit/trail | Full audit log |
| GET | /licenses | Software licenses |
| GET | /notifications | Notifications log |
| GET | /disposals | Disposal records |
| POST | /disposals | Create disposal workflow |
| GET | /report/summary | Full KPI summary |

---

## How to Start the System

```bash
# 1. Start all databases
brew services start mysql mongodb-community influxdb redis

# 2. Start Snipe-IT
cd ~/Sites/snipe-it && valet start

# 3. Start proxy (keep terminal open)
cd ~/ascendia-ams && python3 proxy.py

# 4. Open dashboard
# http://localhost:8888/dashboard.html

# Optional: Start FastAPI service
python3 fastapi_service.py
# http://localhost:8080/docs
```

---

## Security Architecture

| Control | Status | Implementation |
|---|---|---|
| RBAC | ✅ | 16 staff with role-based permissions in Snipe-IT |
| Audit Logging | ✅ | MongoDB audit_events with full before/after trail |
| API Token Auth | ✅ | Bearer token in .env, injected server-side by proxy |
| Database Isolation | ✅ | No direct DB access, API-only pattern |
| Password Policy | ✅ | Strong passwords enforced on all accounts |
| Backup Protection | ✅ | Automated daily backups via cron |
| Event Streaming | ✅ | Redis Streams event bus |
| HTTPS | ⚠️ | HTTP in prototype — certbot SSL for production |

---

## Backup Schedule

- **Daily:** 2:00 AM — MySQL + MongoDB + project files
- **Weekly:** Sunday 3:00 AM — Full system backup
- **Retention:** Last 7 backups kept automatically
- **Location:** `~/ascendia-ams/backups/`

---

## Future Production Deployment

The `docker-compose.yml` file provides a containerized deployment configuration for:
- MySQL, MongoDB, InfluxDB, Redis
- Snipe-IT application
- FastAPI AI service

Deploy to VPS with:
```bash
docker-compose up -d
```

---

*Ascendia Academic Institution Philippines — IT Asset Management System*  
*Implemented by Darwin Mari — MSIT Capstone 2026*
