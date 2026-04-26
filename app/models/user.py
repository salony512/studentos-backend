from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id           = Column(Integer, primary_key=True, index=True)
    name         = Column(String(100), nullable=False)
    email        = Column(String(200), unique=True, index=True, nullable=False)
    hashed_pw    = Column(String(200), nullable=False)
    college      = Column(String(200), nullable=True)
    branch       = Column(String(100), nullable=True)
    year         = Column(Integer, nullable=True)          # 1–4
    target_role  = Column(String(100), nullable=True)      # "Developer", "Analyst"…
    target_cgpa  = Column(Float, nullable=True)
    current_cgpa = Column(Float, nullable=True)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now())

    # relationships
    health_logs      = relationship("HealthLog",     back_populates="user", cascade="all,delete")
    tasks            = relationship("Task",           back_populates="user", cascade="all,delete")
    skill_progresses = relationship("SkillProgress",  back_populates="user", cascade="all,delete")
    gratitude_logs   = relationship("GratitudeLog",   back_populates="user", cascade="all,delete")
    breath_sessions  = relationship("BreathSession",  back_populates="user", cascade="all,delete")
    mood_logs        = relationship("MoodLog",        back_populates="user", cascade="all,delete")
