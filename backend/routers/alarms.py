from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/v1/alarms", tags=["Fault Management & Alarms"])

@router.get("", response_model=List[schemas.AlarmResponse])
def list_alarms(
    severity: Optional[str] = Query(None, description="CRITICAL, MAJOR, MINOR, WARNING"),
    acknowledged: Optional[bool] = Query(None, description="Filter by ack status"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Alarm)
    if severity:
        query = query.filter(models.Alarm.severity == severity.upper())
    if acknowledged is not None:
        query = query.filter(models.Alarm.is_acknowledged == acknowledged)
    return query.order_by(models.Alarm.raised_at.desc()).all()

@router.post("", response_model=schemas.AlarmResponse, status_code=201)
def trigger_alarm(payload: schemas.AlarmCreate, db: Session = Depends(get_db)):
    site = db.query(models.CellSite).filter(models.CellSite.id == payload.site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site ID does not exist")
    
    alarm = models.Alarm(
        site_id=payload.site_id,
        site_code=payload.site_code,
        severity=payload.severity.upper(),
        alarm_type=payload.alarm_type,
        title=payload.title,
        details=payload.details
    )
    db.add(alarm)
    db.commit()
    db.refresh(alarm)
    return alarm

@router.post("/{alarm_id}/ack", response_model=schemas.AlarmResponse)
def acknowledge_alarm(alarm_id: int, operator: str = "NOC_ENGINEER", db: Session = Depends(get_db)):
    alarm = db.query(models.Alarm).filter(models.Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    alarm.is_acknowledged = True
    alarm.acknowledged_by = operator
    db.commit()
    db.refresh(alarm)
    return alarm

@router.post("/{alarm_id}/resolve", response_model=schemas.AlarmResponse)
def resolve_alarm(alarm_id: int, db: Session = Depends(get_db)):
    alarm = db.query(models.Alarm).filter(models.Alarm.id == alarm_id).first()
    if not alarm:
        raise HTTPException(status_code=404, detail="Alarm not found")
    alarm.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(alarm)
    return alarm
