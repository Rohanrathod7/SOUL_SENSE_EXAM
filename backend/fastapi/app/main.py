from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .routers import health, auth

settings = get_settings()

def create_app() -> FastAPI:
    app = FastAPI(title="SoulSense FastAPI")

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(auth.router, prefix="/auth", tags=["authentication"])

    @app.on_event("startup")
    async def startup_event():
        app.state.settings = settings

    return app


app = create_app()
