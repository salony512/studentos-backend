# StudentOS — Deployment Guide
> Get your app live and shareable with your college mates in under 30 minutes.

---

## Option 1: Railway (Recommended — Free + PostgreSQL included)

Railway gives you a free PostgreSQL database + Python hosting. Perfect for college projects.

### Steps:
1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "StudentOS initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/studentos-backend.git
   git push -u origin main
   ```

2. **Deploy to Railway**
   - Go to [railway.app](https://railway.app) → Sign in with GitHub
   - Click **New Project** → **Deploy from GitHub repo**
   - Select your `studentos-backend` repo
   - Railway auto-detects Python and builds

3. **Add PostgreSQL**
   - In your Railway project → **+ New** → **Database** → **PostgreSQL**
   - Railway auto-injects `DATABASE_URL` environment variable

4. **Set environment variables** (Railway dashboard → Variables tab):
   ```
   SECRET_KEY=your-random-64-char-string-here
   DEBUG=False
   ALLOWED_ORIGINS=https://your-frontend-url.netlify.app
   ```

5. **Done!** Your API is live at `https://your-app.railway.app`
   - API docs: `https://your-app.railway.app/docs`

---

## Option 2: Render.com (Free tier — spins down after inactivity)

1. Push to GitHub (same as above)
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add a **PostgreSQL** database from the Render dashboard
7. Copy the `DATABASE_URL` from Render DB → paste into your Web Service env vars

---

## Option 3: Docker (Local network — share with hostel mates on same WiFi)

```bash
# Start everything with one command
docker-compose up --build -d

# Check it's running
curl http://localhost:8000/health

# Seed demo data
docker-compose exec api python scripts/seed.py

# Stop
docker-compose down
```

Your mates can access it at `http://YOUR_LOCAL_IP:8000`
Find your IP: `ipconfig` (Windows) or `ifconfig` (Linux/Mac)

---

## Frontend Deployment (Netlify — Free)

Your `index.html` frontend deploys to Netlify in 30 seconds:

1. Go to [netlify.com](https://netlify.com) → **Deploy** → Drag and drop your frontend folder
2. Done — you get a live URL like `https://studentos-xyz.netlify.app`
3. Update `BASE_URL` in `api.js` to your Railway/Render backend URL

---

## Connecting Frontend to Backend

In `api.js`, change line 1:
```js
// Development (local)
const BASE_URL = "http://localhost:8000";

// Production (replace with your Railway/Render URL)
const BASE_URL = "https://studentos-backend.railway.app";
```

In `index.html`, add this at the bottom of `<body>` to initialize:
```html
<script type="module">
  import api from './api.js';

  // Load dashboard on page load
  window.addEventListener('DOMContentLoaded', async () => {
    if (api.auth.isLoggedIn()) {
      const dash = await api.insights.getDashboard();
      document.querySelector('.nav-logo').textContent = `Hi, ${dash.user.name.split(' ')[0]}`;
    }

    // Wire up todo form
    document.getElementById('todoInput').addEventListener('keydown', async (e) => {
      if (e.key === 'Enter') {
        const val = e.target.value.trim();
        if (val) {
          await api.tasks.create(val);
          e.target.value = '';
          // Re-render todos from API
          const tasks = await api.tasks.getAll('pending');
          // update your UI...
        }
      }
    });
  });
</script>
```

---

## Environment Variable Reference

| Variable              | Required | Description                                |
|-----------------------|----------|--------------------------------------------|
| `DATABASE_URL`        | Yes      | PostgreSQL connection string               |
| `SECRET_KEY`          | Yes      | Min 32-char random string for JWT signing  |
| `DEBUG`               | No       | `True` for dev, `False` for prod           |
| `ALLOWED_ORIGINS`     | No       | Comma-separated list of frontend URLs      |
| `ANTHROPIC_API_KEY`   | No       | Enables AI-powered quotes (optional)       |

Generate a secure SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## API Endpoints Reference

| Method | Endpoint                        | Description                        |
|--------|---------------------------------|------------------------------------|
| POST   | `/api/auth/register`            | Create account                     |
| POST   | `/api/auth/login`               | Login → get JWT token              |
| GET    | `/api/auth/me`                  | Get current user profile           |
| GET    | `/api/academics/tasks`          | Get all tasks                      |
| POST   | `/api/academics/tasks`          | Create task                        |
| PATCH  | `/api/academics/tasks/{id}`     | Update task status/priority        |
| GET    | `/api/academics/cgpa`           | Compute live CGPA                  |
| GET    | `/api/academics/dayplan`        | Get AI-generated day schedule      |
| POST   | `/api/health/log`               | Submit daily health check-in       |
| GET    | `/api/health/insights`          | Get ML health correlations         |
| GET    | `/api/insights/procrastination` | Get drop-off probability + triggers|
| GET    | `/api/insights/motivation`      | Get personalized motivational quote|
| GET    | `/api/insights/projection`      | Get 90-day two-futures projection  |
| GET    | `/api/insights/dashboard`       | Full dashboard summary (1 call)    |
| POST   | `/api/mindfulness/gratitude`    | Log gratitude entries              |
| GET    | `/api/mindfulness/gratitude/themes` | AI gratitude theme analysis   |
| POST   | `/api/mindfulness/breath`       | Log breath session                 |

Full interactive docs at: `http://localhost:8000/docs`

---

## Share with Mates

Once deployed:
1. Share your Netlify frontend URL
2. Each mate registers at `/api/auth/register`
3. All data is private per user — JWT-protected
4. Demo account: `arjun@demo.com` / `demo1234` (after running seed.py)
