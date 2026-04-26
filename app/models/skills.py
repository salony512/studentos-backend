from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Skill(Base):
    """Master list of skills (shared across all users)."""
    __tablename__ = "skills"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(200), nullable=False, unique=True)
    category    = Column(String(100), nullable=True)  # DSA/System Design/DBMS/Aptitude/etc.
    description = Column(Text, nullable=True)
    track       = Column(String(100), nullable=True)  # Developer/Analyst/Data Science
    order_in_track = Column(Integer, default=0)
    resources   = Column(Text, nullable=True)         # JSON list of {title, url, type}

class SkillProgress(Base):
    """Per-user skill progress tracking."""
    __tablename__ = "skill_progresses"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    skill_id      = Column(Integer, ForeignKey("skills.id"), nullable=False)
    status        = Column(String(20), default="not_started")  # not_started/in_progress/done
    progress_pct  = Column(Float, default=0.0)   # 0–100
    streak_days   = Column(Integer, default=0)
    last_practiced= Column(DateTime(timezone=True), nullable=True)
    minutes_today = Column(Integer, default=0)
    total_minutes = Column(Integer, default=0)
    notes         = Column(Text, nullable=True)
    started_at    = Column(DateTime(timezone=True), nullable=True)
    completed_at  = Column(DateTime(timezone=True), nullable=True)

    user          = relationship("User", back_populates="skill_progresses")
    skill         = relationship("Skill")
