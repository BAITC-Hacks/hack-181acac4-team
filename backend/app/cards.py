from fastapi import APIRouter


router = APIRouter(prefix="/api/cards", tags=["cards"])

# ANU-6: PATCH /api/cards/{id}, POST /api/cards/{id}/confirm and /publish.
