from fastapi import APIRouter


router = APIRouter(prefix="/api/drafts", tags=["drafts"])

# ANU-6: POST /api/drafts and POST /api/drafts/{id}/answers.
