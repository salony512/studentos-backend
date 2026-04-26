from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class GratitudeLog(Base):
    __tablename__ = "gratitude_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    entry1     = Column(Text, nullable=True)
    entry2     = Column(Text, nullable=True)
    entry3     = Column(Text, nullable=True)
    mood_after = Column(String(20), nullable=True)   # mood after logging
    logged_at  = Column(DateTime(timezone=True), server_default=func.now())

    user       = relationship("User", back_populates="gratitude_logs")

class BreathSession(Base):
    __tablename__ = "breath_sessions"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    technique   = Column(String(50), default="4-7-8")
    cycles      = Column(Integer, default=4)
    duration_s  = Column(Integer, nullable=True)   # actual seconds completed
    completed   = Column(Boolean, default=False)
    mood_before = Column(String(20), nullable=True)
    mood_after  = Column(String(20), nullable=True)
    logged_at   = Column(DateTime(timezone=True), server_default=func.now())

    user        = relationship("User", back_populates="breath_sessions")

class DailyIntention(Base):
    __tablename__ = "daily_intentions"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    intention  = Column(Text, nullable=False)
    achieved   = Column(Boolean, nullable=True)
    date       = Column(DateTime(timezone=True), server_default=func.now())
