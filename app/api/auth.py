from uuid import uuid4

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models.auth import AuthRequest, TokenResponse, UserResponse
from app.services.database import Database

router = APIRouter(prefix="/auth", tags=["auth"])
database = Database(get_settings().database_path)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: AuthRequest) -> UserResponse:
    user_id = str(uuid4())
    try:
        database.execute(
            "INSERT INTO users (id, username, password_hash, created_at) VALUES (?, ?, ?, datetime('now'))",
            (user_id, request.username, hash_password(request.password)),
        )
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            raise HTTPException(status_code=409, detail="Username is already registered.") from exc
        raise HTTPException(status_code=500, detail="Could not create account.") from exc
    return UserResponse(user_id=user_id, username=request.username)


@router.post("/login", response_model=TokenResponse)
def login(request: AuthRequest) -> TokenResponse:
    user = database.fetchone("SELECT id, username, password_hash FROM users WHERE username = ?", (request.username,))
    if user is None or not verify_password(request.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return TokenResponse(access_token=create_access_token(user["id"], user["username"]))