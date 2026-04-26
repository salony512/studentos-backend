from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.skills import Skill, SkillProgress
from app.models.user import User
from app.services.auth_service import get_current_user
import json

router = APIRouter(prefix="/api/skills", tags=["skills"])

# Seed skills (added on first run)
SEED_SKILLS = [
    {"name": "Data Structures & Algorithms", "category": "DSA", "track": "Developer", "order_in_track": 1,
     "description": "Arrays, linked lists, trees, graphs, recursion, dynamic programming.",
     "resources": json.dumps([
         {"title": "Striver's SDE Sheet", "url": "https://takeuforward.org/interviews/strivers-sde-sheet-top-coding-interview-problems/", "type": "list"},
         {"title": "NeetCode 150", "url": "https://neetcode.io/practice", "type": "platform"},
         {"title": "Abdul Bari DSA (YouTube)", "url": "https://youtube.com/@abdul_bari", "type": "video"},
     ])},
    {"name": "System Design", "category": "System Design", "track": "Developer", "order_in_track": 2,
     "description": "Load balancing, caching, databases, microservices, scalability.",
     "resources": json.dumps([
         {"title": "System Design Primer (GitHub)", "url": "https://github.com/donnemartin/system-design-primer", "type": "github"},
         {"title": "Gaurav Sen (YouTube)", "url": "https://youtube.com/@gkcs", "type": "video"},
     ])},
    {"name": "DBMS & SQL", "category": "DBMS", "track": "Developer", "order_in_track": 3,
     "description": "Joins, indexing, normalization, transactions, query optimization.",
     "resources": json.dumps([
         {"title": "NPTEL DBMS", "url": "https://nptel.ac.in/courses/106105175", "type": "course"},
         {"title": "IndiaBix SQL", "url": "https://www.indiabix.com/sql/questions-and-answers/", "type": "practice"},
     ])},
    {"name": "Aptitude & Reasoning", "category": "Aptitude", "track": "All", "order_in_track": 1,
     "description": "Quantitative, verbal, logical reasoning for AMCAT, TCS, Infosys, Wipro.",
     "resources": json.dumps([
         {"title": "IndiaBix Aptitude", "url": "https://www.indiabix.com/aptitude/questions-and-answers/", "type": "practice"},
         {"title": "Freshersworld AMCAT prep", "url": "https://www.freshersworld.com/amcat-question-papers", "type": "practice"},
     ])},
    {"name": "Full Stack Web Dev", "category": "Development", "track": "Developer", "order_in_track": 4,
     "description": "HTML, CSS, JavaScript, React, Node.js, REST APIs, deployment.",
     "resources": json.dumps([
         {"title": "The Odin Project", "url": "https://www.theodinproject.com", "type": "course"},
         {"title": "FreeCodeCamp", "url": "https://www.freecodecamp.org", "type": "course"},
     ])},
]


@router.get("/")
async def get_all_skills(
    track: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all skills with user's progress attached."""
    await _ensure_seed_skills(db)

    q = select(Skill)
    if track:
        q = q.where((Skill.track == track) | (Skill.track == "All"))
    result = await db.execute(q.order_by(Skill.order_in_track))
    skills = result.scalars().all()

    # Get user progress for each skill
    r_progress = await db.execute(
        select(SkillProgress).where(SkillProgress.user_id == current_user.id)
    )
    progress_map = {p.skill_id: p for p in r_progress.scalars().all()}

    return [{
        "id": s.id, "name": s.name, "category": s.category,
        "track": s.track, "description": s.description,
        "resources": json.loads(s.resources) if s.resources else [],
        "order": s.order_in_track,
        "progress": {
            "status": progress_map[s.id].status if s.id in progress_map else "not_started",
            "pct": progress_map[s.id].progress_pct if s.id in progress_map else 0,
            "streak": progress_map[s.id].streak_days if s.id in progress_map else 0,
            "minutes_today": progress_map[s.id].minutes_today if s.id in progress_map else 0,
        } if s.id in progress_map else None,
    } for s in skills]


@router.post("/{skill_id}/progress")
async def update_skill_progress(
    skill_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update progress on a skill. Body: {status, progress_pct, minutes_today, notes}"""
    result = await db.execute(
        select(SkillProgress).where(
            SkillProgress.skill_id == skill_id,
            SkillProgress.user_id == current_user.id,
        )
    )
    progress = result.scalar_one_or_none()

    if not progress:
        progress = SkillProgress(user_id=current_user.id, skill_id=skill_id)
        db.add(progress)

    if "status" in body:
        progress.status = body["status"]
        if body["status"] == "in_progress" and not progress.started_at:
            progress.started_at = datetime.utcnow()
        if body["status"] == "done":
            progress.completed_at = datetime.utcnow()
            progress.progress_pct = 100.0

    if "progress_pct" in body:
        progress.progress_pct = body["progress_pct"]

    if "minutes_today" in body:
        progress.minutes_today = body["minutes_today"]
        progress.total_minutes = (progress.total_minutes or 0) + body["minutes_today"]

    if "notes" in body:
        progress.notes = body["notes"]

    progress.last_practiced = datetime.utcnow()

    # Update streak (simplified: increment if practiced today)
    progress.streak_days = (progress.streak_days or 0) + 1

    db.add(progress)
    return {"message": "Progress updated", "streak": progress.streak_days}


async def _ensure_seed_skills(db: AsyncSession):
    result = await db.execute(select(Skill).limit(1))
    if result.scalar_one_or_none():
        return
    for s in SEED_SKILLS:
        db.add(Skill(**s))
    await db.flush()
