"""Authentication routes."""
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends

from ..models.schemas import RegisterInput, LoginInput
from ..services.auth import hash_password, verify_password, create_token, get_current_user
from ..database import get_db
from ..utils.responses import success_response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
async def register(inp: RegisterInput):
    """Register a new user."""
    db = get_db()
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": inp.email})
    if existing_user:
        raise HTTPException(400, "Email already registered")
    
    # Create new user
    user_id = str(uuid.uuid4())
    user_data = {
        "id": user_id,
        "name": inp.name,
        "email": inp.email,
        "password": hash_password(inp.password),
        "riskPersonality": "Undetermined",
        "financialHealthScore": 0,
        "createdAt": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_data)
    
    # Generate JWT token
    token = create_token(user_id, inp.email)
    
    return success_response(
        data={
            "token": token,
            "user": {"id": user_id, "name": inp.name, "email": inp.email}
        },
        message="Registration successful"
    )


@router.post("/login")
async def login(inp: LoginInput):
    """Login user and return JWT token."""
    db = get_db()
    
    # Find user by email
    user = await db.users.find_one({"email": inp.email}, {"_id": 0})
    
    if not user or not verify_password(inp.password, user["password"]):
        raise HTTPException(401, "Invalid credentials")
    
    # Generate JWT token
    token = create_token(user["id"], user["email"])
    
    return success_response(
        data={
            "token": token,
            "user": {"id": user["id"], "name": user["name"], "email": user["email"]}
        },
        message="Login successful"
    )


@router.get("/me")
async def get_me(user=Depends(get_current_user)):
    """Get current user profile."""
    return success_response(data=user, message="User profile")
