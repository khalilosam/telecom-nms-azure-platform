import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class CellSite(Base):
    __tablename__ = "cell_sites"

    id = Column(Integer, primary_key=True, index=True)
    site_code = Column(String(32), unique=True, index=True, nullable=False)
    site_name = Column(String(128), nullable=False)
    region = Column(String(64), nullable=False)
    technology = Column(String(16), nullable=False) # 2G-GSM, 3G-UMTS, 4G-LTE, 5G-NR
    ip_address = Column(String(45), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status = Column(String(20), default="OPERATIONAL") # OPERATIONAL, DEGRADED, DOWN
    last_heartbeat = Column(DateTime, default=datetime.datetime.utcnow)

    alarms = relationship("Alarm", back_populates="site", cascade="all, delete-orphan")
    metrics = relationship("TelemetryMetric", back_populates="site", cascade="all, delete-orphan")

class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("cell_sites.id"), nullable=False)
    site_code = Column(String(32), nullable=False)
    severity = Column(String(16), nullable=False) # CRITICAL, MAJOR, MINOR, WARNING
    alarm_type = Column(String(64), nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    raised_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(64), nullable=True)

    site = relationship("CellSite", back_populates="alarms")

class TelemetryMetric(Base):
    __tablename__ = "telemetry_metrics"

    id = Column(Integer, primary_key=True, index=True)
    site_id = Column(Integer, ForeignKey("cell_sites.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    rrc_connected_users = Column(Integer, default=0)
    prb_utilization_pct = Column(Float, default=0.0)
    packet_loss_pct = Column(Float, default=0.0)
    throughput_mbps = Column(Float, default=0.0)
    vswr_ratio = Column(Float, default=1.15)

    site = relationship("CellSite", back_populates="metrics")
