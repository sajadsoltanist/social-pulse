from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes.auth import router as auth_router
from app.infrastructure.db.database import create_tables, close_db
from app.core.exceptions import (
    SocialPulseException,
    InvalidCredentialsError,
    UserNotFoundError,
    TokenExpiredError,
    ProfileNotFoundError,
    ProfileAlreadyExistsError,
    AlertNotFoundError
)
from app.config import get_config

config = get_config()

app = FastAPI(
    title="SocialPulse API",
    description="Instagram follower tracking and milestone alerts",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(InvalidCredentialsError)
async def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": str(exc),
            "error_code": "INVALID_CREDENTIALS",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(UserNotFoundError)
async def user_not_found_handler(request: Request, exc: UserNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "error_code": "USER_NOT_FOUND",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(TokenExpiredError)
async def token_expired_handler(request: Request, exc: TokenExpiredError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": str(exc),
            "error_code": "TOKEN_EXPIRED",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(ProfileNotFoundError)
async def profile_not_found_handler(request: Request, exc: ProfileNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "error_code": "PROFILE_NOT_FOUND",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(ProfileAlreadyExistsError)
async def profile_already_exists_handler(request: Request, exc: ProfileAlreadyExistsError):
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "detail": str(exc),
            "error_code": "PROFILE_ALREADY_EXISTS",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(AlertNotFoundError)
async def alert_not_found_handler(request: Request, exc: AlertNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "detail": str(exc),
            "error_code": "ALERT_NOT_FOUND",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(SocialPulseException)
async def social_pulse_exception_handler(request: Request, exc: SocialPulseException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": str(exc),
            "error_code": "SOCIAL_PULSE_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_ERROR",
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.on_event("startup")
async def startup_event():
    await create_tables()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


app.include_router(auth_router, prefix="/auth", tags=["authentication"]) 