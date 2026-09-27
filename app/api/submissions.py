from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Submission, Team, TeamMember, Event, User
from app.auth import get_current_user

router = APIRouter()

class SubmissionCreate(BaseModel):
    title: str
    description: str
    repo_url: str
    demo_url: str | None = None
    is_draft: bool = False

@router.post("/", status_code=status.HTTP_201_CREATED)
def submit_project(
    payload: SubmissionCreate, 
    db: Session = Depends(get_db), 
    user: User = Depends(get_current_user)
):
    # Locate user's team
    membership = db.query(TeamMember).filter(TeamMember.user_id == user.id).first()
    if not membership:
        raise HTTPException(status_code=400, detail="User does not belong to any team.")

    team = db.query(Team).filter(Team.id == membership.team_id).first()
    event = db.query(Event).filter(Event.id == team.event_id).first()

    # Enforce strict deadline
    if datetime.now(timezone.utc) > event.submission_deadline.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=403, detail="Submission deadline has passed.")

    sub = db.query(Submission).filter(Submission.team_id == team.id).first()
    if sub:
        # Edit existing
        sub.title = payload.title
        sub.description = payload.description
        sub.repo_url = payload.repo_url
        sub.demo_url = payload.demo_url
        sub.is_draft = payload.is_draft
        sub.submitted_at = datetime.now(timezone.utc)
    else:
        # Create new
        sub = Submission(
            team_id=team.id,
            title=payload.title,
            description=payload.description,
            repo_url=payload.repo_url,
            demo_url=payload.demo_url,
            is_draft=payload.is_draft,
            submitted_at=datetime.now(timezone.utc)
        )
        db.add(sub)

    db.commit()
    return {"message": "Submission recorded", "submission_id": sub.id}

@router.get("/gallery")
def public_gallery(db: Session = Depends(get_db)):
    """Searchable public gallery showing published submissions."""
    subs = db.query(Submission).filter(Submission.is_draft == False).all()
    return [
        {
            "id": s.id,
            "title": s.title,
            "description": s.description,
            "repo_url": s.repo_url,
            "demo_url": s.demo_url
        }
        for s in subs
    ]
