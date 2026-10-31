import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
import models
from routers import sites, alarms, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("telecom-nms")

def seed_initial_data():
    """Seed sample cell sites and alarms if tables are empty."""
    db = SessionLocal()
    try:
        if db.query(models.CellSite).count() == 0:
            logger.info("Initializing database with baseline telecom cell sites...")
            sample_sites = [
                models.CellSite(site_code="NBO-5G-0101", site_name="Nairobi Central CBD Macro", region="East Africa", technology="5G-NR", ip_address="10.204.12.10", latitude=-1.286389, longitude=36.817223, status="OPERATIONAL"),
                models.CellSite(site_code="NBO-4G-0102", site_name="Westlands Commercial Hub", region="East Africa", technology="4G-LTE", ip_address="10.204.12.11", latitude=-1.2682, longitude=36.8048, status="OPERATIONAL"),
                models.CellSite(site_code="LSK-5G-0201", site_name="Lusaka Industrial Area", region="Southern Africa", technology="5G-NR", ip_address="10.205.18.20", latitude=-15.4167, longitude=28.2833, status="DEGRADED"),
                models.CellSite(site_code="LSK-4G-0202", site_name="Cairo Road Core Site", region="Southern Africa", technology="4G-LTE", ip_address="10.205.18.21", latitude=-15.4215, longitude=28.2829, status="OPERATIONAL"),
                models.CellSite(site_code="WDH-5G-0301", site_name="Windhoek Independence Ave", region="Southern Africa", technology="5G-NR", ip_address="10.206.24.30", latitude=-22.5609, longitude=17.0658, status="OPERATIONAL"),
                models.CellSite(site_code="LLW-4G-0401", site_name="Lilongwe Capital City BTS", region="Southern Africa", technology="4G-LTE", ip_address="10.207.30.40", latitude=-13.9833, longitude=33.7833, status="DOWN"),
                models.CellSite(site_code="MBA-4G-0103", site_name="Mombasa Port Gateway", region="East Africa", technology="4G-LTE", ip_address="10.204.14.15", latitude=-4.0435, longitude=39.6682, status="OPERATIONAL"),
                models.CellSite(site_code="NDL-3G-0205", site_name="Ndola Copperbelt NodeB", region="Southern Africa", technology="3G-UMTS", ip_address="10.205.22.18", latitude=-12.9667, longitude=28.6333, status="OPERATIONAL"),
            ]
            db.add_all(sample_sites)
            db.commit()

            # Seed alarms for the degraded/down sites
            site_down = db.query(models.CellSite).filter(models.CellSite.site_code == "LLW-4G-0401").first()
            site_degraded = db.query(models.CellSite).filter(models.CellSite.site_code == "LSK-5G-0201").first()
            
            if site_down:
                db.add(models.Alarm(
                    site_id=site_down.id,
                    site_code=site_down.site_code,
                    severity="CRITICAL",
                    alarm_type="POWER_OUTAGE",
                    title="Mains Power Failure - Battery Backup Discharging",
                    details="AC Mains supply loss detected by power distribution unit. Fuel generator auto-start failed."
                ))
            if site_degraded:
                db.add(models.Alarm(
                    site_id=site_degraded.id,
                    site_code=site_degraded.site_code,
                    severity="MAJOR",
                    alarm_type="RF_VSWR_HIGH",
                    title="VSWR High Threshold Exceeded (Sector 2 Antenna)",
                    details="Antenna port VSWR measured at 1.85. Possible feeder cable moisture ingress or loose jumper."
                ))
            db.commit()
            logger.info("Baseline data seeded successfully.")
    except Exception as e:
        logger.error(f"Error during baseline seed: {e}")
        db.rollback()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables if not present
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield
    # Teardown logic if needed

app = FastAPI(
    title="Telecom Network Management System (NMS) API",
    description="Enterprise REST API for 4G/5G Radio Access Network (RAN) telemetry, fault management, and cell inventory.",
    version="2.4.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(sites.router)
app.include_router(alarms.router)

@app.get("/")
def root():
    return {
        "service": "Telecom NMS API",
        "documentation": "/docs",
        "health": "/healthz",
        "status": "online"
    }
