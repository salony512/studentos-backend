from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta
from app.database import get_db
from app.models.user import User
from app.models.academics import Task
from app.models.health import HealthLog, MoodLog
from app.models.skills import SkillProgress
from app.services.auth_service import get_current_user
from app.services.ai_service import get_motivational_quote, compute_90_day_projection
from app.ml.procrastination import detector
from app.config import settings

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get("/procrastination")
async def procrastination_analysis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Full procrastination pattern analysis for current user."""
    now = datetime.utcnow()

    # Tasks completed today
    today_start = now.replace(hour=0, minute=0, second=0)
    r_today = await db.execute(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status == "done",
            Task.completed_at >= today_start,
        )
    )
    done_today = r_today.scalar() or 0

    # Tasks completed yesterday
    yest_start = today_start - timedelta(days=1)
    r_yest = await db.execute(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id,
            Task.status == "done",
            Task.completed_at >= yest_start,
            Task.completed_at < today_start,
        )
    )
    done_yest = r_yest.scalar() or 0

    # Latest health log
    r_health = await db.execute(
        select(HealthLog)
        .where(HealthLog.user_id == current_user.id)
        .order_by(desc(HealthLog.log_date))
        .limit(1)
    )
    health = r_health.scalar_one_or_none()

    # Streak calculation (consecutive days with ≥1 completed task)
    r_all = await db.execute(
        select(Task.completed_at)
        .where(Task.user_id == current_user.id, Task.status == "done")
        .order_by(desc(Task.completed_at))
    )
    completed_dates = {t.date() for t in (r_all.scalars().all() or [])}
    streak = 0
    check = now.date()
    while check in completed_dates:
        streak += 1
        check -= timedelta(days=1)

    # Missed days in last 7
    missed = sum(
        1 for i in range(1, 8)
        if (now.date() - timedelta(days=i)) not in completed_dates
    )

    user_data = {
        "sleep_hours":              health.sleep_hours if health else 7.0,
        "energy_level":             health.energy_level if health else 7,
        "mood":                     health.mood if health else "okay",
        "water_liters":             health.water_liters if health else 2.0,
        "tasks_completed_today":    done_today,
        "tasks_completed_yesterday":done_yest,
        "current_streak":           streak,
        "day_of_week":              now.weekday(),
        "hour_of_day":              now.hour,
        "missed_days_last_7":       missed,
    }

    analysis = detector.analyze(user_data)
    analysis["streak"] = streak
    analysis["done_today"] = done_today
    return analysis


@router.get("/weekly-pattern")
async def weekly_pattern(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """7-day burst/crash pattern analysis."""
    now = datetime.utcnow()
    history = []
    for i in range(7):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0)
        day_end   = day_start + timedelta(days=1)

        r_done = await db.execute(
            select(func.count(Task.id)).where(
                Task.user_id == current_user.id,
                Task.status == "done",
                Task.completed_at >= day_start,
                Task.completed_at < day_end,
            )
        )
        r_total = await db.execute(
            select(func.count(Task.id)).where(
                Task.user_id == current_user.id,
                Task.created_at >= day_start,
                Task.created_at < day_end,
            )
        )
        r_health = await db.execute(
            select(HealthLog.sleep_hours).where(
                HealthLog.user_id == current_user.id,
                HealthLog.log_date >= day_start,
                HealthLog.log_date < day_end,
            ).limit(1)
        )
        sleep = r_health.scalar_one_or_none()
        history.append({
            "date": day_start.date().isoformat(),
            "completed": r_done.scalar() or 0,
            "total":     max(r_total.scalar() or 1, 1),
            "sleep_hours": sleep or 7.0,
        })

    return detector.weekly_pattern(history)


@router.get("/motivation")
async def daily_motivation(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get personalized motivational quote + context."""
    # Get pattern
    now = datetime.utcnow()
    r_all = await db.execute(
        select(Task.completed_at).where(
            Task.user_id == current_user.id, Task.status == "done"
        ).order_by(desc(Task.completed_at))
    )
    dates = {t.date() for t in (r_all.scalars().all() or [])}
    streak = 0
    check = now.date()
    while check in dates:
        streak += 1
        check -= timedelta(days=1)

    missed = sum(1 for i in range(1, 8) if (now.date() - timedelta(days=i)) not in dates)
    if missed >= 3:
        pattern = "burst_crash"
    elif missed >= 5:
        pattern = "declining"
    elif streak >= 5:
        pattern = "improving"
    else:
        pattern = "steady"

    quote = await get_motivational_quote(
        pattern=pattern,
        user_name=current_user.name.split()[0] if current_user.name else "",
        streak=streak,
        api_key=settings.ANTHROPIC_API_KEY,
    )
    return {**quote, "streak": streak, "pattern": pattern}


@router.get("/projection")
async def future_projection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """90-day two-futures projection."""
    now = datetime.utcnow()
    r_all = await db.execute(
        select(Task.completed_at).where(Task.user_id == current_user.id, Task.status == "done")
        .order_by(desc(Task.completed_at))
    )
    dates = {t.date() for t in (r_all.scalars().all() or [])}
    streak = 0; check = now.date()
    while check in dates:
        streak += 1; check -= timedelta(days=1)
    missed = sum(1 for i in range(1, 8) if (now.date() - timedelta(days=i)) not in dates)

    r_skills = await db.execute(
        select(func.count(SkillProgress.id)).where(
            SkillProgress.user_id == current_user.id,
            SkillProgress.status == "done",
        )
    )
    skills_done = r_skills.scalar() or 0

    return compute_90_day_projection(
        current_cgpa  = current_user.current_cgpa or 7.0,
        target_cgpa   = current_user.target_cgpa or 8.5,
        current_streak= streak,
        missed_days_last_7 = missed,
        skills_done   = skills_done,
    )


@router.get("/dashboard")
async def dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Single endpoint for the full dashboard — reduces frontend API calls."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0)

    # Pending tasks
    r_tasks = await db.execute(
        select(Task).where(Task.user_id == current_user.id, Task.status == "pending")
        .order_by(Task.priority.desc()).limit(5)
    )
    tasks = r_tasks.scalars().all()

    # Today's health log
    r_health = await db.execute(
        select(HealthLog).where(HealthLog.user_id == current_user.id)
        .order_by(desc(HealthLog.log_date)).limit(1)
    )
    health = r_health.scalar_one_or_none()

    # Done today count
    r_done = await db.execute(
        select(func.count(Task.id)).where(
            Task.user_id == current_user.id, Task.status == "done",
            Task.completed_at >= today_start,
        )
    )
    done_today = r_done.scalar() or 0

    return {
        "user": {"name": current_user.name, "cgpa": current_user.current_cgpa, "target_role": current_user.target_role},
        "today": {
            "done_tasks": done_today,
            "pending_tasks": len(tasks),
            "health_logged": health is not None,
            "energy": health.energy_level if health else None,
            "mood": health.mood if health else None,
        },
        "pending_tasks": [{"id": t.id, "title": t.title, "priority": t.priority, "category": t.category} for t in tasks],
    }
