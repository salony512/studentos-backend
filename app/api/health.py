from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.health import HealthLog, MoodLog
from app.models.user import User
from app.services.auth_service import get_current_user
from app.ml.health_correlator import correlator

router = APIRouter(prefix="/api/health", tags=["health"])

class HealthLogCreate(BaseModel):
    sleep_hours:    Optional[float] = None
    sleep_quality:  Optional[int]   = None
    water_liters:   Optional[float] = None
    exercise_min:   Optional[int]   = None
    steps:          Optional[int]   = None
    stress_level:   Optional[int]   = None
    energy_level:   Optional[int]   = None
    skin_condition: Optional[str]   = None
    skin_score:     Optional[int]   = None
    mood:           Optional[str]   = None
    focus_score:    Optional[int]   = None
    notes:          Optional[str]   = None

class MoodLogCreate(BaseModel):
    mood: str
    note: Optional[str] = None


@router.post("/log", status_code=201)
async def log_health(
    body: HealthLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = HealthLog(user_id=current_user.id, **body.model_dump())
    db.add(log)
    await db.flush()

    # Immediate alerts
    alerts = correlator.today_alerts(body.model_dump())
    return {"id": log.id, "alerts": alerts, "message": "Health log saved"}


@router.get("/logs")
async def get_health_logs(
    limit: int = 30,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthLog)
        .where(HealthLog.user_id == current_user.id)
        .order_by(desc(HealthLog.log_date))
        .limit(limit)
    )
    logs = result.scalars().all()
    return [_log_dict(l) for l in logs]


@router.get("/today")
async def today_health(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from sqlalchemy import func, cast, Date
    result = await db.execute(
        select(HealthLog)
        .where(HealthLog.user_id == current_user.id)
        .order_by(desc(HealthLog.log_date))
        .limit(1)
    )
    log = result.scalar_one_or_none()
    if not log:
        return {"logged": False, "message": "No health log today. Take 2 minutes to check in."}
    alerts = correlator.today_alerts(_log_dict(log))
    return {"logged": True, "log": _log_dict(log), "alerts": alerts}


@router.get("/insights")
async def health_insights(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(HealthLog)
        .where(HealthLog.user_id == current_user.id)
        .order_by(desc(HealthLog.log_date))
        .limit(60)
    )
    logs = [_log_dict(l) for l in result.scalars().all()]
    return correlator.correlate(logs)


@router.post("/mood", status_code=201)
async def log_mood(
    body: MoodLogCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    log = MoodLog(user_id=current_user.id, **body.model_dump())
    db.add(log)
    await db.flush()
    return {"id": log.id, "message": "Mood logged"}


@router.get("/mood/history")
async def mood_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(MoodLog).where(MoodLog.user_id == current_user.id).order_by(desc(MoodLog.logged_at)).limit(limit)
    )
    return result.scalars().all()


def _log_dict(l: HealthLog) -> dict:
    return {
        "id": l.id, "sleep_hours": l.sleep_hours, "sleep_quality": l.sleep_quality,
        "water_liters": l.water_liters, "exercise_min": l.exercise_min,
        "stress_level": l.stress_level, "energy_level": l.energy_level,
        "skin_condition": l.skin_condition, "mood": l.mood,
        "focus_score": l.focus_score, "log_date": l.log_date,
    }
