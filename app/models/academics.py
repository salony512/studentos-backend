from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class Priority(str, enum.Enum):
    low    = "low"
    medium = "medium"
    high   = "high"

class TaskStatus(str, enum.Enum):
    pending     = "pending"
    in_progress = "in_progress"
    done        = "done"
    skipped     = "skipped"

class Task(Base):
    __tablename__ = "tasks"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    title        = Column(String(300), nullable=False)
    description  = Column(Text, nullable=True)
    category     = Column(String(50), nullable=True)   # academics/skills/health/mindfulness
    priority     = Column(String(20), default="medium")
    status       = Column(String(20), default="pending")
    due_date     = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    stress_score = Column(Float, nullable=True)         # 0–10, AI-assigned
    created_at   = Column(DateTime(timezone=True), server_default=func.now())

    user         = relationship("User", back_populates="tasks")

class Subject(Base):
    __tablename__ = "subjects"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    name         = Column(String(200), nullable=False)
    credits      = Column(Integer, default=3)
    current_marks= Column(Float, nullable=True)
    max_marks    = Column(Float, default=100.0)
    semester     = Column(Integer, nullable=True)
    exam_date    = Column(DateTime(timezone=True), nullable=True)

class Exam(Base):
    __tablename__ = "exams"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    exam_type   = Column(String(50), nullable=False)   # AMCAT / aptitude / DBMS / etc.
    exam_date   = Column(DateTime(timezone=True), nullable=True)
    score       = Column(Float, nullable=True)
    notes       = Column(Text, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

class DayPlan(Base):
    """AI-generated daily schedule"""
    __tablename__ = "day_plans"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_date   = Column(DateTime(timezone=True), nullable=False)
    schedule    = Column(Text, nullable=True)   # JSON string of time slots
    energy_pred = Column(Float, nullable=True)  # AI predicted energy 0–10
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
