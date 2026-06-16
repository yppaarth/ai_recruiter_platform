# 🚀 AI Recruiter Outreach Platform

> An AI-powered bulk email outreach platform that generates **unique, personalized recruiter emails** for every contact using the Grok API — with tracking, follow-ups, reply detection, and a full analytics dashboard.

---

## 📐 Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)               │
│  Dashboard │ Campaigns │ Analytics │ Templates │ Settings    │
└─────────────────────────┬────────────────────────────────────┘
                          │ HTTP / REST
┌─────────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend (Python 3.12)               │
│  /auth │ /campaigns │ /contacts │ /upload │ /tracking        │
│  /analytics │ /templates │ /export │ /ai │ /replies          │
└──────┬────────────┬──────────────────────────────────────────┘
       │            │
  ┌────▼────┐  ┌────▼────────────────────────────────────────┐
  │PostgreSQL│  │            Redis + Celery Workers           │
  │ Database │  │  email_tasks │ followup_tasks │ reply_tasks │
  └──────────┘  │  analytics_tasks │ celery_beat (scheduler) │
                └────────────────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Grok API (xAI)   │
                    │  Email generation  │
                    │  AI Analytics      │
                    └────────────────────┘
```

---

## ✨ Features

| Feature | Details |
|---|---|
| **AI Email Generation** | Grok API generates unique subject + body per recruiter |
| **Bulk Campaigns** | Send to 1000+ contacts with rate limiting & random delays |
| **Email Tracking** | 1×1 pixel open tracking + link click tracking |
| **Follow-up Automation** | Auto follow-ups at 3, 7, 14 days if no reply |
| **Reply Detection** | IMAP polling detects replies, cancels pending follow-ups |
| **Analytics Dashboard** | Open/click/reply rates, daily charts, top companies |
| **AI Analytics** | Grok generates campaign insights ("Amazon recruiters 2.3× more responsive") |
| **Excel/CSV Upload** | Auto-detects custom columns beyond name/email/company/title |
| **Resume Attachment** | PDF resume auto-attached to every outgoing email |
| **Export** | CSV, Excel, PDF analytics report per campaign |
| **JWT Auth** | Access + refresh tokens, per-user SMTP/IMAP settings |
| **Audit Logs** | Every action (login, send, reply) is logged |
| **Jinja2 Templates** | `{{name}}`, `{{company}}`, `{{title}}` + custom columns |

---

## 🛠 Tech Stack

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL, Redis, Celery  
**Frontend:** React 18, Vite, TypeScript, TailwindCSS, Recharts  
**AI:** Grok API (xAI) via `/v1/chat/completions`  
**Email:** SMTP (Gmail/Outlook), IMAP for reply detection  
**DevOps:** Docker, Docker Compose, Nginx  
**Testing:** Pytest, FastAPI TestClient  

---

## 🚀 Quick Start (Docker)

### 1. Clone and configure

```bash
git clone <repo>
cd ai-recruiter-platform
cp .env.example .env
```

### 2. Edit `.env` — only 3 required fields to start

```env
SECRET_KEY=your-secret-key-min-32-chars-change-this
GROK_API_KEY=your_grok_api_key_here        # from console.x.ai
SMTP_USERNAME=your_gmail@gmail.com
SMTP_PASSWORD=your_gmail_app_password      # Gmail App Password
```

### 3. Launch everything

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/api/docs |
| Flower (Celery monitor) | http://localhost:5555 |

---

## 💻 Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in values

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000

# Start Celery worker (new terminal)
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery beat scheduler (new terminal)
celery -A app.tasks.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `SECRET_KEY` | JWT signing secret (32+ chars) | ✅ |
| `GROK_API_KEY` | xAI Grok API key | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | ✅ |
| `SMTP_USERNAME` | Sending email address | ✅ |
| `SMTP_PASSWORD` | Gmail App Password | ✅ |
| `REDIS_URL` | Redis connection | ✅ |
| `IMAP_USERNAME` | For reply detection (optional) | ❌ |
| `EMAILS_PER_HOUR` | Rate limit (default: 50) | ❌ |
| `BASE_URL` | Public URL for tracking pixels | ❌ |

---

## 📁 Project Structure

```
ai-recruiter-platform/
├── backend/
│   ├── app/
│   │   ├── api/routes/     # FastAPI route handlers
│   │   ├── core/           # Config, security, logging
│   │   ├── db/             # SQLAlchemy session
│   │   ├── models/         # SQLAlchemy ORM models
│   │   ├── schemas/        # Pydantic request/response schemas
│   │   ├── services/       # Business logic (Grok, SMTP, IMAP, export)
│   │   ├── tasks/          # Celery async tasks
│   │   └── main.py         # FastAPI app factory
│   ├── alembic/            # Database migrations
│   ├── tests/              # Unit + integration tests
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/          # Route-level page components
│       ├── components/     # Shared UI components
│       ├── hooks/          # React hooks (useAuth)
│       ├── services/       # Axios API client
│       └── types/          # TypeScript interfaces
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 📊 API Reference

### Authentication
```
POST /api/v1/auth/register    Register new user
POST /api/v1/auth/login       Login, get JWT tokens
POST /api/v1/auth/refresh     Refresh access token
GET  /api/v1/auth/me          Get current user
PUT  /api/v1/auth/smtp-settings  Update SMTP/IMAP config
```

### Campaigns
```
GET    /api/v1/campaigns/              List campaigns
POST   /api/v1/campaigns/             Create campaign
GET    /api/v1/campaigns/{id}         Get campaign + stats
PUT    /api/v1/campaigns/{id}         Update campaign
DELETE /api/v1/campaigns/{id}         Delete campaign
POST   /api/v1/campaigns/{id}/generate-emails  AI generate emails
POST   /api/v1/campaigns/{id}/launch  Launch campaign
POST   /api/v1/campaigns/{id}/pause   Pause campaign
POST   /api/v1/campaigns/{id}/resume  Resume campaign
POST   /api/v1/campaigns/{id}/clone   Clone campaign
POST   /api/v1/campaigns/{id}/ai-summary  Generate AI insights
```

### Upload
```
POST /api/v1/upload/contacts/{campaign_id}  Upload CSV/XLSX
POST /api/v1/upload/resume/{campaign_id}    Upload PDF resume
```

### Tracking (no auth — called by email clients)
```
GET /api/v1/tracking/open/{tracking_id}    Track email open (returns 1×1 GIF)
GET /api/v1/tracking/click/{email_id}      Track link click + redirect
```

### Analytics
```
GET /api/v1/analytics/overview              Overall stats + daily chart
GET /api/v1/analytics/campaign/{id}        Per-campaign analytics
```

### Export
```
GET /api/v1/export/campaign/{id}/csv       Export CSV
GET /api/v1/export/campaign/{id}/excel     Export Excel
GET /api/v1/export/campaign/{id}/pdf       Export PDF report
```

---

## 🧪 Running Tests

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

## 🚀 Deployment

### Production Docker

```bash
# Set production env vars
export APP_ENV=production
export DEBUG=false
export SECRET_KEY=<strong-random-key>

docker compose up -d --build
```

### Running Database Migrations

```bash
# Inside backend container
docker compose exec backend alembic upgrade head
```

### Scaling Workers

```bash
docker compose up --scale celery_worker=4 -d
```

---

## 📸 Screenshots

> Register → Create Campaign → Upload contacts CSV → AI generates personalized emails → Launch → Track opens/clicks/replies → Analytics Dashboard → Export PDF report

---

## 📄 License

MIT
