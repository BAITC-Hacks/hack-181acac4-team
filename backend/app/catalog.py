from fastapi import APIRouter


router = APIRouter(prefix="/api/tasks", tags=["catalog"])

# ANU-9: GET /api/tasks and GET /api/tasks/{id}.
