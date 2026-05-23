"""FastAPI application entrypoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tastetrail.api.routes import router
from tastetrail.store import RestaurantStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.store = RestaurantStore.load()
    except FileNotFoundError as exc:
        app.state.store = None
        app.state.load_error = str(exc)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="TasteTrail-AI",
        description="AI-powered restaurant recommendations (Groq + Zomato data)",
        version="0.1.0",
        lifespan=lifespan,
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    @app.get("/")
    def root() -> dict:
        return {
            "service": "TasteTrail-AI",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app()
