```markdown
# BergNavn Maritime Voyages — Project Overview and Work Plan

**Version:** 1.4  
**Last updated:** May 4, 2025  
**Author:** Eli  
**Target completion date:** November 30, 2025

---

## Introduction

**BergNavn Maritime Voyages** is a platform designed to support the booking and real-time management of maritime voyages. It offers tailored solutions for operators and passengers through a forward-looking architecture, scalable for future microservices and real-time data integration.

---

## Core Objectives

- Online booking of cruises
- Real-time voyage and fleet management for operators
- Live weather alerts from relevant maritime regions
- AI-based personalization of offers
- Secure and scalable backend infrastructure
- Modular frontend transitioning from Jinja2 templates to React
- Microservice-ready architecture planned for future implementation

---

## Stack Overview

- **Backend:** Flask, PostgreSQL, SQLAlchemy, Alembic  
- **Frontend:** Initial version using Jinja2 templates → gradual transition to React  
- **Infrastructure:** Docker (in a later phase), GitHub Actions for CI/CD  
- **Documentation:** Markdown files under `docs/`  
- **Testing & QA:** pytest, coverage tracking, and automated test scripts  

---

## Project Directory Structure

```

bergnavn/
│
├── app.py
├── .env
├── requirements.txt
├── .gitignore
├── readme.md
│
├── backend/
│   ├── **init**.py
│   ├── models/
│   ├── routes/
│   ├── controllers/
│   ├── services/
│   ├── middleware/
│   ├── config/
│   └── tests/
│
├── database/
│   └── init.sql
│
├── frontend/
│   └── index.html / app.js (Jinja2 or React)
│
├── migrations/
├── templates/
├── docs/
│   └── index.md
└── run\_checks.sh

```

---

## Work Plan (May – November 2025)

All tasks are tracked in `docs/weekly_log.md` and verified using `run_checks.sh`.

### Milestones:

1. **May 2025:**
   - Finalize model definitions (User, Cruise, Booking, Alert)
   - Set up the Alembic migration system
   - Build initial HTML templates for data presentation

2. **June 2025:**
   - Integrate the OpenWeather API for real-time alerts
   - Display weather alerts using Jinja templates
   - Develop a basic admin panel using Flask routes

3. **July 2025:**
   - Begin the transition to React for the booking interface
   - Define REST API endpoints for user and cruise operations
   - Deploy the first functional version to a staging environment

4. **August – September 2025:**
   - Implement authentication, user registration, and role-based access
   - Develop the operator dashboard with real-time data updates
   - Improve test coverage and CI/CD integration

5. **October – November 2025:**
   - Complete the React-based frontend
   - Finalize documentation and deployment automation
   - Draft the roadmap for microservice transition (Q1 2026)

---

## Notes

- Major updates are documented weekly.
- Migrations are reviewed using `alembic revision --autogenerate` before applying.
- Documentation, including this overview, is stored under the `docs/` directory.
- The system architecture is designed to enable a smooth transition to microservices in future phases.

---

## Contact & Ownership

Project maintained by **Eli**, for both internal and external stakeholders of BergNavn.  
Contact: `framgangsrik747@gmail.com` (placeholder)

---
```