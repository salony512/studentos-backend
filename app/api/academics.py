from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models.academics import Task, Subject, Exam, DayPlan
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services.ai_service import build_day_plan

router = APIRouter(prefix="/api/academics", tags=["academics"])

# ── Schemas ────────────────────────────────────────────────────────────────
class TaskCreate(BaseModel):
    title:       str
    description: Optional[str] = None
    category:    Optional[str] = "academics"
    priority:    Optional[str] = "medium"
    due_date:    Optional[datetime] = None

class TaskUpdate(BaseModel):
    status:      Optional[str] = None
    priority:    Optional[str] = None
    title:       Optional[str] = None
    due_date:    Optional[datetime] = None

class SubjectCreate(BaseModel):
    name:          str
    credits:       int = 3
    current_marks: Optional[float] = None
    max_marks:     float = 100.0
    semester:      Optional[int] = None
    exam_date:     Optional[datetime] = None

class ExamCreate(BaseModel):
    exam_type: str
    exam_date: Optional[datetime] = None
    score:     Optional[float] = None
    notes:     Optional[str] = None

# ── Task Routes ────────────────────────────────────────────────────────────
@router.get("/tasks")
async def get_tasks(
    status: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Task).where(Task.user_id == current_user.id).order_by(desc(Task.created_at))
    if status:
        q = q.where(Task.status == status)
    if category:
        q = q.where(Task.category == category)
    result = await db.execute(q)
    tasks = result.scalars().all()
    return [_task_dict(t) for t in tasks]


@router.post("/tasks", status_code=201)
async def create_task(
    body: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = Task(user_id=current_user.id, **body.model_dump())
    db.add(task)
    await db.flush()
    return _task_dict(task)


@router.patch("/tasks/{task_id}")
async def update_task(
    task_id: int,
    body: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(404, "Task not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(task, k, v)
    if body.status == "done":
        task.completed_at = datetime.utcnow()
    db.add(task)
    return _task_dict(task)


@router.delete("/tasks/{task_id}", status_code=204)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == current_user.id))
    task = result.scalar_one_or_none()
    if task:
        await db.delete(task)


# ── Subject Routes ─────────────────────────────────────────────────────────
@router.get("/subjects")
async def get_subjects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.user_id == current_user.id))
    subjects = result.scalars().all()
    return subjects


@router.post("/subjects", status_code=201)
async def add_subject(body: SubjectCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = Subject(user_id=current_user.id, **body.model_dump())
    db.add(sub)
    await db.flush()
    return sub


@router.get("/cgpa")
async def compute_cgpa(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Subject).where(Subject.user_id == current_user.id))
    subjects = result.scalars().all()
    if not subjects:
        return {"cgpa": current_user.current_cgpa, "subjects": [], "message": "Add subjects to compute live CGPA"}

    total_credits = sum(s.credits for s in subjects if s.current_marks is not None)
    if total_credits == 0:
        return {"cgpa": None, "message": "Add marks to compute CGPA"}

    weighted = sum(
        (s.current_marks / s.max_marks * 10) * s.credits
        for s in subjects if s.current_marks is not None
    )
    cgpa = round(weighted / total_credits, 2)
    gap = round((current_user.target_cgpa or 8.0) - cgpa, 2) if current_user.target_cgpa else None
    return {
        "cgpa": cgpa,
        "target_cgpa": current_user.target_cgpa,
        "gap": gap,
        "subjects": len(subjects),
        "recommendation": (
            "You're on track!" if gap and gap <= 0
            else f"Need {gap} more points — focus on high-credit subjects first." if gap else None
        ),
    }


# ── Exam Routes ─────────────────────────────────────────────────────────────
@router.get("/exams")
async def get_exams(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Exam).where(Exam.user_id == current_user.id).order_by(Exam.exam_date))
    return result.scalars().all()


@router.post("/exams", status_code=201)
async def add_exam(body: ExamCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    exam = Exam(user_id=current_user.id, **body.model_dump())
    db.add(exam)
    await db.flush()
    return exam


# ── Day Plan ───────────────────────────────────────────────────────────────
@router.get("/dayplan")
async def get_day_plan(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch pending tasks
    result = await db.execute(
        select(Task).where(Task.user_id == current_user.id, Task.status == "pending")
        .order_by(Task.priority.desc())
        .limit(5)
    )
    tasks = [_task_dict(t) for t in result.scalars().all()]
    schedule = build_day_plan(tasks)
    return {"schedule": schedule, "task_count": len(tasks)}


def _task_dict(t: Task) -> dict:
    return {
        "id": t.id, "title": t.title, "description": t.description,
        "category": t.category, "priority": t.priority, "status": t.status,
        "due_date": t.due_date, "completed_at": t.completed_at, "created_at": t.created_at,
    }
