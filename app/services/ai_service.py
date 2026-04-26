"""
AI Service
───────────
Generates:
  - Personalized motivational quotes based on user's behavioral history
  - Daily schedule based on energy patterns, deadlines, mindfulness needs
  - 90-day projection (consistent vs current pattern)
  - Next-step skill suggestions

Uses Anthropic API if key is set; falls back to curated local content.
"""

import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, date

# ── Fallback quote pools (used when no API key set) ──────────────────────
QUOTES_BY_PATTERN = {
    "burst_crash": [
        "You stopped exactly here last week. This time, you go one step further. One. Step.",
        "The 3-day cycle is a habit, not a fate. Habits are choices. Make a different one today.",
        "Bursts feel heroic. Consistency wins. Pick the boring kind of excellence today.",
    ],
    "declining": [
        "Decline is the default when nobody's watching. You're watching. Change direction now.",
        "The distance between who you are and who you could be is exactly one consistent day.",
        "Your future self is already disappointed — unless you start right now.",
    ],
    "improving": [
        "You're trending up. Rare. Protect this momentum like your most valuable asset.",
        "Consistency compounds silently. What you're doing right now matters more than you know.",
        "Most people stop when it gets hard. You didn't. That's the entire game.",
    ],
    "steady": [
        "The boring kind of excellent is the rarest kind. You have it. Don't lose it.",
        "Mediocrity is loud. Excellence is quiet, daily, and invisible — until suddenly it isn't.",
        "Every day you show up when you don't feel like it, you widen the gap between you and average.",
    ],
    "default": [
        "Your CGPA is not your ceiling. Your consistency is. And consistency is a choice.",
        "The skill you skip today is the interview question you can't answer in six months.",
        "Sleep well. Drink water. Start before you feel ready. That's the whole system.",
        "What would the version of you from 6 months ago think of who you are today?",
        "You don't need motivation. You need a 10-minute start and to trust the momentum.",
    ],
}

async def get_motivational_quote(
    pattern: str = "default",
    user_name: str = "",
    streak: int = 0,
    api_key: str = "",
) -> Dict[str, str]:
    """Return a personalized quote."""
    if api_key:
        try:
            return await _ai_quote(pattern, user_name, streak, api_key)
        except Exception:
            pass  # Fall through to local

    pool = QUOTES_BY_PATTERN.get(pattern, QUOTES_BY_PATTERN["default"])
    quote = random.choice(pool)
    if user_name and random.random() > 0.5:
        quote = f"{user_name}, " + quote[0].lower() + quote[1:]

    streak_suffix = ""
    if streak >= 7:
        streak_suffix = f" ({streak}-day streak — don't break it.)"
    elif streak >= 3:
        streak_suffix = f" ({streak} days strong.)"

    return {
        "text": quote + streak_suffix,
        "author": "StudentOS coach · Based on your pattern",
    }

async def _ai_quote(pattern: str, user_name: str, streak: int, api_key: str) -> Dict[str, str]:
    import httpx
    prompt = (
        f"Generate ONE short, punchy, brutally honest motivational quote for a college student. "
        f"Their pattern: {pattern}. Name: {user_name or 'student'}. "
        f"Current streak: {streak} days. "
        f"Make it specific to their pattern — NOT generic. "
        f"Max 2 sentences. No hashtags. No emojis. Sound like a no-nonsense mentor."
    )
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 150, "messages": [{"role": "user", "content": prompt}]},
            timeout=8,
        )
    data = r.json()
    text = data["content"][0]["text"].strip().strip('"')
    return {"text": text, "author": "AI coach · Based on your pattern"}


def build_day_plan(
    tasks: List[Dict],
    energy_level: int = 7,
    sleep_hours: float = 7.0,
    target_date: Optional[date] = None,
) -> List[Dict]:
    """
    Build an optimal day schedule.
    Returns list of time slots with title, category, duration, priority.
    """
    schedule = []
    target_date = target_date or date.today()

    # Always add mindfulness bookends
    schedule.append({"time": "06:30", "title": "Morning intention + gratitude log", "category": "mindfulness", "duration_min": 5, "priority": "high"})

    # Peak energy tasks first (if energy >= 6, mornings are deep work)
    if energy_level >= 6 and sleep_hours >= 6:
        schedule.append({"time": "07:00", "title": "LeetCode / DSA practice", "category": "skills", "duration_min": 30, "priority": "high"})
        schedule.append({"time": "09:00", "title": "Deep work — hardest academic task", "category": "academics", "duration_min": 90, "priority": "high"})
    else:
        schedule.append({"time": "09:00", "title": "Easy review / revision", "category": "academics", "duration_min": 45, "priority": "medium"})

    schedule.append({"time": "10:30", "title": "4-7-8 breathing + nature break", "category": "mindfulness", "duration_min": 10, "priority": "medium"})

    # Inject pending high-priority tasks
    high_tasks = [t for t in tasks if t.get("priority") == "high" and t.get("status") == "pending"][:2]
    for i, task in enumerate(high_tasks):
        hour = 11 + i
        schedule.append({"time": f"{hour:02d}:00", "title": task["title"], "category": task.get("category", "academics"), "duration_min": 45, "priority": "high"})

    schedule.append({"time": "14:00", "title": "DBMS / subject revision", "category": "academics", "duration_min": 60, "priority": "medium"})
    schedule.append({"time": "16:00", "title": "Aptitude — 10 AMCAT problems", "category": "skills", "duration_min": 25, "priority": "medium"})
    schedule.append({"time": "17:00", "title": "Walk / physical activity", "category": "health", "duration_min": 20, "priority": "medium"})

    if energy_level >= 5:
        schedule.append({"time": "19:00", "title": "Skill reading / YouTube resource", "category": "skills", "duration_min": 30, "priority": "low"})

    schedule.append({"time": "21:30", "title": "Evening gratitude log", "category": "mindfulness", "duration_min": 5, "priority": "high"})
    schedule.append({"time": "22:00", "title": "Wind down — no screens", "category": "health", "duration_min": 30, "priority": "medium"})

    return sorted(schedule, key=lambda x: x["time"])


def compute_90_day_projection(
    current_cgpa: float,
    target_cgpa: float,
    current_streak: int,
    missed_days_last_7: int,
    skills_done: int,
) -> Dict[str, Any]:
    """
    Two futures: consistent path vs current pattern.
    """
    consistency_rate = max(0.1, 1 - (missed_days_last_7 / 7))
    consistent_rate  = 0.9  # 90% consistency

    # CGPA projection
    cgpa_consistent = min(10.0, current_cgpa + (target_cgpa - current_cgpa) * consistent_rate * 0.8)
    cgpa_current    = min(10.0, current_cgpa + (target_cgpa - current_cgpa) * consistency_rate * 0.3)

    # Skills
    skills_consistent = skills_done + int(90 / 7 * consistent_rate * 1.5)
    skills_current    = skills_done + int(90 / 7 * consistency_rate * 0.5)

    # Health score
    health_consistent = min(100, 50 + consistent_rate * 50)
    health_current    = min(100, 50 + consistency_rate * 30)

    # Streak
    streak_consistent = current_streak + int(90 * consistent_rate)
    streak_current    = max(0, current_streak - missed_days_last_7 * 2)

    return {
        "consistent": {
            "cgpa": round(cgpa_consistent, 1),
            "skills": skills_consistent,
            "health_score": int(health_consistent),
            "streak": streak_consistent,
            "label": "If you stay consistent",
        },
        "current": {
            "cgpa": round(cgpa_current, 1),
            "skills": skills_current,
            "health_score": int(health_current),
            "streak": streak_current,
            "label": "If pattern continues",
        },
        "days": 90,
        "message": (
            f"The gap between these two futures is just {int((consistent_rate - consistency_rate) * 100)}% more consistency. "
            f"That's roughly {int((consistent_rate - consistency_rate) * 90)} more days of showing up over the next 3 months."
        ),
    }
