# Clinic Manager — Healthcare Management System

> **Status: Production — actively used by a physiotherapy clinic in Alicante, Spain.**

A full-stack web application built to manage the day-to-day operations of a physiotherapy clinic: patients, treatment packages (bonuses), sales, PDF invoicing, and monthly reports with Excel export.

Built as a real project for a real client — not a tutorial, not a sandbox.

---

## Overview

The clinic needed a simple, private tool to replace spreadsheets. The system handles:

- Patient records and clinical notes
- Treatment packages (5 or 10-session bonuses) with automatic session tracking
- Sales registration per physiotherapist with automatic fee calculation
- Invoice generation and delivery by email (PDF attachment)
- Monthly and annual reports with Chart.js visualizations and Excel export

Only the clinic owner uses the system. Physiotherapists appear in sales and reports but do not have login access.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · Django 5 · Gunicorn |
| Database | PostgreSQL 16 |
| Frontend | Django Templates · HTMX · Alpine.js · Tailwind CSS · DaisyUI |
| PDF | ReportLab |
| Excel | openpyxl |
| Admin | Django Jazzmin |
| Proxy | Nginx |
| Deployment | Docker · docker-compose |
| Infrastructure | Raspberry Pi 5 · Cloudflare Tunnel |

---

## Features

**Patients**
- Full patient records: personal data, contact info, clinical notes
- Active/inactive status without deleting history
- Real-time search with accent-normalized filtering (handles Spanish names correctly)

**Bonuses (Treatment Packages)**
- 5 or 10-session packages, auto-numbered (B001, B002…)
- Session counter per sale — automatic deactivation when exhausted
- Protected deletion: packages with associated sales cannot be removed

**Sales**
- Per-session sales linked to patient, physiotherapist, and treatment type
- Optional bonus linkage — session count updates automatically on save
- Automatic physiotherapist fee calculation via a configurable rate table
- Multiple payment methods: cash, card, Bizum, bank transfer

**Invoicing**
- Invoice number auto-generated on creation (format: `2026/001`, resets yearly)
- PDF generated with ReportLab, delivered by email via Gmail SMTP
- Editable invoice body before sending
- Timestamp recorded on each send

**Reports**
- Monthly revenue breakdown by physiotherapist and treatment type
- Chart.js bar and line charts
- Full Excel export with openpyxl

---

## Infrastructure

Self-hosted on a **Raspberry Pi 5** running **25+ Docker containers** in production.

```
Cloudflare Tunnel (HTTPS)
        ↓
   Nginx (port 8083)
        ↓
  Gunicorn (2 workers)
        ↓
   Django application
        ↓
  PostgreSQL 16
```

- Cloudflare Tunnel handles HTTPS termination externally — no open ports on the home network
- Nginx serves static and media files directly, proxies all other requests to Gunicorn
- Gunicorn runs with 2 workers, tuned for a shared Pi environment
- Containers use fixed IPs to avoid iptables conflicts with other services
- Watchtower is explicitly disabled for this container — migrations require manual control

---

## Architecture

```
clinic-manager/
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
└── backend/
    ├── Dockerfile
    ├── requirements.txt
    ├── manage.py
    ├── apps/
    │   ├── users/        ← authentication + Physio model
    │   ├── patients/     ← patient records
    │   ├── bonuses/      ← treatment packages
    │   ├── sales/        ← sales + invoicing
    │   └── reports/      ← reports, charts, Excel export
    └── config/
        └── settings/
            ├── base.py
            ├── dev.py
            └── prod.py
```

**Key design decisions:**

- Physiotherapists are a separate model (`Physio`) — they appear in sales and reports but have no system login
- No Django REST Framework — pure Django Templates + HTMX, no separate API layer
- Invoice numbers reset yearly and are generated at creation time to guarantee uniqueness
- Accent-normalized search implemented in Python (PostgreSQL does not normalize diacritics by default)
- `on_delete=PROTECT` on patients and physiotherapists to preserve historical data

---

## Deployment

### Prerequisites

- Docker and docker-compose
- A `.env` file based on `.env.example`

### Run locally

```bash
git clone https://github.com/juan-arroyo/clinic-manager.git
cd clinic-manager
cp .env.example .env
# fill in your values in .env
docker compose up -d
```

Create a superuser to log in:

```bash
docker compose exec web python manage.py createsuperuser
```

The app will be available at `http://localhost:8083`.

### Rebuild after code changes

If only Python or templates changed:
```bash
docker compose restart web
```

If `requirements.txt` or `Dockerfile` changed:
```bash
docker compose build web
docker compose up -d web nginx
```

---

## Notes on Privacy

The codebase contains no real patient data. All names, DNIs, and contact details visible in tests and seed data are randomly generated.

When the clinic begins full operation, development will continue in a private repository. This public repo represents the clean, pre-production state of the project.

---

## Author

**Juan Manuel Arroyo**
IT Infrastructure · SysAdmin · Homelab

- Web: [jmarroyo.es](https://jmarroyo.es)
- GitHub: [github.com/juan-arroyo](https://github.com/juan-arroyo)
- LinkedIn: [linkedin.com/in/juanmarroyo](https://linkedin.com/in/juanmarroyo)
