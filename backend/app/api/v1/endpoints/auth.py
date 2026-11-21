"""Authentication endpoints: Register, Login, and Current Recruiter Profile."""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends
from app.core.database import get_database
from app.core.security import hash_password, verify_password, create_access_token, get_current_recruiter
from app.schemas.auth import (
    RecruiterRegisterRequest,
    RecruiterLoginRequest,
    RecruiterResponse,
    AuthTokenResponse,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new recruiter account",
    description="Registers a recruiter with validated name, email, and password. Hashes passwords with bcrypt and returns an auth token.",
)
async def register_recruiter(payload: RecruiterRegisterRequest) -> AuthTokenResponse:
    """Register a new recruiter."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check that MongoDB is running.",
        )

    normalized_email = payload.email.lower().strip()

    # Prevent duplicate accounts
    existing = await database.recruiters.find_one({"email": normalized_email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please sign in instead.",
        )

    # Securely hash password
    hashed_pwd = hash_password(payload.password)
    recruiter_id = f"rec_{uuid.uuid4().hex[:12]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    recruiter_doc = {
        "id": recruiter_id,
        "full_name": payload.full_name,
        "email": normalized_email,
        "hashed_password": hashed_pwd,
        "created_at": now_iso,
    }

    try:
        await database.recruiters.insert_one(recruiter_doc)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create recruiter record: {str(exc)}",
        )

    # Issue access token
    access_token = create_access_token(data={"sub": recruiter_id, "email": normalized_email})

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        recruiter=RecruiterResponse(
            id=recruiter_id,
            full_name=payload.full_name,
            email=normalized_email,
            created_at=now_iso,
        ),
    )


@router.post(
    "/login",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Recruiter login",
    description="Authenticates recruiter with email and password, returning JWT access token.",
)
async def login_recruiter(payload: RecruiterLoginRequest) -> AuthTokenResponse:
    """Authenticate recruiter and return JWT token."""
    database = get_database()
    if database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check that MongoDB is running.",
        )

    normalized_email = payload.email.lower().strip()
    recruiter = await database.recruiters.find_one({"email": normalized_email})

    if not recruiter:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify bcrypt password
    is_valid = verify_password(payload.password, recruiter.get("hashed_password", ""))
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": recruiter["id"], "email": normalized_email}
    )

    return AuthTokenResponse(
        access_token=access_token,
        token_type="bearer",
        recruiter=RecruiterResponse(
            id=recruiter["id"],
            full_name=recruiter["full_name"],
            email=recruiter["email"],
            created_at=recruiter.get("created_at"),
        ),
    )


@router.get(
    "/me",
    response_model=RecruiterResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current recruiter profile",
    description="Validates Bearer token and returns authenticated recruiter details.",
)
async def get_my_profile(current_recruiter: dict = Depends(get_current_recruiter)) -> RecruiterResponse:
    """Return verified current recruiter details."""
    return RecruiterResponse(
        id=current_recruiter["id"],
        full_name=current_recruiter["full_name"],
        email=current_recruiter["email"],
        created_at=current_recruiter.get("created_at"),
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Recruiter logout",
    description="Acknowledges recruiter logout; client clears local token.",
)
async def logout_recruiter(current_recruiter: dict = Depends(get_current_recruiter)):
    """Handle recruiter logout."""
    return {"status": "success", "message": "Successfully logged out."}
