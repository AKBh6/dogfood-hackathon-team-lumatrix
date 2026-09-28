from fastapi import FastAPI, Depends, HTTPException, Response, Form, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token, get_current_user

app = FastAPI(title="Dogfood App")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

@app.post("/register")
def register(
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("participant"),
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=email,
        hashed_password=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    return {"message": "Registration successful"}

@app.post("/login")
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})

    # Set JWT in an HttpOnly cookie
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,  # Set to True in HTTPS environments
        max_age=86400
    )
    return {"message": "Login successful", "role": user.role}

# Example Protected Dashboard Route
@app.get("/participant/dashboard", response_class=HTMLResponse)
def participant_dashboard(request: Request, current_user: User = Depends(get_current_user)):
    return templates.TemplateResponse(
        "participant/dashboard.html",
        {"request": request, "user": current_user}
    )
