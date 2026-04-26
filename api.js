/**
 * StudentOS — Frontend API Connector
 * ────────────────────────────────────
 * Drop this into your frontend folder and import it.
 * It connects the HTML/JS frontend to your FastAPI backend.
 *
 * Usage:
 *   import api from './api.js'
 *   await api.auth.login('email@example.com', 'password')
 *   await api.tasks.getAll()
 *   await api.insights.getDashboard()
 */

const BASE_URL = "http://localhost:8000";// Change to your deployed URL

// ── Token management ──────────────────────────────────────────────────────
const token = {
  get: () => localStorage.getItem("studentos_token"),
  set: (t) => localStorage.setItem("studentos_token", t),
  clear: () => localStorage.removeItem("studentos_token"),
};

// ── Core fetch wrapper ────────────────────────────────────────────────────
async function req(method, path, body = null, auth = true) {
  const headers = { "Content-Type": "application/json" };
  if (auth && token.get()) {
    headers["Authorization"] = `Bearer ${token.get()}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : null,
  });

  if (res.status === 401) {
    token.clear();
    window.location.href = "/login.html";
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }

  if (res.status === 204) return null;
  return res.json();
}

// ── Auth form helper (login uses form data not JSON) ──────────────────────
async function loginReq(email, password) {
  const form = new FormData();
  form.append("username", email);
  form.append("password", password);
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error("Invalid credentials");
  return res.json();
}

// ── API modules ───────────────────────────────────────────────────────────
const api = {

  // ── Auth ────────────────────────────────────────────────────────────────
  auth: {
    async register(name, email, password, college, branch, year, targetRole) {
      const data = await req("POST", "/api/auth/register", {
        name, email, password, college, branch, year,
        target_role: targetRole,
      }, false);
      token.set(data.access_token);
      return data;
    },

    async login(email, password) {
      const data = await loginReq(email, password);
      token.set(data.access_token);
      return data;
    },

    logout() {
      token.clear();
      window.location.href = "/";
    },

    async me() {
      return req("GET", "/api/auth/me");
    },

    async updateProfile(updates) {
      return req("PATCH", "/api/auth/me", updates);
    },

    isLoggedIn() {
      return !!token.get();
    },
  },

  // ── Tasks ────────────────────────────────────────────────────────────────
  tasks: {
    getAll(status, category) {
      const params = new URLSearchParams();
      if (status) params.set("status", status);
      if (category) params.set("category", category);
      return req("GET", `/api/academics/tasks?${params}`);
    },
    create(title, category = "academics", priority = "medium", dueDate = null) {
      return req("POST", "/api/academics/tasks", { title, category, priority, due_date: dueDate });
    },
    update(id, updates) {
      return req("PATCH", `/api/academics/tasks/${id}`, updates);
    },
    markDone(id) {
      return req("PATCH", `/api/academics/tasks/${id}`, { status: "done" });
    },
    delete(id) {
      return req("DELETE", `/api/academics/tasks/${id}`);
    },
  },

  // ── Academics ────────────────────────────────────────────────────────────
  academics: {
    getCGPA() {
      return req("GET", "/api/academics/cgpa");
    },
    getSubjects() {
      return req("GET", "/api/academics/subjects");
    },
    addSubject(name, credits, marks, maxMarks, semester, examDate) {
      return req("POST", "/api/academics/subjects", {
        name, credits, current_marks: marks, max_marks: maxMarks, semester, exam_date: examDate,
      });
    },
    getExams() {
      return req("GET", "/api/academics/exams");
    },
    addExam(type, date, score, notes) {
      return req("POST", "/api/academics/exams", { exam_type: type, exam_date: date, score, notes });
    },
    getDayPlan() {
      return req("GET", "/api/academics/dayplan");
    },
  },

  // ── Health ───────────────────────────────────────────────────────────────
  health: {
    logToday(data) {
      return req("POST", "/api/health/log", data);
    },
    getToday() {
      return req("GET", "/api/health/today");
    },
    getLogs(limit = 30) {
      return req("GET", `/api/health/logs?limit=${limit}`);
    },
    getInsights() {
      return req("GET", "/api/health/insights");
    },
    logMood(mood, note) {
      return req("POST", "/api/health/mood", { mood, note });
    },
    getMoodHistory() {
      return req("GET", "/api/health/mood/history");
    },
  },

  // ── Skills ───────────────────────────────────────────────────────────────
  skills: {
    getAll(track) {
      const params = track ? `?track=${track}` : "";
      return req("GET", `/api/skills/${params}`);
    },
    updateProgress(skillId, updates) {
      return req("POST", `/api/skills/${skillId}/progress`, updates);
    },
    logMinutes(skillId, minutes) {
      return req("POST", `/api/skills/${skillId}/progress`, { minutes_today: minutes });
    },
    markInProgress(skillId) {
      return req("POST", `/api/skills/${skillId}/progress`, { status: "in_progress" });
    },
    markDone(skillId) {
      return req("POST", `/api/skills/${skillId}/progress`, { status: "done" });
    },
  },

  // ── Mindfulness ──────────────────────────────────────────────────────────
  mindfulness: {
    logGratitude(entry1, entry2, entry3, moodAfter) {
      return req("POST", "/api/mindfulness/gratitude", { entry1, entry2, entry3, mood_after: moodAfter });
    },
    getGratitude(limit = 10) {
      return req("GET", `/api/mindfulness/gratitude?limit=${limit}`);
    },
    getGratitudeThemes() {
      return req("GET", "/api/mindfulness/gratitude/themes");
    },
    logBreath(completed, technique = "4-7-8", cycles = 4, durationS, moodBefore, moodAfter) {
      return req("POST", "/api/mindfulness/breath", {
        completed, technique, cycles, duration_s: durationS,
        mood_before: moodBefore, mood_after: moodAfter,
      });
    },
    getBreathStats() {
      return req("GET", "/api/mindfulness/breath/stats");
    },
    setIntention(intention) {
      return req("POST", "/api/mindfulness/intention", { intention });
    },
    getTodayIntention() {
      return req("GET", "/api/mindfulness/intention/today");
    },
  },

  // ── Insights (ML) ────────────────────────────────────────────────────────
  insights: {
    getProcrastination() {
      return req("GET", "/api/insights/procrastination");
    },
    getWeeklyPattern() {
      return req("GET", "/api/insights/weekly-pattern");
    },
    getMotivation() {
      return req("GET", "/api/insights/motivation");
    },
    getProjection() {
      return req("GET", "/api/insights/projection");
    },
    getDashboard() {
      return req("GET", "/api/insights/dashboard");
    },
  },
};

export default api;

// ── Quick integration example ──────────────────────────────────────────────
/*

EXAMPLE: Wire up the login form in your HTML

import api from './api.js';

document.getElementById('loginForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const pass  = document.getElementById('password').value;
  try {
    await api.auth.login(email, pass);
    window.location.href = '/dashboard';
  } catch (err) {
    alert('Login failed: ' + err.message);
  }
});

EXAMPLE: Load dashboard data

const dash = await api.insights.getDashboard();
document.getElementById('userName').textContent = dash.user.name;
document.getElementById('doneTasks').textContent = dash.today.done_tasks;

EXAMPLE: Log a health check-in

await api.health.logToday({
  sleep_hours: 7.0,
  energy_level: 8,
  water_liters: 2.0,
  stress_level: 4,
  mood: 'good',
  skin_condition: 'good',
  focus_score: 7,
});

EXAMPLE: Complete the breath session

await api.mindfulness.logBreath(
  true,         // completed
  '4-7-8',      // technique
  4,            // cycles
  240,          // duration in seconds
  'okay',       // mood before
  'good',       // mood after
);

EXAMPLE: Get procrastination analysis

const analysis = await api.insights.getProcrastination();
console.log(analysis.drop_off_probability);  // 0.0–1.0
console.log(analysis.anti_mediocrity_score); // 0–100
console.log(analysis.recovery_plan);         // array of steps
console.log(analysis.top_triggers);          // array of strings

*/
