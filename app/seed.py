from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.models import User, RoleEnum, Event, RubricCriterion, Team, TeamMember, Submission
from app.database import SessionLocal

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed_offline_fixtures():
    db = SessionLocal()
    try:
        if db.query(User).first():
            return  # Already seeded

        # 1. Base Users
        admin = User(
            email="admin@raptors.dev",
            full_name="Hackathon Admin",
            hashed_password=pwd_context.hash("admin123"),
            role=RoleEnum.ADMIN
        )
        judge = User(
            email="judge@raptors.dev",
            full_name="Principal Judge",
            hashed_password=pwd_context.hash("judge123"),
            role=RoleEnum.JUDGE
        )
        participant = User(
            email="builder@raptors.dev",
            full_name="Lead Builder",
            hashed_password=pwd_context.hash("build123"),
            role=RoleEnum.PARTICIPANT
        )
        db.add_all([admin, judge, participant])
        db.flush()

        # 2. Dogfood Hackathon Event
        now = datetime.now(timezone.utc)
        event = Event(
            slug="dogfood-2026",
            title="Dogfood 2026 | 72-Hour Hackathon",
            submission_deadline=now + timedelta(days=2),
            voting_deadline=now + timedelta(days=4),
            is_active=True
        )
        db.add(event)
        db.flush()

        # 3. Standard Rubrics (T2)
        criteria = [
            RubricCriterion(event_id=event.id, name="Tier Completion & Correctness", weight=0.40, max_score=10),
            RubricCriterion(event_id=event.id, name="Judging Integrity", weight=0.25, max_score=10),
            RubricCriterion(event_id=event.id, name="Adoptability & Operability", weight=0.20, max_score=10),
            RubricCriterion(event_id=event.id, name="Code Quality & Innovation", weight=0.15, max_score=10),
        ]
        db.add_all(criteria)
        db.flush()

        # 4. Fixture Team & Submission
        team = Team(name="Lumatrix", invite_code="LUMA-2026-X", event_id=event.id)
        db.add(team)
        db.flush()

        db.add(TeamMember(user_id=participant.id, team_id=team.id, is_leader=True))
        
        sub = Submission(
            team_id=team.id,
            title="Dogfood Platform Core",
            description="Offline-first hackathon runner with backend role isolation and z-score normalization.",
            repo_url="https://github.com/lumatrix/dogfood-core",
            demo_url="http://localhost:8000/gallery",
            is_draft=False,
            submitted_at=now
        )
        db.add(sub)
        db.commit()
        print("Successfully seeded fixture data.")
    finally:
        db.close()
