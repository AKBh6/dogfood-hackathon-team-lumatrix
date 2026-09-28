# fix_main.py
import os

content = """from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models import User, RoleEnum
from app.auth import get_password_hash, verify_password, get_current_user
from app.api import submissions, judging

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dogfood Platform")
app.add_middleware(SessionMiddleware, secret_key="dogfood-super-secret-key-2026")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(submissions.router)
app.include_router(judging.router)

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            request=request, 
            name="login.html", 
            context={"error": "Invalid email or password", "email": email}
        )
    
    request.session["user_id"] = user.id
    if user.role in [RoleEnum.ORGANIZER, RoleEnum.ADMIN]:
        return RedirectResponse(url="/organizer/dashboard", status_code=303)
    elif user.role == RoleEnum.JUDGE:
        return RedirectResponse(url="/judge/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/participant/dashboard", status_code=303)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    roles = [r.value for r in RoleEnum]
    return templates.TemplateResponse(request=request, name="register.html", context={"roles": roles})

@app.post("/register")
async def register(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        roles = [r.value for r in RoleEnum]
        return templates.TemplateResponse(
            request=request, 
            name="register.html", 
            context={
                "error": "Email already registered",
                "full_name": full_name,
                "email": email,
                "roles": roles
            }
        )
    
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=get_password_hash(password),
        role=RoleEnum(role)
    )
    db.add(user)
    db.commit()
    return templates.TemplateResponse(
        request=request, 
        name="login.html", 
        context={"message": "Account created! Please sign in."}
    )

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/participant/dashboard", response_class=HTMLResponse)
async def participant_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="participant/dashboard.html", context={"user": current_user})

@app.get("/judge/dashboard", response_class=HTMLResponse)
async def judge_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="judge/dashboard.html", context={"user": current_user})

@app.get("/organizer/dashboard", response_class=HTMLResponse)
async def organizer_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(request=request, name="organizer/dashboard.html", context={"user": current_user})
"""

with open("app/main.py", "w", encoding="utf-8") as f:
    f.write(content.strip())

print("app/main.py updated successfully!")