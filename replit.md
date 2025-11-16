# Dealer Outreach System - Stingerworx

## Project Overview
AI-driven multi-tenant SaaS platform for automated dealer discovery and outreach. Built for suppressor manufacturers (starting with Stingerworx) to connect with Class 3 SOT dealers across the United States.

## Current Status (MVP Phase 1 - In Progress)
**Date:** November 16, 2025  
**First Client:** Stingerworx (Craig)  
**Status:** Foundation Complete, Building Core Features

### What's Working
✅ Multi-tenant database architecture  
✅ FastAPI backend with REST API  
✅ React dashboard UI (Chakra UI)  
✅ Stingerworx tenant seeded with sample dealers  
✅ Basic dealer listing and stats display  
✅ Campaign management UI structure  
✅ **AI-Powered Web Crawler** - Real dealer discovery using OpenAI  
✅ **Intelligent Website Discovery** - AI predicts and validates dealer websites  
✅ **Contact Information Extraction** - AI analyzes pages for email, phone, address

### In Progress
🔄 Contact form automation with Playwright  
🔄 Approval workflow system  
🔄 Response tracking and analytics

## Architecture

### Tech Stack
- **Backend:** Python FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** React 18, Vite, Chakra UI, React Router
- **AI/LLM:** OpenAI (for message personalization)
- **Automation:** Playwright (browser automation), Scrapy (web scraping)
- **Background Jobs:** Celery + Redis (planned)
- **Database:** PostgreSQL (Replit managed)

### Project Structure
```
/backend
  ├── main.py              # FastAPI app and API endpoints
  ├── database.py          # Database connection
  ├── models.py            # SQLAlchemy models
  ├── seed_data.py         # Stingerworx initial data
  └── requirements.txt     # Python dependencies

/frontend
  ├── src/
  │   ├── components/      # Reusable UI components
  │   ├── pages/           # Dashboard, Dealers, Campaigns
  │   ├── services/        # API clients
  │   ├── App.jsx          # Main app component
  │   └── main.jsx         # Entry point
  ├── index.html
  ├── vite.config.js       # Vite config (allowedHosts: true)
  └── package.json
```

### Database Schema
**Multi-tenant with row-level tenant_id isolation**

**Core Tables:**
- `tenants` - Client companies (Stingerworx, etc.)
- `users` - User accounts per tenant
- `dealers` - Class 3 SOT dealer prospects
- `message_templates` - Outreach message templates
- `outreach_attempts` - Contact attempts and responses

**Dealer Statuses:**
- discovered → enriched → contacted → responded → interested/not_interested

**Outreach Statuses:**
- pending → approved → sent → responded/failed

## API Endpoints

### Health & Info
- `GET /` - API info
- `GET /api/health` - Health check

### Tenants
- `POST /api/tenants` - Create new tenant

### Dealers
- `GET /api/dealers?tenant_id={id}` - List dealers
- Supports pagination (skip/limit)

### Outreach
- `GET /api/outreach?tenant_id={id}` - List outreach attempts

### Stats
- `GET /api/stats?tenant_id={id}` - Dashboard statistics

## Workflows
- **backend:** `uvicorn main:app --host 0.0.0.0 --port 8000` (port 8000)
- **frontend:** `npm run dev` (port 5000, webview)

## Environment Variables
- `DATABASE_URL` - PostgreSQL connection string (auto-configured)
- `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` - DB credentials
- (Future) `OPENAI_API_KEY` - For LLM message generation

## Phase Implementation Plan

### Phase 0: Foundation ✅ COMPLETE
- Multi-tenant database schema
- FastAPI backend with basic endpoints
- React dashboard UI
- Stingerworx as first tenant

### Phase 1: Dealer Discovery (Current)
- [ ] ATF FFL list importer (CSV parser)
- [ ] Web scraping engine for dealer directories
- [ ] Contact enrichment (find websites, forms, emails)
- [ ] Dealer management UI enhancements

### Phase 2: Outreach Automation (Next)
- [ ] OpenAI integration for message personalization
- [ ] Message template system with variables
- [ ] Playwright browser automation for form submissions
- [ ] Email fallback system
- [ ] Approval workflow UI

### Phase 3: Response Management
- [ ] Response tracking and lead scoring
- [ ] Notification system (email/dashboard alerts)
- [ ] Analytics and reporting
- [ ] Campaign optimization tools

### Phase 4: Enterprise Features
- [ ] User authentication (Replit Auth)
- [ ] Advanced rate limiting
- [ ] Audit logging
- [ ] Multi-client onboarding flow

## Business Context

### Problem
Suppressor manufacturers like Stingerworx struggle to expand their dealer network. They need to efficiently identify and reach out to ~1,300+ Class 3 SOT dealers across 42 states.

### Solution
Automated AI-driven system that:
1. Continuously discovers Class 3 dealers via ATF lists and web scraping
2. Enriches contact info (websites, forms, emails)
3. Generates personalized outreach messages using LLM
4. Automates contact form submissions (bypasses email spam filters)
5. Tracks responses and notifies sales team of interested leads

### Key Differentiators
- **Contact Form Strategy:** Bypasses spam filters by submitting via dealer websites
- **AI Personalization:** Each message customized using dealer context
- **Human-in-Loop:** Approval gates for quality control
- **Multi-Tenant SaaS:** Scales to multiple manufacturer clients

## Recent Changes
- 2025-11-16: **REAL ATF Dealer List Integration**
  - Uploaded official ATF dealer list with 78,408 total dealers
  - Filtered for 6,066 Class 3 SOT dealers (SOT Type 2 - NFA/suppressor licenses)
  - Updated ATF importer to read from Excel file and filter by SOT type
  - Top states: TX (974), FL (545), GA (426), NC (332)
  - System now imports verified Class 3 dealers instead of mock data
- 2025-11-16: **AI-Powered Web Crawler Implemented**
  - Created AIBrowserAgent class using OpenAI AI Integrations
  - Multi-strategy search: DuckDuckGo → Google → AI prediction
  - AI extracts contact info (email, phone, address, forms) from webpages
  - No API keys required (uses Replit AI Integrations, billed to credits)
- 2025-11-16: **Real-Time Activity Feed**
  - Live monitoring of AI web crawling progress
  - Auto-refreshes every 2 seconds
  - Shows dealer search, website discovery, contact extraction steps
- 2025-11-16: Initial project setup, database schema, basic UI

## Next Steps
1. Build ATF list importer
2. Implement web scraping for dealer discovery
3. Add OpenAI integration for message generation
4. Build Playwright automation for form submissions

## Notes
- Frontend configured with `allowedHosts: true` for Replit proxy
- Database uses `extra_data` JSON column (not `metadata` - reserved by SQLAlchemy)
- API supports multi-tenancy via `tenant_id` query parameter
- Stingerworx is tenant_id=1
