# make_core.py
import os

def clean(text):
    return (text
        .replace("[LT]", "<")
        .replace("[GT]", ">")
        .replace("[BO]", "{%")
        .replace("[BC]", "%}")
        .replace("[VO]", "{{")
        .replace("[VC]", "}}")
    )

files = {
    # -------------------------------------------------------------
    # 1. DATABASE CONFIGURATION
    # -------------------------------------------------------------
    "app/database.py": """from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./dogfood.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
""",

    # -------------------------------------------------------------
    # 2. SQLALCHEMY MODELS
    # -------------------------------------------------------------
    "app/models.py": """import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.database import Base

class RoleEnum(str, enum.Enum):
    PARTICIPANT = "Participant"
    JUDGE = "Judge"
    ORGANIZER = "Organizer"
    ADMIN = "Admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), default=RoleEnum.PARTICIPANT)

    team_memberships = relationship("TeamMember", back_populates="user")
    scores = relationship("Score", back_populates="judge")

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    invite_code = Column(String, unique=True, nullable=False)

    members = relationship("TeamMember", back_populates="team")
    submissions = relationship("Submission", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_leader = Column(Boolean, default=False)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")

class Submission(Base):
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    repo_url = Column(String, nullable=False)
    demo_url = Column(String, nullable=True)
    is_draft = Column(Boolean, default=True)

    team = relationship("Team", back_populates="submissions")
    scores = relationship("Score", back_populates="scores")

class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    weight = Column(Float, default=1.0)
    max_score = Column(Float, default=10.0)

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    judge_id = Column(Integer, ForeignKey("users.id"))
    criterion_id = Column(Integer, ForeignKey("rubric_criteria.id"))
    raw_score = Column(Float, nullable=False)
    feedback = Column(String, nullable=True)

    submission = relationship("Submission", back_populates="scores")
    judge = relationship("User", back_populates="scores")
""",

    # -------------------------------------------------------------
    # 3. AUTH UTILITIES
    # -------------------------------------------------------------
    "app/auth.py": """from fastapi import Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
""",

    # -------------------------------------------------------------
    # 4. STYLESHEET
    # -------------------------------------------------------------
    "app/static/css/style.css": """* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

body {
    background-color: #0f172a;
    color: #f8fafc;
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}

.navbar {
    background-color: #1e293b;
    border-bottom: 1px solid #334155;
    padding: 1rem 2rem;
}

.nav-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    max-width: 1200px;
    margin: 0 auto;
}

.brand {
    font-size: 1.25rem;
    font-weight: bold;
    color: #38bdf8;
    text-decoration: none;
}

.nav-links a {
    color: #94a3b8;
    text-decoration: none;
    margin-left: 1.5rem;
    transition: color 0.2s;
}

.nav-links a:hover {
    color: #f8fafc;
}

.container {
    flex: 1;
    max-width: 1200px;
    width: 100%;
    margin: 2rem auto;
    padding: 0 1.5rem;
}

.card, .auth-card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 2rem;
    margin-bottom: 1.5rem;
}

.auth-card {
    max-width: 420px;
    margin: 4rem auto;
}

.form-group {
    display: flex;
    flex-direction: column;
    gap: 1.2rem;
    margin-top: 1.5rem;
}

.field {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
}

label {
    font-size: 0.875rem;
    color: #cbd5e1;
}

input, select, textarea {
    background-color: #0f172a;
    border: 1px solid #334155;
    color: #f8fafc;
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 1rem;
}

input:focus, select:focus, textarea:focus {
    outline: none;
    border-color: #38bdf8;
}

.btn {
    padding: 0.75rem 1.5rem;
    border-radius: 6px;
    border: none;
    font-weight: 600;
    cursor: pointer;
    text-decoration: none;
    display: inline-block;
    text-align: center;
}

.btn-primary {
    background-color: #0284c7;
    color: #ffffff;
}

.btn-primary:hover {
    background-color: #0369a1;
}

.alert {
    padding: 0.75rem;
    border-radius: 6px;
    margin-bottom: 1rem;
    font-size: 0.875rem;
}

.alert-danger {
    background-color: #7f1d1d;
    color: #fecaca;
}

.alert-success {
    background-color: #14532d;
    color: #bbf7d0;
}

.footer {
    background-color: #1e293b;
    border-top: 1px solid #334155;
    text-align: center;
    padding: 1.5rem;
    font-size: 0.875rem;
    color: #64748b;
}

.results-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

.results-table th, .results-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #334155;
}

.results-table th {
    color: #38bdf8;
}
""",

    # -------------------------------------------------------------
    # 5. MAIN FASTAPI APP ENTRYPOINT
    # -------------------------------------------------------------
    "app/main.py": """from fastapi import FastAPI, Request, Form, Depends
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
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Invalid email or password",
            "email": email
        })
    
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
    return templates.TemplateResponse("register.html", {"request": request, "roles": roles})

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
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Email already registered",
            "full_name": full_name,
            "email": email,
            "roles": roles
        })
    
    user = User(
        full_name=full_name,
        email=email,
        hashed_password=get_password_hash(password),
        role=RoleEnum(role)
    )
    db.add(user)
    db.commit()
    return templates.TemplateResponse("login.html", {
        "request": request,
        "message": "Account created! Please sign in."
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/participant/dashboard", response_class=HTMLResponse)
async def participant_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("participant/dashboard.html", {"request": request, "user": current_user})

@app.get("/judge/dashboard", response_class=HTMLResponse)
async def judge_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("judge/dashboard.html", {"request": request, "user": current_user})

@app.get("/organizer/dashboard", response_class=HTMLResponse)
async def organizer_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse("organizer/dashboard.html", {"request": request, "user": current_user})
"""
}

# Write files safely to disk
for filepath, content in files.items():
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(clean(content).strip())
    print(f"Generated: {filepath}")

print("\nCore engine successfully built!")