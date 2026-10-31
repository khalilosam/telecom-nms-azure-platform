from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db

router = APIRouter(tags=["Health & Probes"])

@router.get("/healthz", status_code=status.HTTP_200_OK)
def liveness():
    return {"status": "healthy", "service": "telecom-nms-backend", "engine": "FastAPI/Uvicorn"}

@router.get("/readyz")
def readiness(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected",
            "provider": "Azure Database for PostgreSQL Flexible Server"
        }
    except Exception as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "database": "disconnected",
            "error": str(exc)
        }
