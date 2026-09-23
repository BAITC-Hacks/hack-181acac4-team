from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from . import models  # Register tables before create_all.
from .cards import router as cards_router
from .catalog import router as catalog_router
from .db import Base, engine, get_db
from .schemas import TeamProfile
from .drafts import router as drafts_router
from .proposals import router as proposals_router
from .ai.client import AIError
from .services.intake import IntakeError


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="HackAlem AI", lifespan=lifespan)
app.include_router(drafts_router)
app.include_router(cards_router)
app.include_router(catalog_router)
app.include_router(proposals_router)


@app.get("/api/teams", response_model=list[TeamProfile])
def list_teams(db: Session = Depends(get_db)):
    return list(db.scalars(select(models.TeamProfile).order_by(models.TeamProfile.name)))


@app.exception_handler(IntakeError)
async def intake_error(_request, error: IntakeError):
    return JSONResponse(status_code=error.status, content={"detail": str(error)})


@app.exception_handler(AIError)
async def ai_error(_request, error: AIError):
    return JSONResponse(status_code=503, content={"detail": str(error)})


@app.get("/api/health")
def health() -> dict[str, str]:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return {"status": "ok"}
