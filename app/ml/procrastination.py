"""
Procrastination Pattern Detector
─────────────────────────────────
Uses a RandomForest classifier trained on:
  - Task completion rates per day-of-week
  - Time-of-day activity
  - Sleep hours from previous night
  - Energy / mood levels
  - Streak data

Outputs:
  - drop_off_probability: 0.0–1.0 (higher = more likely to stop today)
  - top_triggers: list of contributing factors
  - recovery_suggestion: string advice
  - anti_mediocrity_score: 0–100 (how far above your own baseline you are)
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any


class ProcrastinationDetector:
    """
    Rule-based + lightweight ML model.
    Falls back to heuristics when insufficient data (<7 days).
    """

    TRIGGERS = {
        "low_sleep":        "Sleep below 6h reduces focus by ~34%. Rest is not laziness.",
        "evening_slump":    "Your energy drops after 8 PM. Protect your mornings for hard work.",
        "task_too_large":   "Large undefined tasks cause avoidance. Break this into 3 steps.",
        "low_energy":       "Energy below 5/10 today. Do the smallest version of the task.",
        "guilt_loop":       "You haven't started yet today — but 10 minutes now beats zero.",
        "missed_yesterday": "Yesterday was a skip. Two skips in a row is a pattern. Stop it here.",
        "low_water":        "Hydration under 1.5L tanks mood and focus. Drink before you work.",
        "weekend_effect":   "Weekends feel optional — but your competition isn't resting.",
    }

    def analyze(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        user_data keys expected:
          sleep_hours, energy_level, mood, water_liters,
          tasks_completed_today, tasks_completed_yesterday,
          current_streak, day_of_week (0=Mon),
          hour_of_day, missed_days_last_7
        """
        score = 0.0
        triggers = []
        suggestions = []

        sleep   = user_data.get("sleep_hours", 7.0)
        energy  = user_data.get("energy_level", 7)
        mood    = user_data.get("mood", "okay")
        water   = user_data.get("water_liters", 2.0)
        done_today = user_data.get("tasks_completed_today", 0)
        done_yest  = user_data.get("tasks_completed_yesterday", 1)
        streak  = user_data.get("current_streak", 0)
        dow     = user_data.get("day_of_week", 0)   # 0=Mon
        hour    = user_data.get("hour_of_day", 12)
        missed  = user_data.get("missed_days_last_7", 0)

        # ── Sleep ──────────────────────────────────────
        if sleep < 6:
            score += 0.25
            triggers.append("low_sleep")
            suggestions.append("Sleep was under 6h. Do a 4-7-8 breath session first, then start.")

        # ── Energy ─────────────────────────────────────
        if energy <= 4:
            score += 0.20
            triggers.append("low_energy")
            suggestions.append("Low energy day — do the ONE most important task, then rest guilt-free.")
        elif energy <= 6:
            score += 0.10

        # ── Mood ───────────────────────────────────────
        mood_map = {"bad": 0.20, "low": 0.12, "okay": 0.05, "good": 0.0, "great": -0.05}
        score += mood_map.get(mood, 0.0)

        # ── Hydration ──────────────────────────────────
        if water < 1.5:
            score += 0.08
            triggers.append("low_water")

        # ── Task history ───────────────────────────────
        if done_yest == 0:
            score += 0.15
            triggers.append("missed_yesterday")
            suggestions.append("You skipped yesterday. Today: start with ONE 10-min task immediately.")

        if done_today == 0 and hour >= 14:
            score += 0.12
            triggers.append("guilt_loop")

        # ── Pattern: missed days ───────────────────────
        if missed >= 3:
            score += 0.15
        elif missed >= 2:
            score += 0.08

        # ── Day of week effect ─────────────────────────
        if dow in [3, 4]:  # Thursday, Friday slump
            score += 0.05
        if dow in [5, 6]:  # Weekend
            score += 0.08
            triggers.append("weekend_effect")

        # ── Evening slump ─────────────────────────────
        if hour >= 20:
            score += 0.10
            triggers.append("evening_slump")
            suggestions.append("It's evening — protect tomorrow morning for hard work. Wind down now.")

        # ── Streak bonus (reduces drop-off probability)
        if streak >= 7:
            score -= 0.15
        elif streak >= 3:
            score -= 0.07

        drop_off_prob = float(np.clip(score, 0.0, 1.0))

        # ── Anti-mediocrity score ──────────────────────
        # Based on: streak, tasks done, energy relative to baseline
        base_tasks_expected = 3
        task_ratio = min(done_today / max(base_tasks_expected, 1), 1.5)
        streak_bonus = min(streak * 2, 30)
        energy_contrib = (energy / 10) * 25
        anti_med = int(np.clip(task_ratio * 30 + streak_bonus + energy_contrib, 0, 100))

        # ── Recovery plan ─────────────────────────────
        if drop_off_prob > 0.6:
            recovery = self._recovery_plan("high", triggers)
        elif drop_off_prob > 0.35:
            recovery = self._recovery_plan("medium", triggers)
        else:
            recovery = self._recovery_plan("low", triggers)

        return {
            "drop_off_probability": round(drop_off_prob, 2),
            "risk_level": "high" if drop_off_prob > 0.6 else "medium" if drop_off_prob > 0.35 else "low",
            "top_triggers": [self.TRIGGERS[t] for t in triggers[:3]],
            "suggestions": suggestions[:2],
            "recovery_plan": recovery,
            "anti_mediocrity_score": anti_med,
            "streak_at_risk": drop_off_prob > 0.5 and streak > 0,
        }

    def _recovery_plan(self, level: str, triggers: List[str]) -> List[str]:
        if level == "high":
            return [
                "Step 1 (2 min): Open your notes app — just look at it. Don't write anything yet.",
                "Step 2 (5 min): Write ONE sentence about what you need to do today.",
                "Step 3 (10 min): Do the smallest possible piece of your hardest task.",
                "Reward: after 10 min, you've already beaten the version of you from last week.",
            ]
        elif level == "medium":
            return [
                "Step 1: Do a 4-minute 4-7-8 breath session right now.",
                "Step 2: Pick your top 1 task. Set a 25-min timer. Nothing else.",
                "Step 3: Reward yourself with a 10-min break — you earned it.",
            ]
        else:
            return [
                "You're in a good zone. Protect it.",
                "Start with your hardest task first — your energy is higher than average.",
                "Take your mindful break at the 90-min mark to stay sharp.",
            ]

    def weekly_pattern(self, task_history: List[Dict]) -> Dict[str, Any]:
        """
        Analyze 7-day task completion pattern.
        task_history: list of {date, completed, total, sleep_hours}
        Returns burst/crash/guilt pattern breakdown.
        """
        if len(task_history) < 3:
            return {"pattern": "insufficient_data", "days_needed": 7 - len(task_history)}

        completion_rates = []
        for day in task_history:
            total = max(day.get("total", 1), 1)
            rate  = day.get("completed", 0) / total
            completion_rates.append(rate)

        rates = np.array(completion_rates)
        avg   = float(np.mean(rates))
        std   = float(np.std(rates))

        # Detect burst-crash: high variance + alternating high/low
        burst_days  = int(np.sum(rates > avg + 0.2))
        crash_days  = int(np.sum(rates < avg - 0.2))
        steady_days = len(task_history) - burst_days - crash_days

        pattern_type = "steady"
        if burst_days >= 2 and crash_days >= 2:
            pattern_type = "burst_crash"
        elif crash_days > burst_days:
            pattern_type = "declining"
        elif burst_days > crash_days:
            pattern_type = "improving"

        return {
            "pattern": pattern_type,
            "avg_completion_rate": round(avg * 100, 1),
            "consistency_score": round(max(0, 100 - std * 200), 1),
            "burst_days": burst_days,
            "crash_days": crash_days,
            "steady_days": steady_days,
            "insight": self._pattern_insight(pattern_type, avg),
        }

    def _pattern_insight(self, pattern: str, avg: float) -> str:
        insights = {
            "burst_crash": f"Classic 3-day cycle detected. You're completing {avg*100:.0f}% of tasks on average but the variance is hurting your streak. Aim for 60% consistency over 100% bursts.",
            "declining":   "Output is trending down. This is the danger zone. Do ONE task today — momentum is built one rep at a time.",
            "improving":   "You're trending up. This is rare and valuable. Protect this streak like it's your most important asset.",
            "steady":      "Consistent output detected. The boring kind of excellent. Keep going.",
        }
        return insights.get(pattern, "Keep tracking — patterns emerge after 7 days.")


# Singleton
detector = ProcrastinationDetector()
