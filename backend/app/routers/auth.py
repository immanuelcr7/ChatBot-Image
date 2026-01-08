from fastapi import APIRouter, HTTPException, Form, Body
from pydantic import BaseModel
from typing import Optional
import json
from ..database import create_user, authenticate_user, find_user_by_google_id, get_user_sessions

router = APIRouter()

class GoogleAuth(BaseModel):
    google_id: str
    email: str
    name: str
    avatar: Optional[str] = None

@router.post("/register")
async def register(username: str = Form(...), password: str = Form(...), email: str = Form(None)):
    user_id = create_user(username=username, password=password, email=email)
    if user_id:
        return {"id": user_id, "username": username, "email": email}
    raise HTTPException(status_code=400, detail="Username or email already exists")

@router.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    user_id = authenticate_user(username, password)
    if user_id:
        return {"id": user_id, "username": username}
    raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/google-login")
async def google_login(data: GoogleAuth):
    # Check if user exists
    user = find_user_by_google_id(data.google_id)
    if user:
        return {"id": user[0], "username": user[1], "email": user[2], "avatar": user[3]}
    
    # Create new user for google
    user_id = create_user(username=data.name, email=data.email, google_id=data.google_id, avatar=data.avatar)
    if user_id:
        return {"id": user_id, "username": data.name, "email": data.email, "avatar": data.avatar}
    
    raise HTTPException(status_code=500, detail="Failed to create account")

@router.get("/history/{user_id}")
async def get_history(user_id: str):
    sessions = get_user_sessions(user_id)
    # Parse JSON messages for the frontend
    history = []
    for s in sessions:
        history.append({
            "id": s[0],
            "image_preview": s[1],
            "messages": json.loads(s[2]),
            "last_updated": s[3]
        })
    return {"history": history}
