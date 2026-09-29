from datetime import datetime, timezone
import secrets
from fastapi import FastAPI, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db, engine, Base
from app.models import User, RoleEnum, Event, Team, TeamMember, Submission, JudgeAssignment, Score
from app.auth import hash_password, verify_password, create_access_token, require_roles, get_current_user
from app.api import judging
Base.metadata.create_all(bind=engine)
app=FastAPI(title="Dogfood Platform")
app.mount("/static",StaticFiles(directory="app/static"),name="static")
templates=Jinja2Templates(directory="app/templates")
def render(request,name,context): return templates.TemplateResponse(request=request,name=name,context=context)
app.include_router(judging.router,prefix="/api/judging")
def now(): return datetime.now(timezone.utc)
def dashboard(role): return "/judge/dashboard" if role==RoleEnum.JUDGE else "/organizer/dashboard" if role in (RoleEnum.ORGANIZER,RoleEnum.ADMIN) else "/participant/dashboard"
def event_for(db): return db.query(Event).filter_by(slug="dogfood-2026").first()
def get_participant_membership(db,user): return db.query(TeamMember).join(Team).filter(TeamMember.user_id==user.id,Team.event_id==event_for(db).id).first()
@app.get("/",response_class=HTMLResponse)
def landing(request:Request): return render(request,"index.html",{"request":request})
@app.get("/register",response_class=HTMLResponse)
def register_page(request:Request): return render(request,"register.html",{"request":request})
@app.post("/register")
def register(request:Request,full_name:str=Form(...),email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    email=email.strip().lower()
    if db.query(User).filter_by(email=email).first(): return templates.TemplateResponse("register.html",{"request":request,"error":"An account with this email already exists."},status_code=400)
    if len(password)<6: return templates.TemplateResponse("register.html",{"request":request,"error":"Password must be at least 6 characters."},status_code=400)
    db.add(User(full_name=full_name.strip(),email=email,hashed_password=hash_password(password),role=RoleEnum.PARTICIPANT)); db.commit()
    return RedirectResponse("/login?registered=1",303)
@app.get("/login",response_class=HTMLResponse)
def login_page(request:Request,registered:bool=False,error:str|None=None): return render(request,"login.html",{"request":request,"message":"Account created successfully. Please sign in." if registered else None,"error":error})
@app.post("/login")
def login(email:str=Form(...),password:str=Form(...),db:Session=Depends(get_db)):
    user=db.query(User).filter_by(email=email.strip().lower()).first()
    if not user or not verify_password(password,user.hashed_password): return RedirectResponse("/login?error=Invalid%20email%20or%20password",303)
    response=RedirectResponse(dashboard(user.role),303); response.set_cookie("access_token",create_access_token({"sub":str(user.id)}),httponly=True,samesite="lax",max_age=86400); return response
@app.get("/logout")
def logout(): response=RedirectResponse("/login",303); response.delete_cookie("access_token"); return response
@app.get("/gallery",response_class=HTMLResponse)
def gallery(request:Request,search:str="",db:Session=Depends(get_db)):
    q=db.query(Submission).join(Team).filter(Submission.is_draft==False)
    if search.strip(): term=f"%{search.strip()}%"; q=q.filter((Submission.title.ilike(term))|(Submission.description.ilike(term)))
    return render(request,"gallery.html",{"request":request,"submissions":q.order_by(Submission.submitted_at.desc()).all(),"search":search})
@app.get("/api/submissions/gallery")
def api_gallery(search:str="",db:Session=Depends(get_db)):
    q=db.query(Submission).join(Team).filter(Submission.is_draft==False)
    if search.strip(): term=f"%{search.strip()}%"; q=q.filter((Submission.title.ilike(term))|(Submission.description.ilike(term)))
    return [{"id":s.id,"title":s.title,"description":s.description,"team_name":s.team.name,"repo_url":s.repo_url,"demo_url":s.demo_url} for s in q.all()]
@app.post("/api/teams/create")
def create_team(name:str=Form(...),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    event=event_for(db)
    if not event: raise HTTPException(500,"Demo event not initialized.")
    if get_participant_membership(db,user): raise HTTPException(400,"You already belong to a team for this event.")
    if not name.strip(): raise HTTPException(400,"Team name is required.")
    team=Team(name=name.strip(),invite_code=secrets.token_urlsafe(8),event_id=event.id); db.add(team); db.flush(); db.add(TeamMember(user_id=user.id,team_id=team.id,is_leader=True)); db.commit()
    return RedirectResponse("/participant/team",303)
@app.post("/api/teams/join")
def join_team(invite_code:str=Form(...),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    team=db.query(Team).filter_by(invite_code=invite_code.strip()).first()
    if not team: raise HTTPException(404,"Invalid invite code.")
    if len(team.members)>=4: raise HTTPException(400,"Team is full.")
    if db.query(TeamMember).join(Team).filter(TeamMember.user_id==user.id,Team.event_id==team.event_id).first(): raise HTTPException(400,"You already belong to a team for this event.")
    db.add(TeamMember(user_id=user.id,team_id=team.id,is_leader=False)); db.commit(); return RedirectResponse("/participant/team",303)
@app.get("/api/teams/me")
def my_team(db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    m=participant_team(db,user)
    if not m:return {"team":None}
    return {"team":{"id":m.team.id,"name":m.team.name,"invite_code":m.team.invite_code,"leader":next(x.user.full_name for x in m.team.members if x.is_leader),"members":[x.user.full_name for x in m.team.members]}}
@app.post("/api/submissions/save")
def save_submission(title:str=Form(...),description:str=Form(...),repo_url:str=Form(...),demo_url:str=Form(""),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from app.api.submissions import SubmissionCreate,save_submission as save
    save(SubmissionCreate(title=title,description=description,repo_url=repo_url,demo_url=demo_url or None,is_draft=True),db,user); return RedirectResponse("/participant/submission",303)
@app.post("/api/submissions/final")
def final_submission(title:str=Form(...),description:str=Form(...),repo_url:str=Form(...),demo_url:str=Form(""),db:Session=Depends(get_db),user:User=Depends(get_current_user)):
    from app.api.submissions import SubmissionCreate,save_submission as save
    save(SubmissionCreate(title=title,description=description,repo_url=repo_url,demo_url=demo_url or None,is_draft=False),db,user); return RedirectResponse("/participant/submission",303)
@app.get("/participant/dashboard",response_class=HTMLResponse)
def participant_dashboard(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.PARTICIPANT))): return render(request,"participant/dashboard.html",{"request":request,"user":user,"team":participant_team(db,user).team if participant_team(db,user) else None})
@app.get("/participant/team",response_class=HTMLResponse)
def participant_team(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.PARTICIPANT))): return render(request,"participant/team.html",{"request":request,"user":user,"team":participant_team(db,user).team if participant_team(db,user) else None})
@app.get("/participant/submission",response_class=HTMLResponse)
def participant_submission(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.PARTICIPANT))):
    m=participant_team(db,user); team=m.team if m else None; sub=team.submission if team else None; event=team.event if team else event_for(db)
    return render(request,"participant/submission.html",{"request":request,"user":user,"team":team,"submission":sub,"event":event})
@app.get("/judge/dashboard",response_class=HTMLResponse)
def judge_dashboard(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.JUDGE))):
    assignments=db.query(JudgeAssignment).filter_by(judge_id=user.id).all(); done={s.submission_id for s in db.query(Score).filter_by(judge_id=user.id).all()}
    return render(request,"judge/dashboard.html",{"request":request,"user":user,"assignments":assignments,"done":done})
@app.get("/judge/assignments",response_class=HTMLResponse)
def judge_assignments(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.JUDGE))):
    return render(request,"judge/assignments.html",{"request":request,"user":user,"assignments":db.query(JudgeAssignment).filter_by(judge_id=user.id).all()})
@app.get("/judge/evaluate/{submission_id}",response_class=HTMLResponse)
def judge_evaluate(request:Request,submission_id:int,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.JUDGE))):
    from app.api.judging import assert_assigned
    assert_assigned(db,user.id,submission_id); sub=db.query(Submission).filter_by(id=submission_id).first()
    if not sub: raise HTTPException(404,"Submission not found.")
    scores={s.criterion_id:s for s in db.query(Score).filter_by(judge_id=user.id,submission_id=submission_id).all()}
    return render(request,"judge/evaluate.html",{"request":request,"user":user,"submission":sub,"criteria":sub.team.event.rubrics,"scores":scores})
@app.get("/organizer/dashboard",response_class=HTMLResponse)
def organizer_dashboard(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.ORGANIZER,RoleEnum.ADMIN))):
    event=event_for(db)
    return render(request,"organizer/dashboard.html",{"request":request,"user":user,"event":event,"teams":db.query(Team).filter_by(event_id=event.id).count(),"submissions":db.query(Submission).join(Team).filter(Team.event_id==event.id,Submission.is_draft==False).count(),"judges":db.query(User).filter_by(role=RoleEnum.JUDGE).count(),"assignments":db.query(JudgeAssignment).count(),"scores":db.query(Score).count()})
@app.get("/organizer/event",response_class=HTMLResponse)
def organizer_event(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.ORGANIZER,RoleEnum.ADMIN))):
    event=event_for(db); return render(request,"organizer/event.html",{"request":request,"user":user,"event":event,"criteria":event.rubrics})
@app.post("/organizer/event")
def organizer_event_post(title:str=Form(...),db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.ORGANIZER,RoleEnum.ADMIN))):
    event=event_for(db); event.title=title.strip(); db.commit(); return RedirectResponse("/organizer/event",303)
@app.get("/organizer/results",response_class=HTMLResponse)
def organizer_results(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.ORGANIZER,RoleEnum.ADMIN))):
    from app.api.judging import ranking_rows
    return render(request,"organizer/results.html",{"request":request,"user":user,"rows":ranking_rows(db)})
@app.post("/organizer/assign")
def organizer_assign(db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.ORGANIZER,RoleEnum.ADMIN))):
    judges=db.query(User).filter(User.role==RoleEnum.JUDGE).order_by(User.id).all()
    if not judges: raise HTTPException(400,"No judges are available.")
    submissions=db.query(Submission).join(Team).filter(Submission.is_draft==False).order_by(Submission.id).all()
    for i,sub in enumerate(submissions):
        judge=judges[i % len(judges)]
        if not db.query(JudgeAssignment).filter_by(judge_id=judge.id,submission_id=sub.id).first(): db.add(JudgeAssignment(judge_id=judge.id,submission_id=sub.id))
    db.commit(); return RedirectResponse("/organizer/dashboard",303)
@app.get("/organizer/assignments",response_class=HTMLResponse)
def organizer_assignments(request:Request,db:Session=Depends(get_db),user:User=Depends(require_roles(RoleEnum.ORGANIZER,RoleEnum.ADMIN))):
    return render(request,"judge/assignments.html",{"request":request,"user":user,"assignments":db.query(JudgeAssignment).all(),"organizer":True})
