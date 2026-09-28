# seed.py
from app.database import SessionLocal, engine, Base
from app.models import User, RoleEnum, RubricCriterion
from app.auth import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

users = [
    User(
        full_name="Alice Builder",
        email="builder@raptors.dev",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.PARTICIPANT
    ),
    User(
        full_name="Bob Judge",
        email="judge@raptors.dev",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.JUDGE
    ),
    User(
        full_name="Charlie Admin",
        email="admin@raptors.dev",
        hashed_password=get_password_hash("password123"),
        role=RoleEnum.ORGANIZER
    ),
]

for user in users:
    if not db.query(User).filter(User.email == user.email).first():
        db.add(user)

criteria = [
    RubricCriterion(name="Innovation & Originality", weight=1.5, max_score=10.0),
    RubricCriterion(name="Technical Execution", weight=2.0, max_score=10.0),
    RubricCriterion(name="UI/UX & Design", weight=1.0, max_score=10.0),
]

for crit in criteria:
    if not db.query(RubricCriterion).filter(RubricCriterion.name == crit.name).first():
        db.add(crit)

db.commit()
db.close()
print("Database seeded with test accounts and evaluation rubrics!")
