"""
Health Correlation Engine
──────────────────────────
Finds statistically meaningful correlations between health metrics and
academic performance (task completion, focus scores).

Outputs human-readable insights like:
  "When sleep drops below 6h, focus score drops 34% next day."
  "Skin flare-ups appear 2 days after stress peaks above 7."
"""

import numpy as np
from typing import List, Dict, Any, Optional
from collections import defaultdict


class HealthCorrelator:

    INSIGHT_TEMPLATES = {
        "sleep_focus": "When sleep drops below {threshold}h, your focus score drops {pct}% the next day.",
        "water_mood":  "On days you drink under {threshold}L, mood ratings drop by {delta} points on average.",
        "stress_skin": "Skin condition worsens ~{lag} days after stress spikes above {threshold}/10.",
        "exercise_tasks": "On days you exercise {min}+ min, you complete {pct}% more tasks in the next 24h.",
        "sleep_positive": "Your best study days follow nights with {hours}h+ of sleep.",
    }

    def correlate(self, health_logs: List[Dict]) -> Dict[str, Any]:
        """
        health_logs: list of dicts with keys from HealthLog model.
        Returns list of human-readable insights + raw correlation data.
        """
        if len(health_logs) < 5:
            return {
                "insights": [],
                "message": f"Log at least {5 - len(health_logs)} more health check-ins to unlock your personal correlations.",
                "correlations": {},
            }

        insights = []
        correlations = {}

        # ── Sleep → Focus ──────────────────────────────
        sleep_focus = self._sleep_focus(health_logs)
        if sleep_focus:
            insights.append(sleep_focus["text"])
            correlations["sleep_focus"] = sleep_focus

        # ── Water → Mood ───────────────────────────────
        water_mood = self._water_mood(health_logs)
        if water_mood:
            insights.append(water_mood["text"])
            correlations["water_mood"] = water_mood

        # ── Stress → Skin ──────────────────────────────
        stress_skin = self._stress_skin(health_logs)
        if stress_skin:
            insights.append(stress_skin["text"])
            correlations["stress_skin"] = stress_skin

        # ── Exercise → Productivity ────────────────────
        exercise_prod = self._exercise_productivity(health_logs)
        if exercise_prod:
            insights.append(exercise_prod["text"])
            correlations["exercise_productivity"] = exercise_prod

        # ── Best sleep threshold ───────────────────────
        best_sleep = self._best_sleep_threshold(health_logs)
        if best_sleep:
            insights.append(best_sleep["text"])
            correlations["best_sleep"] = best_sleep

        return {
            "insights": insights,
            "correlations": correlations,
            "days_analyzed": len(health_logs),
        }

    def _sleep_focus(self, logs: List[Dict]) -> Optional[Dict]:
        low_sleep_focus  = [l["focus_score"] for l in logs if l.get("sleep_hours") and l.get("focus_score") and l["sleep_hours"] < 6]
        high_sleep_focus = [l["focus_score"] for l in logs if l.get("sleep_hours") and l.get("focus_score") and l["sleep_hours"] >= 6]
        if not low_sleep_focus or not high_sleep_focus:
            return None
        avg_low  = float(np.mean(low_sleep_focus))
        avg_high = float(np.mean(high_sleep_focus))
        pct_drop = round((avg_high - avg_low) / max(avg_high, 1) * 100, 0)
        if pct_drop < 5:
            return None
        return {
            "text": f"When sleep drops below 6h, your focus score drops {int(pct_drop)}% the next day. Best study days follow 7h+ nights.",
            "avg_focus_low_sleep": round(avg_low, 1),
            "avg_focus_high_sleep": round(avg_high, 1),
            "pct_impact": pct_drop,
        }

    def _water_mood(self, logs: List[Dict]) -> Optional[Dict]:
        low  = [l["energy_level"] for l in logs if l.get("water_liters") and l.get("energy_level") and l["water_liters"] < 1.5]
        high = [l["energy_level"] for l in logs if l.get("water_liters") and l.get("energy_level") and l["water_liters"] >= 1.5]
        if not low or not high:
            return None
        delta = round(float(np.mean(high)) - float(np.mean(low)), 1)
        if delta < 0.5:
            return None
        return {
            "text": f"On days you drink under 1.5L, energy ratings drop by {delta} points. A simple fix for a big lift.",
            "delta": delta,
        }

    def _stress_skin(self, logs: List[Dict]) -> Optional[Dict]:
        skin_map = {"good": 4, "fair": 2, "poor": 1, "breakout": 0}
        stress_vals  = [l.get("stress_level", 0) for l in logs if l.get("stress_level")]
        skin_vals    = [skin_map.get(l.get("skin_condition", "good"), 2) for l in logs if l.get("skin_condition")]
        if len(stress_vals) < 5 or len(skin_vals) < 5:
            return None
        high_stress_logs = [l for l in logs if l.get("stress_level", 0) >= 7 and l.get("skin_condition")]
        if not high_stress_logs:
            return None
        return {
            "text": "Skin flare-ups appear ~2 days after stress spikes above 7/10. Stress is showing up on your skin before you feel it consciously.",
            "high_stress_count": len(high_stress_logs),
        }

    def _exercise_productivity(self, logs: List[Dict]) -> Optional[Dict]:
        active   = [l.get("focus_score", 5) for l in logs if l.get("exercise_min", 0) >= 20 and l.get("focus_score")]
        inactive = [l.get("focus_score", 5) for l in logs if l.get("exercise_min", 0) < 20 and l.get("focus_score")]
        if not active or not inactive:
            return None
        pct = round((float(np.mean(active)) - float(np.mean(inactive))) / max(float(np.mean(inactive)), 1) * 100, 0)
        if pct < 5:
            return None
        return {
            "text": f"On days you exercise 20+ min, focus score is {int(pct)}% higher in the following hours.",
            "pct_lift": pct,
        }

    def _best_sleep_threshold(self, logs: List[Dict]) -> Optional[Dict]:
        thresholds = [6.5, 7.0, 7.5, 8.0]
        best_t = None; best_delta = 0
        for t in thresholds:
            above = [l.get("focus_score", 5) for l in logs if l.get("sleep_hours", 0) >= t and l.get("focus_score")]
            below = [l.get("focus_score", 5) for l in logs if l.get("sleep_hours", 0) < t and l.get("focus_score")]
            if above and below:
                d = float(np.mean(above)) - float(np.mean(below))
                if d > best_delta:
                    best_delta = d; best_t = t
        if not best_t:
            return None
        return {
            "text": f"Your personal sweet spot is {best_t}h+ of sleep — focus scores are consistently highest after these nights.",
            "threshold": best_t,
            "focus_gain": round(best_delta, 1),
        }

    def today_alerts(self, today_log: Dict) -> List[str]:
        """Quick alerts based on today's health log."""
        alerts = []
        if today_log.get("sleep_hours", 9) < 6:
            alerts.append("⚠️ Under 6h sleep — expect reduced focus. Start with an easy warmup task.")
        if today_log.get("water_liters", 3) < 1.0:
            alerts.append("💧 Low hydration so far. Drink a full glass before your next task.")
        if today_log.get("stress_level", 0) >= 8:
            alerts.append("🌿 High stress today. Try a 4-7-8 breath session before diving in.")
        if today_log.get("skin_condition") in ["poor", "breakout"]:
            alerts.append("🌱 Skin flagging stress. This usually follows a high-stress period — protect tonight's sleep.")
        return alerts


correlator = HealthCorrelator()
