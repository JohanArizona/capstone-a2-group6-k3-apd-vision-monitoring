"""
Detection Statistics Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import User, DetectionStats, Camera
from app.schemas.detection_stats import (
    DetectionStatsCreate,
    DetectionStatsResponse,
    DetectionStatsListResponse,
    DetectionStatsSummary
)

router = APIRouter(prefix="/api/detections", tags=["Detection Statistics"])

# ========================
# POST - Create Detection Stats (Edge AI)
# ========================
@router.post("/stats", response_model=DetectionStatsResponse, status_code=status.HTTP_201_CREATED)
async def create_detection_stats(
    stats_data: DetectionStatsCreate,
    db: Session = Depends(get_db)
):
    """
    Menerima data agregasi jumlah pekerja dari Edge AI
    
    Akses: Edge AI / System Integration
    (Tanpa auth - dari trusted edge device)
    """
    # Validate camera exists
    camera = db.query(Camera).filter(Camera.id == stats_data.camera_id).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Validate compliance logic
    if stats_data.compliant_workers + stats_data.violating_workers > stats_data.total_workers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="compliant_workers + violating_workers tidak boleh lebih besar dari total_workers"
        )
    
    new_stats = DetectionStats(
        camera_id=stats_data.camera_id,
        total_workers=stats_data.total_workers,
        compliant_workers=stats_data.compliant_workers,
        violating_workers=stats_data.violating_workers,
        timestamp=stats_data.timestamp  # Will be None if not provided, server will use current time
    )
    
    db.add(new_stats)
    db.commit()
    db.refresh(new_stats)
    
    return new_stats

# ========================
# GET - List Detection Stats (Dashboard)
# ========================
@router.get("/stats", response_model=list[DetectionStatsListResponse])
async def get_detection_stats(
    camera_id: UUID = Query(None, description="Filter by camera ID (optional)"),
    start_date: datetime = Query(None, description="Start date (ISO format: 2026-04-10T00:00:00)"),
    end_date: datetime = Query(None, description="End date (ISO format: 2026-04-10T23:59:59)"),
    limit: int = Query(500, ge=1, le=5000, description="Limit records (max 5000)"),
    offset: int = Query(0, ge=0, description="Offset records"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mengambil data statistik deteksi untuk Line/Bar Chart
    
    Akses: Semua role (Admin_IT, Pengawas_K3, Manager_HR)
    
    Query Parameters:
    - camera_id: Filter by specific camera (optional)
    - start_date: Start date range (optional)
    - end_date: End date range (optional)
    - limit: Max records to return (default 500, max 5000)
    - offset: Pagination offset (default 0)
    """
    query = db.query(DetectionStats)
    
    # Apply filters
    filters = []
    
    if camera_id:
        filters.append(DetectionStats.camera_id == camera_id)
    
    if start_date:
        filters.append(DetectionStats.timestamp >= start_date)
    
    if end_date:
        filters.append(DetectionStats.timestamp <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    # Order by timestamp descending (newest first)
    query = query.order_by(DetectionStats.timestamp.desc())
    
    # Apply pagination
    total_count = query.count()
    stats = query.offset(offset).limit(limit).all()
    
    return stats

# ========================
# GET - Summary Statistics (for Dashboard Analytics)
# ========================
@router.get("/stats/summary", response_model=DetectionStatsSummary)
async def get_detection_stats_summary(
    camera_id: UUID = Query(None, description="Filter by camera ID (optional)"),
    start_date: datetime = Query(None, description="Start date for summary period"),
    end_date: datetime = Query(None, description="End date for summary period"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mengambil summary statistik untuk analytics dashboard
    
    Akses: Semua role (Admin_IT, Pengawas_K3, Manager_HR)
    
    Mengembalikan:
    - Total records dalam periode
    - Rata-rata jumlah pekerja
    - Rata-rata compliance rate
    - Peak jumlah pekerja
    - Total violations
    """
    query = db.query(DetectionStats)
    
    # Apply filters
    filters = []
    
    if camera_id:
        filters.append(DetectionStats.camera_id == camera_id)
    
    if start_date:
        filters.append(DetectionStats.timestamp >= start_date)
    
    if end_date:
        filters.append(DetectionStats.timestamp <= end_date)
    
    if filters:
        query = query.filter(and_(*filters))
    
    stats_list = query.all()
    
    if not stats_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No statistics data found for the given period"
        )
    
    # Calculate summary
    total_records = len(stats_list)
    average_workers = sum(s.total_workers for s in stats_list) / total_records if total_records > 0 else 0
    total_violations = sum(s.violating_workers for s in stats_list)
    
    # Calculate compliance rate
    total_compliant = sum(s.compliant_workers for s in stats_list)
    total_all = sum(s.total_workers for s in stats_list)
    average_compliance_rate = (total_compliant / total_all * 100) if total_all > 0 else 0
    
    # Peak workers
    peak_workers = max(s.total_workers for s in stats_list) if stats_list else 0
    
    return DetectionStatsSummary(
        total_records=total_records,
        average_workers=round(average_workers, 2),
        average_compliance_rate=round(average_compliance_rate, 2),
        peak_workers=peak_workers,
        total_violations=total_violations
    )
