# build_participant.py - FIXED
import os

files = {
    "app/templates/base.html": """<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}Dogfood Platform{% endblock %}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<nav>
    <span>🐕 Dogfood Platform</span>
    {% if user %}
    <span>{{ user.full_name }} ({{ user.role.value }})</span>
    <a href="/logout">Logout</a>
    {% endif %}
</nav>
<main>
{% block content %}{% endblock %}
</main>
</body>
</html>""",

    "app/templates/participant/dashboard.html": """{% extends "base.html" %}
{% block content %}
<h2>Welcome to the Builder Portal</h2>
<p>Manage your team and submit your hackathon project here.</p>
<ul>
    <li><a href="/participant/team">1. Manage Team</a></li>
    <li><a href="/participant/submission">2. Project Submission</a></li>
</ul>
{% endblock %}""",

    "app/templates/participant/team.html": """{% extends "base.html" %}
{% block content %}
<h2>Team Management</h2>
{% if team %}
<h3>Current Team: {{ team.name }}</h3>
<p><strong>Invite Code: {{ team.invite_code }}</strong></p>
<p>Share this code with your teammates so they can join.</p>
{% else %}
<h3>Create a New Team</h3>
<form action="/participant/team/create" method="POST">
    <input type="text" name="name" placeholder="Team Name" required>
    <button type="submit">Create Team</button>
</form>
<h3>Join Existing Team</h3>
<form action="/participant/team/join" method="POST">
    <input type="text" name="invite_code" placeholder="6-Character Invite Code" required maxlength="6">
    <button type="submit">Join Team</button>
</form>
{% endif %}
<a href="/participant/dashboard">← Back to Dashboard</a>
{% endblock %}""",

    "app/templates/participant/submission.html": """{% extends "base.html" %}
{% block content %}
<h2>Project Submission</h2>
<p>Team: {{ team.name }}</p>

{% if submission and not submission.is_draft %}
<div class="alert-success">✅ Submission Finalized! Your project has been locked and is ready for judging.</div>
{% endif %}

<form action="/participant/submission" method="POST">
    <label>Project Title</label>
    <input type="text" name="title" value="{{ submission.title if submission else '' }}" required {% if submission and not submission.is_draft %}disabled{% endif %}>
    
    <label>Description</label>
    <textarea name="description" required {% if submission and not submission.is_draft %}disabled{% endif %}>{{ submission.description if submission else '' }}</textarea>
    
    <label>GitHub Repository URL</label>
    <input type="url" name="repo_url" value="{{ submission.repo_url if submission else '' }}" required {% if submission and not submission.is_draft %}disabled{% endif %}>
    
    <label>Live Demo URL (Optional)</label>
    <input type="url" name="demo_url" value="{{ submission.demo_url if submission else '' }}" {% if submission and not submission.is_draft %}disabled{% endif %}>

    {% if not submission or submission.is_draft %}
    <button type="submit" name="action" value="draft">💾 Save Draft</button>
    <button type="submit" name="action" value="final">🚀 Final Submit</button>
    {% endif %}
</form>
<a href="/participant/dashboard">← Back to Dashboard</a>
{% endblock %}""",

    "app/api/submissions.py": """import string
import random
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Team, TeamMember, Submission
from app.auth import get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/participant/team", response_class=HTMLResponse)
async def team_page(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first()
    team = membership.team if membership else None
    return templates.TemplateResponse(request=request, name="participant/team.html", context={"user": current_user, "team": team})

@router.post("/participant/team/create")
async def create_team(request: Request, name: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first():
        return RedirectResponse(url="/participant/team", status_code=303)
    invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    # ensure unique code
    while db.query(Team).filter(Team.invite_code == invite_code).first():
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    new_team = Team(name=name, invite_code=invite_code)
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    member = TeamMember(team_id=new_team.id, user_id=current_user.id, is_leader=True)
    db.add(member)
    db.commit()
    return RedirectResponse(url="/participant/team", status_code=303)

@router.post("/participant/team/join")
async def join_team(request: Request, invite_code: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first():
        return RedirectResponse(url="/participant/team", status_code=303)
    team = db.query(Team).filter(Team.invite_code == invite_code.upper().strip()).first()
    if not team:
        return RedirectResponse(url="/participant/team?error=Invalid+code", status_code=303)
    member = TeamMember(team_id=team.id, user_id=current_user.id, is_leader=False)
    db.add(member)
    db.commit()
    return RedirectResponse(url="/participant/team", status_code=303)

@router.get("/participant/submission", response_class=HTMLResponse)
async def submission_page(request: Request, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first()
    if not membership:
        return RedirectResponse(url="/participant/team", status_code=303)
    submission = db.query(Submission).filter(Submission.team_id == membership.team_id).first()
    return templates.TemplateResponse(request=request, name="participant/submission.html", context={"user": current_user, "team": membership.team, "submission": submission})

@router.post("/participant/submission")
async def handle_submission(request: Request, title: str = Form(...), description: str = Form(...), repo_url: str = Form(...), demo_url: str = Form(""), action: str = Form(...), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    membership = db.query(TeamMember).filter(TeamMember.user_id == current_user.id).first()
    if not membership:
        return RedirectResponse(url="/participant/team", status_code=303)
    submission = db.query(Submission).filter(Submission.team_id == membership.team_id).first()
    is_draft = (action == "draft")
    if submission:
        if not submission.is_draft:
            return RedirectResponse(url="/participant/submission", status_code=303)
        submission.title = title
        submission.description = description
        submission.repo_url = repo_url
        submission.demo_url = demo_url
        submission.is_draft = is_draft
    else:
        submission = Submission(team_id=membership.team_id, title=title, description=description, repo_url=repo_url, demo_url=demo_url, is_draft=is_draft)
        db.add(submission)
    db.commit()
    return RedirectResponse(url="/participant/submission", status_code=303)
"""
}

for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"Generated: {filepath}")

print("\nParticipant components built successfully!")