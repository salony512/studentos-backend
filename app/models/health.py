from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class HealthLog(Base):
    """Daily health check-in — the core data for ML correlation engine."""
    __tablename__ = "health_logs"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date      = Column(DateTime(timezone=True), server_default=func.now())

    # Sleep
    sleep_hours   = Column(Float, nullable=True)      # e.g. 6.5
    sleep_quality = Column(Integer, nullable=True)    # 1–10

    # Physical
    water_liters  = Column(Float, nullable=True)      # e.g. 2.0
    exercise_min  = Column(Integer, nullable=True)    # minutes of exercise
    steps         = Column(Integer, nullable=True)

    # Mental & skin
    stress_level  = Column(Integer, nullable=True)    # 1–10
    energy_level  = Column(Integer, nullable=True)    # 1–10
    skin_condition= Column(String(20), nullable=True) # good/fair/poor/breakout
    skin_score    = Column(Integer, nullable=True)    # 1–10

    # Overall
    mood          = Column(String(20), nullable=True) # great/good/okay/low/bad
    focus_score   = Column(Integer, nullable=True)    # 1–10 self rated
    notes         = Column(Text, nullable=True)

    user          = relationship("User", back_populates="health_logs")

class MoodLog(Base):
    """Quick mood check-ins (multiple per day)."""
    __tablename__ = "mood_logs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    mood       = Column(String(20), nullable=False)   # great/good/okay/low/bad
    note       = Column(Text, nullable=True)
    logged_at  = Column(DateTime(timezone=True), server_default=func.now())

    user       = relationship("User", back_populates="mood_logs")
