"""
Camera Management Routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_admin_user
from app.models import User, Camera
from app.schemas.cameras import (
    CameraCreate,
    CameraUpdate,
    CameraResponse,
    CameraListResponse,
    CameraDetailResponse
)

router = APIRouter(prefix="/api/cameras", tags=["Cameras"])

# ========================
# GET - All Cameras (All Role)
# ========================
@router.get("", response_model=list[CameraListResponse])
async def get_cameras(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Menampilkan daftar semua kamera
    
    Akses: Semua role (Admin_IT, Pengawas_K3, Manager_HR)
    """
    cameras = db.query(Camera).all()
    return cameras

# ========================
# GET - Camera Detail (All Role)
# ========================
@router.get("/{camera_id}", response_model=CameraDetailResponse)
async def get_camera_detail(
    camera_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mengambil detail satu kamera spesifik
    
    Akses: Semua role (Admin_IT, Pengawas_K3, Manager_HR)
    """
    try:
        camera_uuid = UUID(camera_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid camera ID format"
        )
    
    camera = db.query(Camera).filter(Camera.id == camera_uuid).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    return camera

# ========================
# POST - Create Camera (Admin Only)
# ========================
@router.post("", response_model=CameraDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_camera(
    camera_data: CameraCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Menambah data kamera baru
    
    Akses: Hanya Admin_IT
    """
    # Check if camera name already exists in this location
    existing_camera = db.query(Camera).filter(
        Camera.name == camera_data.name,
        Camera.location == camera_data.location
    ).first()
    
    if existing_camera:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Camera dengan nama dan lokasi yang sama sudah ada"
        )
    
    new_camera = Camera(
        name=camera_data.name,
        location=camera_data.location,
        rtsp_url=camera_data.rtsp_url,
        status=camera_data.status
    )
    
    db.add(new_camera)
    db.commit()
    db.refresh(new_camera)
    
    return new_camera

# ========================
# PUT - Update Camera (Admin Only)
# ========================
@router.put("/{camera_id}", response_model=CameraDetailResponse)
async def update_camera(
    camera_id: str,
    camera_data: CameraUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Mengubah data kamera
    
    Akses: Hanya Admin_IT
    """
    try:
        camera_uuid = UUID(camera_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid camera ID format"
        )
    
    camera = db.query(Camera).filter(Camera.id == camera_uuid).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    # Check duplicate name+location if updating these fields
    if camera_data.name or camera_data.location:
        existing_camera = db.query(Camera).filter(
            Camera.id != camera_uuid,
            Camera.name == (camera_data.name or camera.name),
            Camera.location == (camera_data.location or camera.location)
        ).first()
        
        if existing_camera:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Camera dengan nama dan lokasi yang sama sudah ada"
            )
    
    # Update fields if provided
    if camera_data.name is not None:
        camera.name = camera_data.name
    if camera_data.location is not None:
        camera.location = camera_data.location
    if camera_data.rtsp_url is not None:
        camera.rtsp_url = camera_data.rtsp_url
    if camera_data.status is not None:
        camera.status = camera_data.status
    
    db.commit()
    db.refresh(camera)
    
    return camera

# ========================
# DELETE - Delete Camera (Admin Only)
# ========================
@router.delete("/{camera_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_camera(
    camera_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    Menghapus kamera
    
    Akses: Hanya Admin_IT
    """
    try:
        camera_uuid = UUID(camera_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid camera ID format"
        )
    
    camera = db.query(Camera).filter(Camera.id == camera_uuid).first()
    if not camera:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camera not found"
        )
    
    db.delete(camera)
    db.commit()
    
    return None
