from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException
from pydantic import BaseModel,Field
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Submission,Team,TeamMember,Event,User
router=APIRouter()
class SubmissionCreate(BaseModel):
    title:str=Field(min_length=1,max_length=255)
    tagline:str|None=None
    description:str=Field(min_length=1)
    thumbnail_url:str|None=None
    image_gallery:str=""
    demo_video_url:str|None=None
    repo_url:str=Field(min_length=1,max_length=512)
    live_url:str|None=None
    tech_tags:str=""
    track:str|None=None
    custom_answers:str=""
    demo_url:str|None=None
    is_draft:bool=True
def utcnow(): return datetime.now(timezone.utc)
def get_event_team(db,user):
    event=db.query(Event).filter_by(is_active=True).order_by(Event.id.desc()).first()
    membership=db.query(TeamMember).join(Team).filter(TeamMember.user_id==user.id,Team.event_id==event.id).first() if event else None
    if not membership: raise HTTPException(400,"You do not belong to a team for the active event.")
    return membership.team,event
def save_submission(payload,db,user):
    team,event=get_event_team(db,user); deadline=event.submission_deadline
    if deadline.tzinfo is None: deadline=deadline.replace(tzinfo=timezone.utc)
    if utcnow()>deadline: raise HTTPException(403,"Submission deadline has passed.")
    existing=db.query(Submission).filter_by(team_id=team.id).first()
    if existing and not existing.is_draft: raise HTTPException(403,"Final submissions cannot be edited.")
    sub=existing or Submission(team_id=team.id,title="",description="",repo_url="")
    sub.title,sub.tagline,sub.description=payload.title,payload.tagline,payload.description
    sub.thumbnail_url,sub.image_gallery=payload.thumbnail_url,payload.image_gallery
    sub.demo_video_url,sub.repo_url=payload.demo_video_url,payload.repo_url
    sub.live_url,sub.tech_tags=payload.live_url,payload.tech_tags
    sub.track,sub.custom_answers,sub.demo_url=payload.track,payload.custom_answers,payload.demo_url
    sub.is_draft=payload.is_draft; sub.submitted_at=None if payload.is_draft else utcnow()
    db.add(sub); db.commit(); db.refresh(sub); return sub
@router.get("/gallery")
def public_gallery(search:str="",db:Session=Depends(get_db)):
    q=db.query(Submission).join(Team).filter(Submission.is_draft==False)
    if search.strip():
        term=f"%{search.strip()}%"; q=q.filter((Submission.title.ilike(term))|(Submission.description.ilike(term)))
    return [{"id":s.id,"title":s.title,"description":s.description,"team_name":s.team.name,"repo_url":s.repo_url,"demo_url":s.demo_url} for s in q.order_by(Submission.submitted_at.desc()).all()]
