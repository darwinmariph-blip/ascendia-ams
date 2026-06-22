<p align="center">
  <img src="logo.png" width="120" alt="Ascendia Logo"/>
</p>

# Ascendia Academic Institution Philippines
## IT Asset Management System
### MSIT 631 Advanced Systems Design and Implementation

---

## 🌐 Live Deployment

**The system is deployed live on Google Cloud Platform — accessible 24/7, no local machine needed.**

> **🔐 New HTTPS Domain (Recommended for mobile QR scanning)**  
> The system is now also accessible via a secure domain with a valid SSL certificate — camera-based QR scanning works on mobile.

| Service | HTTPS URL |
|---|---|
| **Dashboard** | https://ascendia.mari-dev.tech/dashboard.html |
| **Mobile QR Scanner** | https://ascendia.mari-dev.tech/mobile_qr.html |

**The original IP‑based URLs below still work** (HTTP only), but the new domain provides **HTTPS** so the camera works on mobile devices.

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
