# StudentOS — Backend + Database + ML

## Tech Stack
- **Backend**: FastAPI (Python) — async, fast, auto-docs at /docs
- **Database**: PostgreSQL + SQLAlchemy ORM + Alembic migrations
- **Auth**: JWT tokens (python-jose + bcrypt)
- **ML**: scikit-learn — procrastination pattern detector
- **Deploy**: Docker + docker-compose (one command deploy)

## Project Structure
```
studentos-backend/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings & env vars
│   ├── database.py          # DB connection & session
│   ├── api/
│   │   ├── auth.py          # Register / Login / JWT
│   │   ├── user.py          # User profile CRUD
│   │   ├── academics.py     # CGPA, tasks, exams
│   │   ├── health.py        # Sleep, mood, skin logs
│   │   ├── skills.py        # Skill roadmap & resources
│   │   ├── mindfulness.py   # Breath sessions, gratitude
│   │   └── insights.py      # ML predictions & insights
│   ├── models/
│   │   ├── user.py          # User DB model
│   │   ├── academics.py     # Academic DB models
│   │   ├── health.py        # Health DB models
│   │   ├── skills.py        # Skills DB models
│   │   └── mindfulness.py   # Mindfulness DB models
│   ├── services/
│   │   ├── auth_service.py  # JWT create/verify
│   │   └── ai_service.py    # Quote generation, insights
│   └── ml/
│       ├── procrastination.py  # Pattern detection model
│       └── health_correlator.py # Health-productivity ML
├── alembic/                 # DB migrations
├── scripts/
│   └── seed.py              # Seed demo data
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Quick Start (Local)

```bash
# 1. Clone and enter directory
cd studentos-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy env file and fill in values
cp .env.example .env

# 5. Start PostgreSQL (or use Docker)
docker-compose up -d db

# 6. Run DB migrations
alembic upgrade head

# 7. Seed demo data (optional)
python scripts/seed.py

# 8. Start the server
uvicorn app.main:app --reload --port 8000
```

## Deploy with Docker (one command)

```bash
docker-compose up --build -d
```

API docs available at: http://localhost:8000/docs

## Deploy to Railway / Render (Free)

1. Push this folder to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Add environment variables from .env.example
4. Add a PostgreSQL plugin
5. Done — Railway auto-deploys on every push
