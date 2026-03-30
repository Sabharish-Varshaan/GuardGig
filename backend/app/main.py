from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routes.auth import router as auth_router
from .routes.onboarding import router as onboarding_router

settings = get_settings()

app = FastAPI(
    title="GuardGig API",
    version="0.1.0",
    description="Registration, login, and onboarding APIs for GuardGig"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "environment": settings.app_env
    }


app.include_router(auth_router)
app.include_router(onboarding_router)
