"""Entrypoint for serving FastAPI with Uvicorn."""

from __future__ import annotations

import uvicorn

from app.config.settings import settings


def run() -> None:
    """Run the API server."""
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=False,
    )


if __name__ == "__main__":
    run()
