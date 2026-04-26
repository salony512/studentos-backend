"""
Seed script — populates the DB with demo data for testing.
Run: python scripts/seed.py
"""
import asyncio
import sys
sys.path.insert(0, ".")

from app.database import AsyncSessionLocal, init_db
from app.models.user import User
from app.models.academics import Task, Subject, Exam
from app.models.health import HealthLog, MoodLog
from app.models.mindfulness import GratitudeLog
from app.services.auth_service import hash_password
from datetime import datetime, timedelta
import random


async def seed():
    await init_db()
    async with AsyncSessionLocal() as db:
        # Demo user
        user = User(
            name="Arjun Sharma",
            email="arjun@demo.com",
            hashed_pw=hash_password("demo1234"),
            college="Chandigarh University",
            branch="Computer Science",
            year=3,
            target_role="Software Developer",
            current_cgpa=7.2,
            target_cgpa=8.5,
        )
        db.add(user)
        await db.flush()

        # Subjects
        for sub in [
            ("Data Structures", 4, 72, 100),
            ("DBMS", 3, 68, 100),
            ("Operating Systems", 3, 75, 100),
            ("Computer Networks", 3, 80, 100),
        ]:
            db.add(Subject(user_id=user.id, name=sub[0], credits=sub[1], current_marks=sub[2], max_marks=sub[3], semester=5))

        # Tasks
        tasks_data = [
            ("Complete Striver sheet — trees", "skills", "high"),
            ("DBMS normalization revision", "academics", "high"),
            ("Solve 5 AMCAT quant problems", "skills", "medium"),
            ("Update resume projects section", "academics", "high"),
            ("Read OS deadlock chapter", "academics", "medium"),
            ("Drink 2.5L water today", "health", "low"),
            ("Evening walk 20 min", "health", "medium"),
        ]
        for title, cat, pri in tasks_data:
            db.add(Task(user_id=user.id, title=title, category=cat, priority=pri, status="pending"))

        # Health logs (last 14 days)
        moods = ["great", "good", "okay", "good", "low", "okay", "good", "great", "good", "okay", "low", "good", "good", "okay"]
        for i in range(14):
            db.add(HealthLog(
                user_id=user.id,
                log_date=datetime.utcnow() - timedelta(days=i),
                sleep_hours=round(random.uniform(5.5, 8.0), 1),
                sleep_quality=random.randint(5, 9),
                water_liters=round(random.uniform(1.2, 2.8), 1),
                exercise_min=random.choice([0, 0, 20, 30, 0, 25, 0]),
                stress_level=random.randint(3, 8),
                energy_level=random.randint(5, 9),
                skin_condition=random.choice(["good", "fair", "good", "good", "poor"]),
                mood=moods[i],
                focus_score=random.randint(5, 9),
            ))

        # Gratitude logs
        entries = [
            ("Finished a hard LeetCode problem", "My roommate explained networking concepts", "Slept 7.5h last night"),
            ("Got positive feedback on my project", "Had a productive morning study session", "My friend shared AMCAT resources"),
        ]
        for e1, e2, e3 in entries:
            db.add(GratitudeLog(user_id=user.id, entry1=e1, entry2=e2, entry3=e3, mood_after="good"))

        await db.commit()
        print("✅ Demo data seeded!")
        print("📧 Login: arjun@demo.com | Password: demo1234")
        print("📖 API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed())
