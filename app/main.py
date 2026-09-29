from datetime import datetime, timezone
import csv
import io
import json
import re
import secrets

from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app.models import (
    User, RoleEnum, Event, Team, TeamMember, Submission,
    JudgeAssignment, JudgeInvitation, JudgeTrack, Score
)
from app.auth import hash_password, verify_password, create_access_token, require_roles, get_current_user
from app.api import judging

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dogfood Platform")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def render(request, name, context, status_code=200):
    return templates.TemplateResponse(request=request, name=name, context=context, status_code=status_code)


app.include_router(judging.router, prefix="/api/judging")


def now():
    return datetime.now(timezone.utc)


def dashboard(role):
    if role == RoleEnum.JUDGE:
        return "/judge/dashboard"
    if role in (RoleEnum.ORGANIZER, RoleEnum.ADMIN):
        return "/organizer/dashboard"
    return "/participant/dashboard"


def event_for(db):
    return db.query(Event).filter_by(is_active=True).order_by(Event.id.desc()).first()


def parse_lines(value):
    return [x.strip() for x in (value or "").splitlines() if x.strip()]


def dump_lines(values):
    return "\n".join(values or [])


def get_participant_membership(db, user):
    event = event_for(db)
    if not event:
        return None
    return db.query(TeamMember).join(Team).filter(
        TeamMember.user_id == user.id,
        Team.event_id == event.id
    ).first()


def judge_can_access_submission(db, judge_id, submission):
    assignment = db.query(JudgeAssignment).filter_by(
        judge_id=judge_id, submission_id=submission.id
    ).first()
    if not assignment:
        return False
    scoped = db.query(JudgeTrack).filter_by(judge_id=judge_id, event_id=submission.team.event_id).all()
    if scoped and (submission.track or "General") not in {x.track for x in scoped}:
        return False
    return True


@app.get("/", response_class=HTMLResponse)
def landing(request: Request):
    return render(request, "index.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return render(request, "register.html", {"request": request})


@app.post("/register")
def register(request: Request, full_name: str = Form(...), email: str = Form(...),
             password: str = Form(...), db: Session = Depends(get_db)):
    full_name = full_name.strip()
    email = email.strip().lower()
    if not full_name:
        return render(request, "register.html", {"request": request, "error": "Full name is required."}, 400)
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return render(request, "register.html", {"request": request, "error": "Enter a valid email address."}, 400)
    if db.query(User).filter_by(email=email).first():
        return render(request, "register.html", {"request": request, "error": "An account with this email already exists."}, 400)
    if len(password) < 6:
        return render(request, "register.html", {"request": request, "error": "Password must be at least 6 characters."}, 400)
    db.add(User(full_name=full_name, email=email, hashed_password=hash_password(password), role=RoleEnum.PARTICIPANT))
    db.commit()
    return RedirectResponse("/login?registered=1", 303)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, registered: bool = False, error: str | None = None):
    return render(request, "login.html", {
        "request": request,
        "message": "Account created successfully. Please sign in." if registered else None,
        "error": error
    })


@app.post("/login")
def login(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=email.strip().lower()).first()
    if not user or not verify_password(password, user.hashed_password):
        return RedirectResponse("/login?error=Invalid%20email%20or%20password", 303)
    response = RedirectResponse(dashboard(user.role), 303)
    response.set_cookie(
        "access_token",
        create_access_token({"sub": str(user.id)}),
        httponly=True,
        samesite="lax",
        max_age=86400
    )
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", 303)
    response.delete_cookie("access_token")
    return response


@app.get("/judge/invite/{token}", response_class=HTMLResponse)
def judge_invite_page(request: Request, token: str, db: Session = Depends(get_db)):
    invitation = db.query(JudgeInvitation).filter_by(token=token).first()
    if not invitation or invitation.accepted_at:
        return render(request, "login.html", {"request": request, "error": "This judge invitation is invalid or already used."}, 400)
    return render(request, "judge/accept_invite.html", {"request": request, "invitation": invitation})


@app.post("/judge/invite/{token}")
def accept_judge_invite(request: Request, token: str, full_name: str = Form(...),
                        password: str = Form(...), db: Session = Depends(get_db)):
    invitation = db.query(JudgeInvitation).filter_by(token=token).first()
    if not invitation or invitation.accepted_at:
        raise HTTPException(400, "This judge invitation is invalid or already used.")
    email = invitation.email.strip().lower()
    if db.query(User).filter_by(email=email).first():
        raise HTTPException(400, "An account already exists for this email.")
    if len(password) < 6:
        return render(request, "judge/accept_invite.html", {"request": request, "invitation": invitation, "error": "Password must be at least 6 characters."}, 400)
    user = User(email=email, full_name=full_name.strip(), hashed_password=hash_password(password), role=RoleEnum.JUDGE)
    db.add(user)
    invitation.accepted_at = now()
    db.commit()
    return RedirectResponse("/login?registered=1", 303)


@app.get("/gallery", response_class=HTMLResponse)
def gallery(request: Request, search: str = "", track: str = "", tag: str = "", db: Session = Depends(get_db)):
    q = db.query(Submission).join(Team).filter(Submission.is_draft == False)
    if search.strip():
        term = f"%{search.strip()}%"
        q = q.filter((Submission.title.ilike(term)) | (Submission.description.ilike(term)) | (Submission.tagline.ilike(term)))
    if track.strip():
        q = q.filter(Submission.track == track.strip())
    if tag.strip():
        q = q.filter(Submission.tech_tags.ilike(f"%{tag.strip()}%"))
    submissions = q.order_by(Submission.submitted_at.desc()).all()
    tracks = sorted({s.track for s in db.query(Submission).filter(Submission.is_draft == False).all() if s.track})
    return render(request, "gallery.html", {
        "request": request, "submissions": submissions, "search": search,
        "track": track, "tag": tag, "tracks": tracks
    })


@app.get("/api/submissions/gallery")
def api_gallery(search: str = "", track: str = "", tag: str = "", db: Session = Depends(get_db)):
    q = db.query(Submission).join(Team).filter(Submission.is_draft == False)
    if search.strip():
        term = f"%{search.strip()}%"
        q = q.filter((Submission.title.ilike(term)) | (Submission.description.ilike(term)) | (Submission.tagline.ilike(term)))
    if track.strip():
        q = q.filter(Submission.track == track.strip())
    if tag.strip():
        q = q.filter(Submission.tech_tags.ilike(f"%{tag.strip()}%"))
    return [{
        "id": s.id, "title": s.title, "tagline": s.tagline,
        "description": s.description, "team_name": s.team.name,
        "repo_url": s.repo_url, "live_url": s.live_url,
        "demo_video_url": s.demo_video_url, "track": s.track,
        "tech_tags": parse_lines(s.tech_tags), "thumbnail_url": s.thumbnail_url,
        "image_gallery": parse_lines(s.image_gallery)
    } for s in q.order_by(Submission.submitted_at.desc()).all()]


@app.post("/api/teams/create")
def create_team(name: str = Form(...), db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    event = event_for(db)
    if not event:
        raise HTTPException(500, "No active event.")
    if user.role != RoleEnum.PARTICIPANT:
        raise HTTPException(403, "Only participants can form teams.")
    if get_participant_membership(db, user):
        raise HTTPException(400, "You already belong to a team for this event.")
    if not name.strip():
        raise HTTPException(400, "Team name is required.")
    team = Team(name=name.strip(), invite_code=secrets.token_urlsafe(8), event_id=event.id)
    db.add(team)
    db.flush()
    db.add(TeamMember(user_id=user.id, team_id=team.id, is_leader=True))
    db.commit()
    return RedirectResponse("/participant/team", 303)


@app.post("/api/teams/join")
def join_team(invite_code: str = Form(...), db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    if user.role != RoleEnum.PARTICIPANT:
        raise HTTPException(403, "Only participants can join teams.")
    team = db.query(Team).filter_by(invite_code=invite_code.strip()).first()
    if not team:
        raise HTTPException(404, "Invalid invite code.")
    if len(team.members) >= 4:
        raise HTTPException(400, "Team is full.")
    if db.query(TeamMember).join(Team).filter(
        TeamMember.user_id == user.id, Team.event_id == team.event_id
    ).first():
        raise HTTPException(400, "You already belong to a team for this event.")
    db.add(TeamMember(user_id=user.id, team_id=team.id, is_leader=False))
    db.commit()
    return RedirectResponse("/participant/team", 303)


@app.get("/participant/team/invite/{invite_code}")
def join_team_link(invite_code: str, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleEnum.PARTICIPANT))):
    team = db.query(Team).filter_by(invite_code=invite_code).first()
    if not team:
        raise HTTPException(404, "Invalid invite link.")
    if len(team.members) >= 4:
        raise HTTPException(400, "Team is full.")
    if db.query(TeamMember).join(Team).filter(TeamMember.user_id == user.id, Team.event_id == team.event_id).first():
        return RedirectResponse("/participant/team", 303)
    db.add(TeamMember(user_id=user.id, team_id=team.id, is_leader=False))
    db.commit()
    return RedirectResponse("/participant/team", 303)


@app.get("/api/teams/me")
def my_team(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = get_participant_membership(db, user)
    if not m:
        return {"team": None}
    return {"team": {
        "id": m.team.id, "name": m.team.name, "invite_code": m.team.invite_code,
        "leader": next(x.user.full_name for x in m.team.members if x.is_leader),
        "members": [x.user.full_name for x in m.team.members]
    }}


@app.post("/api/submissions/save")
def save_submission(title: str = Form(...), tagline: str = Form(""),
                    description: str = Form(...), thumbnail_url: str = Form(""),
                    image_gallery: str = Form(""), demo_video_url: str = Form(""),
                    repo_url: str = Form(...), live_url: str = Form(""),
                    tech_tags: str = Form(""), track: str = Form(""),
                    custom_answers: str = Form(""), db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleEnum.PARTICIPANT))):
    from app.api.submissions import SubmissionCreate, save_submission as save
    event = event_for(db)
    if event and track and track not in parse_lines(event.tracks):
        raise HTTPException(400, "Invalid track for this event.")
    save(SubmissionCreate(
        title=title, tagline=tagline or None, description=description,
        thumbnail_url=thumbnail_url or None, image_gallery=image_gallery,
        demo_video_url=demo_video_url or None, repo_url=repo_url,
        live_url=live_url or None, tech_tags=tech_tags, track=track or None,
        custom_answers=custom_answers, demo_url=live_url or None, is_draft=True
    ), db, user)
    return RedirectResponse("/participant/submission", 303)


@app.post("/api/submissions/final")
def final_submission(title: str = Form(...), tagline: str = Form(""),
                      description: str = Form(...), thumbnail_url: str = Form(""),
                      image_gallery: str = Form(""), demo_video_url: str = Form(""),
                      repo_url: str = Form(...), live_url: str = Form(""),
                      tech_tags: str = Form(""), track: str = Form(""),
                      custom_answers: str = Form(""), db: Session = Depends(get_db),
                      user: User = Depends(require_roles(RoleEnum.PARTICIPANT))):
    from app.api.submissions import SubmissionCreate, save_submission as save
    event = event_for(db)
    if event and track and track not in parse_lines(event.tracks):
        raise HTTPException(400, "Invalid track for this event.")
    save(SubmissionCreate(
        title=title, tagline=tagline or None, description=description,
        thumbnail_url=thumbnail_url or None, image_gallery=image_gallery,
        demo_video_url=demo_video_url or None, repo_url=repo_url,
        live_url=live_url or None, tech_tags=tech_tags, track=track or None,
        custom_answers=custom_answers, demo_url=live_url or None, is_draft=False
    ), db, user)
    return RedirectResponse("/participant/submission", 303)


@app.get("/participant/dashboard", response_class=HTMLResponse)
def participant_dashboard(request: Request, db: Session = Depends(get_db),
                          user: User = Depends(require_roles(RoleEnum.PARTICIPANT))):
    m = get_participant_membership(db, user)
    return render(request, "participant/dashboard.html", {"request": request, "user": user, "team": m.team if m else None})


@app.get("/participant/team", response_class=HTMLResponse)
def participant_team(request: Request, db: Session = Depends(get_db),
                     user: User = Depends(require_roles(RoleEnum.PARTICIPANT))):
    m = get_participant_membership(db, user)
    return render(request, "participant/team.html", {"request": request, "user": user, "team": m.team if m else None})


@app.get("/participant/submission", response_class=HTMLResponse)
def participant_submission(request: Request, db: Session = Depends(get_db),
                           user: User = Depends(require_roles(RoleEnum.PARTICIPANT))):
    m = get_participant_membership(db, user)
    team = m.team if m else None
    sub = team.submission if team else None
    event = team.event if team else event_for(db)
    return render(request, "participant/submission.html", {
        "request": request, "user": user, "team": team, "submission": sub,
        "event": event, "tracks": parse_lines(event.tracks) if event else [],
        "questions": parse_lines(event.custom_questions) if event else []
    })


@app.get("/judge/dashboard", response_class=HTMLResponse)
def judge_dashboard(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleEnum.JUDGE))):
    assignments = db.query(JudgeAssignment).filter_by(judge_id=user.id).all()
    visible = [a for a in assignments if judge_can_access_submission(db, user.id, a.submission)]
    done = {s.submission_id for s in db.query(Score).filter_by(judge_id=user.id).all()}
    return render(request, "judge/dashboard.html", {
        "request": request, "user": user, "assignments": visible, "done": done
    })


@app.get("/judge/assignments", response_class=HTMLResponse)
def judge_assignments(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_roles(RoleEnum.JUDGE))):
    assignments = db.query(JudgeAssignment).filter_by(judge_id=user.id).all()
    assignments = [a for a in assignments if judge_can_access_submission(db, user.id, a.submission)]
    return render(request, "judge/assignments.html", {"request": request, "user": user, "assignments": assignments})


@app.get("/judge/evaluate/{submission_id}", response_class=HTMLResponse)
def judge_evaluate(request: Request, submission_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_roles(RoleEnum.JUDGE))):
    sub = db.query(Submission).filter_by(id=submission_id).first()
    if not sub or not judge_can_access_submission(db, user.id, sub):
        raise HTTPException(403, "This submission is not assigned to you.")
    scores = {s.criterion_id: s for s in db.query(Score).filter_by(
        judge_id=user.id, submission_id=submission_id
    ).all()}
    return render(request, "judge/evaluate.html", {
        "request": request, "user": user, "submission": sub,
        "criteria": sub.team.event.rubrics, "scores": scores
    })


@app.get("/organizer/dashboard", response_class=HTMLResponse)
def organizer_dashboard(request: Request, db: Session = Depends(get_db),
                        user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    if not event:
        raise HTTPException(500, "No active event.")
    judges = db.query(User).filter_by(role=RoleEnum.JUDGE).all()
    submissions = db.query(Submission).join(Team).filter(
        Team.event_id == event.id, Submission.is_draft == False
    ).all()
    progress = []
    criteria_count = len(event.rubrics)
    for judge in judges:
        assignments = [a for a in db.query(JudgeAssignment).filter_by(judge_id=judge.id).all()
                       if a.submission.team.event_id == event.id and judge_can_access_submission(db, judge.id, a.submission)]
        scored = 0
        for a in assignments:
            count = db.query(Score).filter_by(judge_id=judge.id, submission_id=a.submission_id).count()
            if count >= criteria_count and criteria_count:
                scored += 1
        progress.append({"judge": judge, "assigned": len(assignments), "completed": scored,
                         "pending": max(0, len(assignments) - scored)})
    return render(request, "organizer/dashboard.html", {
        "request": request, "user": user, "event": event,
        "teams": db.query(Team).filter_by(event_id=event.id).count(),
        "submissions": len(submissions), "judges": len(judges),
        "assignments": db.query(JudgeAssignment).join(Submission).join(Team).filter(Team.event_id == event.id).count(),
        "scores": db.query(Score).join(Submission).join(Team).filter(Team.event_id == event.id).count(),
        "progress": progress
    })


@app.get("/organizer/event", response_class=HTMLResponse)
def organizer_event(request: Request, db: Session = Depends(get_db),
                    user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    return render(request, "organizer/event.html", {
        "request": request, "user": user, "event": event,
        "criteria": event.rubrics, "tracks": parse_lines(event.tracks),
        "questions": parse_lines(event.custom_questions)
    })


@app.post("/organizer/event")
def organizer_event_post(
    title: str = Form(...), start_at: str = Form(""), end_at: str = Form(""),
    submission_deadline: str = Form(...), voting_deadline: str = Form(...),
    tracks: str = Form(""), prizes: str = Form(""), custom_questions: str = Form(""),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))
):
    event = event_for(db)
    if not event:
        raise HTTPException(500, "No active event.")
    def parse_dt(value):
        if not value:
            return None
        return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)
    event.title = title.strip()
    event.start_at = parse_dt(start_at)
    event.end_at = parse_dt(end_at)
    event.submission_deadline = parse_dt(submission_deadline)
    event.voting_deadline = parse_dt(voting_deadline)
    event.tracks = "\n".join(parse_lines(tracks))
    event.prizes = "\n".join(parse_lines(prizes))
    event.custom_questions = "\n".join(parse_lines(custom_questions))
    db.commit()
    return RedirectResponse("/organizer/event", 303)


@app.post("/organizer/invite-judges")
def invite_judges(emails: str = Form(...), tracks: str = Form(""),
                  db: Session = Depends(get_db),
                  user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    invited = []
    selected_tracks = parse_lines(tracks)
    for email in re.split(r"[,\n]+", emails):
        email = email.strip().lower()
        if not email or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            continue
        if db.query(User).filter_by(email=email).first():
            continue
        token = secrets.token_urlsafe(24)
        db.add(JudgeInvitation(event_id=event.id, email=email, token=token))
        invited.append({"email": email, "token": token})
    db.commit()
    return render(request=None if False else Request, "organizer/event.html", {}) if False else RedirectResponse("/organizer/event?invited=1", 303)


@app.post("/organizer/assign")
def organizer_assign(db: Session = Depends(get_db),
                     user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    judges = db.query(User).filter(User.role == RoleEnum.JUDGE).order_by(User.id).all()
    if not judges:
        raise HTTPException(400, "No judges are available.")
    submissions = db.query(Submission).join(Team).filter(
        Team.event_id == event.id, Submission.is_draft == False
    ).order_by(Submission.id).all()
    for i, sub in enumerate(submissions):
        eligible = []
        for judge in judges:
            scopes = db.query(JudgeTrack).filter_by(judge_id=judge.id, event_id=event.id).all()
            if not scopes or (sub.track or "General") in {x.track for x in scopes}:
                eligible.append(judge)
        if not eligible:
            continue
        judge = eligible[i % len(eligible)]
        if not db.query(JudgeAssignment).filter_by(judge_id=judge.id, submission_id=sub.id).first():
            db.add(JudgeAssignment(judge_id=judge.id, submission_id=sub.id))
    db.commit()
    return RedirectResponse("/organizer/dashboard", 303)


@app.post("/organizer/assign-track")
def assign_judge_track(judge_id: int = Form(...), track: str = Form(...),
                       db: Session = Depends(get_db),
                       user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    judge = db.query(User).filter_by(id=judge_id, role=RoleEnum.JUDGE).first()
    if not judge:
        raise HTTPException(404, "Judge not found.")
    if track not in parse_lines(event.tracks):
        raise HTTPException(400, "Track is not configured for this event.")
    if not db.query(JudgeTrack).filter_by(judge_id=judge.id, event_id=event.id, track=track).first():
        db.add(JudgeTrack(judge_id=judge.id, event_id=event.id, track=track))
        db.commit()
    return RedirectResponse("/organizer/event", 303)


@app.get("/organizer/results", response_class=HTMLResponse)
def organizer_results(request: Request, db: Session = Depends(get_db),
                      user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    from app.api.judging import ranking_rows
    return render(request, "organizer/results.html", {"request": request, "user": user, "rows": ranking_rows(db)})


def csv_response(filename, headers, rows):
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    writer.writerows(rows)
    return RedirectResponse("/organizer/dashboard", 303) if False else __import__("fastapi").responses.Response(
        output.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/organizer/export/submissions.csv")
def export_submissions(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    rows = db.query(Submission).join(Team).filter(Team.event_id == event.id).all()
    return csv_response("submissions.csv",
        ["id","team","title","tagline","track","tech_tags","repo_url","live_url","demo_video_url","is_draft","submitted_at"],
        [{"id":s.id,"team":s.team.name,"title":s.title,"tagline":s.tagline or "","track":s.track or "",
          "tech_tags":s.tech_tags.replace("\n", ", "),"repo_url":s.repo_url,"live_url":s.live_url or "",
          "demo_video_url":s.demo_video_url or "","is_draft":s.is_draft,"submitted_at":s.submitted_at} for s in rows])


@app.get("/organizer/export/assignments.csv")
def export_assignments(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    rows = db.query(JudgeAssignment).join(Submission).join(Team).filter(Team.event_id == event.id).all()
    return csv_response("assignments.csv", ["judge","email","submission","team","track"],
        [{"judge":a.judge.full_name,"email":a.judge.email,"submission":a.submission.title,
          "team":a.submission.team.name,"track":a.submission.track or "General"} for a in rows])


@app.get("/organizer/export/scores.csv")
def export_scores(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    rows = db.query(Score).join(Submission).join(Team).filter(Team.event_id == event.id).all()
    return csv_response("scores.csv", ["judge","email","team","project","criterion","raw_score","feedback","created_at"],
        [{"judge":s.judge.full_name,"email":s.judge.email,"team":s.submission.team.name,"project":s.submission.title,
          "criterion":s.criterion.name,"raw_score":s.raw_score,"feedback":s.feedback or "","created_at":s.created_at} for s in rows])


@app.get("/organizer/export/progress.csv")
def export_progress(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    event = event_for(db)
    criteria_count = len(event.rubrics)
    rows = []
    for judge in db.query(User).filter_by(role=RoleEnum.JUDGE).all():
        assignments = [a for a in db.query(JudgeAssignment).filter_by(judge_id=judge.id).all()
                       if a.submission.team.event_id == event.id and judge_can_access_submission(db, judge.id, a.submission)]
        completed = sum(
            1 for a in assignments
            if db.query(Score).filter_by(judge_id=judge.id, submission_id=a.submission_id).count() >= criteria_count
        )
        rows.append({"judge":judge.full_name,"email":judge.email,"assigned":len(assignments),
                     "completed":completed,"pending":len(assignments)-completed})
    return csv_response("judging-progress.csv", ["judge","email","assigned","completed","pending"], rows)


@app.get("/organizer/assignments", response_class=HTMLResponse)
def organizer_assignments(request: Request, db: Session = Depends(get_db),
                          user: User = Depends(require_roles(RoleEnum.ORGANIZER, RoleEnum.ADMIN))):
    return render(request, "judge/assignments.html", {
        "request": request, "user": user,
        "assignments": db.query(JudgeAssignment).join(Submission).join(Team).filter(
            Team.event_id == event_for(db).id
        ).all(), "organizer": True
    })
