from datetime import datetime, timezone, timedelta
from app.database import engine, Base, SessionLocal
from app.models import User, RoleEnum, Event, RubricCriterion, Team, TeamMember, Submission, JudgeAssignment
from app.auth import hash_password, create_access_token

DEMO_SUBMISSION_DEADLINE=datetime(2027,1,1,tzinfo=timezone.utc)
DEMO_VOTING_DEADLINE=datetime(2027,1,8,tzinfo=timezone.utc)

def seed_offline_fixtures():
    Base.metadata.create_all(bind=engine)
    db=SessionLocal()
    try:
        admin=db.query(User).filter_by(email="admin@raptors.dev").first()
        if not admin:
            admin=User(email="admin@raptors.dev",full_name="Hackathon Admin",hashed_password=hash_password("admin123"),role=RoleEnum.ADMIN); db.add(admin)
        judge=db.query(User).filter_by(email="judge@raptors.dev").first()
        if not judge:
            judge=User(email="judge@raptors.dev",full_name="Principal Judge",hashed_password=hash_password("judge123"),role=RoleEnum.JUDGE); db.add(judge)
        judge_b=db.query(User).filter_by(email="judgeb@raptors.dev").first()
        if not judge_b:
            judge_b=User(email="judgeb@raptors.dev",full_name="Second Judge",hashed_password=hash_password("judgeb123"),role=RoleEnum.JUDGE); db.add(judge_b)
        participant=db.query(User).filter_by(email="builder@raptors.dev").first()
        if not participant:
            participant=User(email="builder@raptors.dev",full_name="Lead Builder",hashed_password=hash_password("build123"),role=RoleEnum.PARTICIPANT); db.add(participant)
        db.flush()
        event=db.query(Event).filter_by(slug="dogfood-2026").first()
        if not event:
            event=Event(slug="dogfood-2026",title="Dogfood 2026 | 72-Hour Hackathon",submission_deadline=DEMO_SUBMISSION_DEADLINE,voting_deadline=DEMO_VOTING_DEADLINE,start_at=datetime(2026,12,29,tzinfo=timezone.utc),end_at=datetime(2027,1,1,tzinfo=timezone.utc),tracks="General\nAI\nWeb",prizes="1st Place\n2nd Place\nBest Technical Implementation",custom_questions="What problem does this solve?\nWhat would you improve next?",is_active=True); db.add(event); db.flush()
        criteria=[("Tier Completion & Correctness",.40),("Judging Integrity",.25),("Adoptability & Operability",.20),("Code Quality & Innovation",.15)]
        for name,weight in criteria:
            if not db.query(RubricCriterion).filter_by(event_id=event.id,name=name).first(): db.add(RubricCriterion(event_id=event.id,name=name,weight=weight,max_score=10))
        db.flush()
        team=db.query(Team).filter_by(event_id=event.id,name="Lumatrix").first()
        if not team:
            team=Team(name="Lumatrix",invite_code="LUMA-2026-X",event_id=event.id); db.add(team); db.flush()
        if not db.query(TeamMember).filter_by(user_id=participant.id,team_id=team.id).first(): db.add(TeamMember(user_id=participant.id,team_id=team.id,is_leader=True))
        sub=db.query(Submission).filter_by(team_id=team.id).first()
        if not sub:
            sub=Submission(team_id=team.id,title="Dogfood Platform Core",tagline="Offline-first hackathon operations",description="Offline-first hackathon management platform with role isolation and normalized judging.",thumbnail_url="",image_gallery="",demo_video_url="",repo_url="https://github.com/AKBh6/dogfood-hackathon-team-lumatrix",live_url="http://localhost:8000/gallery",tech_tags="FastAPI\nSQLAlchemy\nSQLite",track="Web",custom_answers="Hackathon operations\nAdd richer analytics",demo_url="http://localhost:8000/gallery",is_draft=False,submitted_at=datetime.now(timezone.utc)); db.add(sub); db.flush()
        if not db.query(JudgeAssignment).filter_by(judge_id=judge.id,submission_id=sub.id).first(): db.add(JudgeAssignment(judge_id=judge.id,submission_id=sub.id))
        db.commit()
        expires = timedelta(days=30)
        print("Seed complete.")
        print("acceptance organizer: Cookie: access_token=" + create_access_token({"sub": str(admin.id)}, expires))
        print("acceptance judge_a: Cookie: access_token=" + create_access_token({"sub": str(judge.id)}, expires))
        print("acceptance judge_b: Cookie: access_token=" + create_access_token({"sub": str(judge_b.id)}, expires))
        print("acceptance participant: Cookie: access_token=" + create_access_token({"sub": str(participant.id)}, expires))
    finally: db.close()

if __name__=="__main__": seed_offline_fixtures()
