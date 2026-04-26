from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.mindfulness import GratitudeLog, BreathSession, DailyIntention
from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/api/mindfulness", tags=["mindfulness"])

class GratitudeCreate(BaseModel):
    entry1:     Optional[str] = None
    entry2:     Optional[str] = None
    entry3:     Optional[str] = None
    mood_after: Optional[str] = None

class BreathCreate(BaseModel):
    technique:   str = "4-7-8"
    cycles:      int = 4
    duration_s:  Optional[int] = None
    completed:   bool = False
    mood_before: Optional[str] = None
    mood_after:  Optional[str] = None

class IntentionCreate(BaseModel):
    intention: str


@router.post("/gratitude", status_code=201)
async def log_gratitude(
    body: GratitudeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = GratitudeLog(user_id=current_user.id, **body.model_dump())
    db.add(log)
    await db.flush()
    return {"id": log.id, "message": "Gratitude logged. Small wins compound."}


@router.get("/gratitude")
async def get_gratitude(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GratitudeLog)
        .where(GratitudeLog.user_id == current_user.id)
        .order_by(desc(GratitudeLog.logged_at))
        .limit(limit)
    )
    logs = result.scalars().all()
    return [{
        "id": l.id, "entry1": l.entry1, "entry2": l.entry2, "entry3": l.entry3,
        "mood_after": l.mood_after, "logged_at": l.logged_at,
    } for l in logs]


@router.get("/gratitude/themes")
async def gratitude_themes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Simple keyword frequency across all entries."""
    result = await db.execute(
        select(GratitudeLog).where(GratitudeLog.user_id == current_user.id)
    )
    logs = result.scalars().all()
    all_text = " ".join(
        f"{l.entry1 or ''} {l.entry2 or ''} {l.entry3 or ''}"
        for l in logs
    ).lower()
    theme_keywords = {
        "health":     ["sleep", "water", "exercise", "walk", "eat", "rest"],
        "academics":  ["study", "exam", "class", "lecture", "grade", "marks", "cgpa"],
        "skills":     ["code", "leetcode", "project", "skill", "learn", "practice"],
        "people":     ["friend", "family", "professor", "mate", "helped", "team"],
        "mindset":    ["focus", "consistent", "streak", "motivated", "calm", "peace"],
    }
    theme_counts = {theme: sum(all_text.count(kw) for kw in kws) for theme, kws in theme_keywords.items()}
    top = sorted(theme_counts.items(), key=lambda x: x[1], reverse=True)
    return {
        "top_themes": [{"theme": t, "count": c} for t, c in top if c > 0],
        "total_entries": len(logs),
        "insight": f"You most frequently feel grateful for things related to '{top[0][0]}'. That's your energy source." if top and top[0][1] > 0 else "Keep logging — themes emerge after a week.",
    }


@router.post("/breath", status_code=201)
async def log_breath_session(
    body: BreathCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session = BreathSession(user_id=current_user.id, **body.model_dump())
    db.add(session)
    await db.flush()
    msg = "Session complete. Notice how you feel — that calm is your baseline." if body.completed else "Partial session saved. Any breathing is better than none."
    return {"id": session.id, "message": msg}


@router.get("/breath/stats")
async def breath_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(BreathSession).where(BreathSession.user_id == current_user.id)
    )
    sessions = result.scalars().all()
    completed = [s for s in sessions if s.completed]
    total_min = sum(s.duration_s or 0 for s in completed) // 60
    return {
        "total_sessions": len(sessions),
        "completed_sessions": len(completed),
        "total_minutes": total_min,
        "insight": f"{total_min} minutes of intentional breathing. Your nervous system thanks you." if total_min > 0 else "Start your first session below.",
    }


@router.post("/intention", status_code=201)
async def set_intention(
    body: IntentionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    intention = DailyIntention(user_id=current_user.id, intention=body.intention)
    db.add(intention)
    await db.flush()
    return {"id": intention.id, "message": "Intention set. Let this guide your day."}


@router.get("/intention/today")
async def today_intention(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DailyIntention)
        .where(DailyIntention.user_id == current_user.id)
        .order_by(desc(DailyIntention.date))
        .limit(1)
    )
    intention = result.scalar_one_or_none()
    if not intention:
        return {"set": False, "prompt": "What's the one thing that would make today feel successful?"}
    return {"set": True, "intention": intention.intention, "date": intention.date}
