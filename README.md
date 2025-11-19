# Stingerworx Dealer Outreach System

An AI-driven multi-tenant SaaS platform for automating dealer discovery and outreach. Built for suppressor manufacturers to connect with Class 3 SOT dealers across the United States.

## 🚀 Features

- **Dealer Discovery**: Automatically imports and enriches dealer data from ATF lists.
- **AI Enrichment**: Finds websites, emails, and contact forms using AI-powered web scraping.
- **Class 3 Verification**: Verifies SOT status by analyzing dealer websites.
- **Outreach Automation**: Personalized message generation and approval workflows.
- **Live Browser Streaming**: View the AI agent navigating the web in real-time via WebRTC.

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, Vite, Chakra UI
- **Automation**: Playwright, Crawl4AI
- **AI**: OpenAI GPT-4o

## 📦 Project Structure

```
/backend
  ├── main.py              # FastAPI app entry point
  ├── models.py            # Database models
  ├── scrapers/            # AI scrapers & importers
  └── services/            # Business logic services

/frontend
  ├── src/
  │   ├── pages/           # React pages
  │   └── components/      # UI components
```

## 🏃‍♂️ Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```

## 📝 License

Proprietary software built for Stingerworx.
