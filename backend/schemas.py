from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# Site Schemas
class CellSiteBase(BaseModel):
    site_code: str = Field(..., example="NBO-5G-0101")
    site_name: str = Field(..., example="Nairobi Central CBD Macro")
    region: str = Field(..., example="East Africa")
    technology: str = Field(..., example="5G-NR")
    ip_address: str = Field(..., example="10.204.12.10")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    status: Optional[str] = "OPERATIONAL"

class CellSiteCreate(CellSiteBase):
    pass

class CellSiteResponse(CellSiteBase):
    id: int
    last_heartbeat: Optional[datetime] = None

    class Config:
        from_attributes = True

# Alarm Schemas
class AlarmBase(BaseModel):
    site_code: str
    severity: str # CRITICAL, MAJOR, MINOR, WARNING
    alarm_type: str
    title: str
    details: Optional[str] = None

class AlarmCreate(AlarmBase):
    site_id: int

class AlarmResponse(AlarmBase):
    id: int
    site_id: int
    raised_at: datetime
    resolved_at: Optional[datetime] = None
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None

    class Config:
        from_attributes = True

# Telemetry Schemas
class MetricResponse(BaseModel):
    id: int
    site_id: int
    timestamp: datetime
    rrc_connected_users: int
    prb_utilization_pct: float
    packet_loss_pct: float
    throughput_mbps: float
    vswr_ratio: float

    class Config:
        from_attributes = True
