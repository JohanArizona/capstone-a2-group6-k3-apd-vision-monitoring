from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from app.core import engine, Base
from app.models import User, Camera
from app.models.violation import Violation
from app.models.detection_stats import DetectionStats
from app.models.notification import Notification
from app.api.v1 import auth, users, cameras, detection_stats, violations, notifications

# Create all tables
Base.metadata.create_all(bind=engine)

application = FastAPI(
    title="APD Vision Monitoring API",
    description="API untuk monitoring APD dengan vision detection",
    version="1.0.0"
)

# Add CORS middleware
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploaded violation snapshots
uploads_dir = Path("/app/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
application.mount("/uploads", StaticFiles(directory="/app/uploads"), name="uploads")

# Include routers
application.include_router(auth.router)
application.include_router(users.router)
application.include_router(cameras.router)
application.include_router(detection_stats.router)
application.include_router(violations.router)
application.include_router(notifications.router)

@application.get("/test")
def read_root():
    return {
        "status": "ok",
        "message": "Backend is running!",
        "database": "connected"
    }

@application.get("/health")
def health_check():
    return {"status": "healthy"}