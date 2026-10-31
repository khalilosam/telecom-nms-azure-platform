from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/v1/sites", tags=["Cell Sites"])

@router.get("", response_model=List[schemas.CellSiteResponse])
def list_cell_sites(
    technology: Optional[str] = Query(None, description="Filter by tech e.g. 5G-NR, 4G-LTE"),
    region: Optional[str] = Query(None, description="Filter by region e.g. East Africa"),
    status: Optional[str] = Query(None, description="Filter by status e.g. OPERATIONAL, DOWN"),
    db: Session = Depends(get_db)
):
    query = db.query(models.CellSite)
    if technology:
        query = query.filter(models.CellSite.technology == technology)
    if region:
        query = query.filter(models.CellSite.region == region)
    if status:
        query = query.filter(models.CellSite.status == status)
    return query.all()

@router.get("/{site_id}", response_model=schemas.CellSiteResponse)
def get_cell_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(models.CellSite).filter(models.CellSite.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail=f"Cell site with ID {site_id} not found")
    return site

@router.post("", response_model=schemas.CellSiteResponse, status_code=201)
def create_cell_site(payload: schemas.CellSiteCreate, db: Session = Depends(get_db)):
    existing = db.query(models.CellSite).filter(models.CellSite.site_code == payload.site_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Site code '{payload.site_code}' already exists")
    site = models.CellSite(**payload.dict())
    db.add(site)
    db.commit()
    db.refresh(site)
    return site
