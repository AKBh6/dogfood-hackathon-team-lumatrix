from fastapi import FastAPI, Depends, Request, Response, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, engine, Base
from app.models import User, RoleEnum
from app.auth import (
    hash_password, 
    verify_password, 
    create_access_token, 
    get_current_user
)

# Ensure database tables exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Dogfood Platform")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

def get_role_dashboard_url(role: RoleEnum) -> str:
    """Helper to route users to their respective role dashboard."""
    if role == RoleEnum.JUDGE:
        return "/judge/dashboard"
    elif role in (RoleEnum.ORGANIZER, RoleEnum.ADMIN):
        return "/organizer/dashboard"
    return "/participant/dashboard"


# --- AUTHENTICATION ROUTES ---

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "roles": [role.value for role in RoleEnum]}
    )


@app.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: RoleEnum = Form(RoleEnum.PARTICIPANT),
    db: Session = Depends(get_db)
):
    roles_list = [r.value for r in RoleEnum]
    
    # 1. Check if user already exists
    existing_user = db.query(User).filter(User.email == email.strip().lower()).first()
    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "An account with this email address already exists.",
                "roles": roles_list,
                "full_name": full_name,
                "email": email
            },
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 2. Create new user
    new_user = User(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        hashed_password=hash_password(password),
        role=role
    )
    db.add(new_user)
    db.commit()

    # 3. Redirect to login page with success indicator
    return RedirectResponse(
        url="/login?registered=1", 
        status_code=status.HTTP_303_SEE_OTHER
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, registered: bool = False):
    message = "Account created successfully! Please sign in." if registered else None
    return templates.TemplateResponse("login.html", {"request": request, "message": message})


@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email.strip().lower()).first()

    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid email address or password.",
                "email": email
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # Generate JWT token
    token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    # Set cookie and redirect to dashboard
    redirect_url = get_role_dashboard_url(user.role)
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in production over HTTPS
        max_age=86400
    )
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response
