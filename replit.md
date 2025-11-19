# Dealer Outreach System - Stingerworx

## Project Overview
AI-driven multi-tenant SaaS platform for automated dealer discovery and outreach. Built for suppressor manufacturers (starting with Stingerworx) to connect with Class 3 SOT dealers across the United States.

## Current Status (MVP Phase 1 - In Progress)
**Date:** November 19, 2025  
**First Client:** Stingerworx (Craig)  
**Status:** Foundation Complete, Building Core Features

### What's Working
✅ Multi-tenant database architecture  
✅ FastAPI backend with REST API  
✅ React dashboard UI (Chakra UI)  
✅ Stingerworx tenant seeded with sample dealers  
✅ Basic dealer listing and stats display  
✅ Campaign management UI structure  
✅ **Crawl4AI Browser Automation** - Chromium headless browser for web scraping (WORKING!)  
✅ **Intelligent Website Discovery** - Google search + URL validation  
✅ **Contact Information Extraction** - Email, phone, address extraction from pages  
✅ **Class 3 SOT Verification** - AI analyzes dealer websites for NFA license indicators  
✅ **Real-Time Activity Feed** - Live monitoring of enrichment progress  
✅ **Live Logs Viewer** - Terminal-style real-time workflow monitoring  
✅ **WebRTC Browser Streaming** - Live video stream of browser automation using aiortc (10 FPS @ 720p)
✅ **Contact Page Detection** - Finds contact forms on Class 3 dealer websites for automated outreach
✅ **Form Field Analysis** - Extracts form field metadata (name, type, required) for future automation
✅ **Multi-Contact Method Storage** - Stores ALL contact pages found (forms, emails, phones) with priority ranking

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
- 2025-11-19: **Contact Page Detection & Form Field Analysis**
  - Built ContactPageDetector class that scans Class 3 verified dealer websites for contact pages
  - Searches for common contact URLs: /contact, /contact-us, /dealer-inquiry, /become-a-dealer, /wholesale-inquiry
  - Analyzes form fields and extracts metadata: field name, type, required status, placeholder text
  - Falls back to email/phone extraction if no forms found (doesn't skip Class 3 dealers)
  - Stores ALL contact pages found (not just one) in dealer.extra_data.contact_pages[] with priority ranking
  - Integrated into Class3Verifier workflow - runs automatically for Class 3 verified dealers only
  - Updated UI to show FORM/EMAIL/PHONE badges on dealer cards based on preferred contact method
  - System now prioritizes contact forms over email for outreach (bypasses spam filters)
- 2025-11-17: **WebRTC Browser Streaming - Optimized Screenshot Approach**
  - Reverted from CDP (compatibility issues in Replit) to optimized screenshot streaming
  - Background frame capture loop for non-blocking operation
  - Async frame buffer with locking for thread-safe access
  - 10 FPS @ 720p reliable streaming
  - Fixed hanging issue with CDP session creation
  - WebRTC client receives real-time browser updates via aiortc video track
- 2025-11-17: **WebRTC Browser Streaming Implemented**
  - Built complete WebRTC video streaming system using aiortc for real-time browser automation viewing
  - Added FastAPI signaling endpoints: /api/webrtc/offer, /api/webrtc/search, /api/webrtc/session (DELETE)
  - Implemented React BrowserStream component with RTCPeerConnection for WebRTC client
  - Supports live Google searches and URL navigation within video stream
  - Installed system dependencies: ffmpeg, libvpx, libopus, aiortc, av, numpy
  - Added "Live Stream" navigation link and dedicated /browser-stream page
- 2025-11-17: **Crawl4AI Successfully Integrated with Chromium**
  - Added system dependencies (chromium, mesa, libgbm) to replit.nix
  - Fixed Crawl4AI API compatibility issues (removed invalid CrawlerRunConfig parameters)
  - Verified browser automation working: Chromium launches, searches Google, scrapes dealer websites
  - System now finding real dealer websites (e.g., 5shotfirearms.com, 520tactical.com)
- 2025-11-17: **Enhanced Dealer Pipeline UI**
  - Added Class 3 SOT badges with AI confidence scores on dealer cards
  - Added contact info badges (Email, Phone, Contact Page) with hover tooltips
  - Created dealer detail modal showing class3_evidence and full enrichment data
  - Improved activity sidebar: filters irrelevant URLs, groups events by dealer with collapsible timelines
  - Fixed critical bug: Proper number parsing for confidence scores (handles strings/null/zero)
- 2025-11-16: **Complete UI/UX Redesign of Dealer Management**
  - Created dedicated `/dealers/import` page for importing dealers from ATF database
  - Redesigned main `/dealers` page as pipeline-based view with tabs:
    - All, Discovered, Enriched, Ready to Contact, Contacted
  - Added real-time activity sidebar showing AI enrichment progress (auto-refreshes every 3s)
  - Stats dashboard showing: Total Dealers, Discovered, Enriched, Class 3 Verified, Contacted
  - Smart filters: Search by name/city, filter by state
  - Card-based layout replacing messy table view
  - Fixed filter synchronization bug ensuring "Ready to Contact" respects search/state filters
  - Replaced @chakra-ui/icons with react-icons for better dependency stability
- 2025-11-16: **AI-Powered Class 3 SOT Verification**
  - Built Class3Verifier agent that analyzes dealer websites for Class 3 indicators
  - Searches for keywords: "Class 3", "SOT", "NFA", "suppressors", "silencers", "SBR"
  - AI analyzes website content to determine if dealer has Class 3 license
  - Stores verification confidence score and evidence
  - System now verifies Class 3 status from web sources (not just ATF data)
- 2025-11-16: **REAL ATF Dealer List Integration**
  - Uploaded official ATF dealer list with 78,408 total dealers
  - Imports Type 01/02 FFLs (can get Class 3 SOT) from all states
  - Updated ATF importer to read from Excel file
  - System verifies Class 3 status via AI web research (not relying on ATF sot_type alone)
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
