"""FastAPI application factory for the AI DevSecOps cockpit."""

from fastapi import FastAPI
from pydantic import BaseModel

from devsecops_ai import __version__


class HealthResponse(BaseModel):
    status: str
    version: str


def create_app() -> FastAPI:
    app = FastAPI(title="AI DevSecOps Cockpit", version=__version__)

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", version=__version__)

    return app


app = create_app()
