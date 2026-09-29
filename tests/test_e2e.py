from fastapi.testclient import TestClient
from app.main import app
from app.database import Base,engine,SessionLocal
from app.models import User,Team,Submission,JudgeAssignment,Score,RubricCriterion
from app.seed import seed_offline_fixtures
import os

client=TestClient(app)

def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    seed_offline_fixtures()

def login(email,password):
    r=client.post("/login",data={"email":email,"password":password},follow_redirects=False)
    assert r.status_code==303
    return r.cookies

def test_public_pages():
    assert client.get("/").status_code==200
    assert client.get("/gallery").status_code==200
    assert client.get("/register").status_code==200

def test_end_to_end_participant_team_submission_judge_results():
    email="e2e@example.com"
    r=client.post("/register",data={"full_name":"E2E Builder","email":email,"password":"build123"},follow_redirects=False)
    assert r.status_code==303
    cookies=login(email,"build123")
    r=client.post("/api/teams/create",data={"name":"E2E Team"},cookies=cookies,follow_redirects=False)
    assert r.status_code==303
    r=client.post("/api/submissions/final",data={"title":"E2E Project","description":"A working offline submission","repo_url":"https://example.test/repo","demo_url":"http://localhost:8000"},cookies=cookies,follow_redirects=False)
    assert r.status_code==303
    db=SessionLocal()
    try:
        sub=db.query(Submission).filter_by(title="E2E Project").one()
        assert not sub.is_draft
        assert sub.submitted_at is not None
        assert db.query(Team).filter_by(name="E2E Team").count()==1
    finally: db.close()
    admin_cookies=login("admin@raptors.dev","admin123")
    r=client.post("/organizer/assign",cookies=admin_cookies,follow_redirects=False)
    assert r.status_code==303
    db=SessionLocal()
    try:
        sub=db.query(Submission).filter_by(title="E2E Project").one()
        judge=db.query(User).filter_by(email="judge@raptors.dev").one()
        assert db.query(JudgeAssignment).filter_by(judge_id=judge.id,submission_id=sub.id).count()==1
        criteria=db.query(RubricCriterion).filter_by(event_id=sub.team.event_id).order_by(RubricCriterion.id).all()
        assert len(criteria)==4
    finally: db.close()
    judge_cookies=login("judge@raptors.dev","judge123")
    assert client.get(f"/judge/evaluate/{sub.id}",cookies=judge_cookies).status_code==200
    for criterion in criteria:
        r=client.post("/api/judging/evaluate",json={"submission_id":sub.id,"criterion_id":criterion.id,"raw_score":8.0,"feedback":"solid"},cookies=judge_cookies)
        assert r.status_code==200
    db=SessionLocal()
    try:
        assert db.query(Score).filter_by(submission_id=sub.id).count()==4
    finally: db.close()
    r=client.get("/organizer/results",cookies=admin_cookies)
    assert r.status_code==200
    assert "E2E Project" in r.text
    r=client.get("/api/judging/results.csv",cookies=admin_cookies)
    assert r.status_code==200 and "E2E Project" in r.text
    r=client.get("/gallery")
    assert "E2E Project" in r.text
    r=client.post("/api/submissions/final",data={"title":"Changed","description":"No","repo_url":"https://example.test/x"},cookies=cookies,follow_redirects=False)
    assert r.status_code==403
