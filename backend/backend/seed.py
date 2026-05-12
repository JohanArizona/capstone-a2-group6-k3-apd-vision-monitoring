"""
Database initialization dan seeding script
Run ini setelah migrations untuk populate initial data
"""
import os
import sys
from bcrypt import hashpw, gensalt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import Base, engine
from app.models import User, Camera

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

def hash_password(password: str) -> str:
    """Hash password menggunakan bcrypt"""
    return hashpw(password.encode('utf-8'), gensalt()).decode('utf-8')

def seed_admin_users():
    """Seed admin users"""
    min_admin = db.query(User).filter(User.role == 'Admin_IT').first()
    if min_admin:
        print("✓ Admin users sudah ada")
        return
    
    admin_user = User(
        username="admin",
        password=hash_password("admin123"),
        full_name="Admin System",
        email="admin@apd-vision.com",
        role='Admin_IT',
        is_active=True
    )
    
    pengawas_user = User(
        username="pengawas",
        password=hash_password("pengawas123"),
        full_name="Pengawas K3",
        email="pengawas@apd-vision.com",
        role='Pengawas_K3',
        is_active=True
    )
    
    manager_user = User(
        username="manager",
        password=hash_password("manager123"),
        full_name="Manager HR",
        email="manager@apd-vision.com",
        role='Manager_HR',
        is_active=True
    )
    
    db.add_all([admin_user, pengawas_user, manager_user])
    db.commit()
    print("✓ Admin users created")
    print(f"  - Username: admin, Password: admin123")
    print(f"  - Username: pengawas, Password: pengawas123")
    print(f"  - Username: manager, Password: manager123")

def seed_cameras():
    """Seed initial camera data"""
    existing_cameras = db.query(Camera).count()
    if existing_cameras > 0:
        print(f"✓ Cameras sudah ada ({existing_cameras} cameras)")
        return
    
    cameras = [
        Camera(
            name="Lokasi Produksi A",
            location="Lantai 1 - Area Produksi",
            rtsp_url="rtsp://192.168.1.100:554/stream",
            status='Active'
        ),
        Camera(
            name="Lokasi Produksi B",
            location="Lantai 2 - Area Produksi",
            rtsp_url="rtsp://192.168.1.101:554/stream",
            status='Active'
        ),
        Camera(
            name="Lokasi Warehouse",
            location="Gudang - Area Penyimpanan",
            rtsp_url="rtsp://192.168.1.102:554/stream",
            status='Active'
        ),
    ]
    
    db.add_all(cameras)
    db.commit()
    print("✓ Cameras created")
    for camera in cameras:
        print(f"  - {camera.name} @ {camera.location}")

def main():
    """Main seeding function"""
    print("\n" + "="*60)
    print("DATABASE SEEDING")
    print("="*60 + "\n")
    
    try:
        seed_admin_users()
        seed_cameras()
        print("\n" + "="*60)
        print("✓ Seeding completed successfully!")
        print("="*60 + "\n")
    except Exception as e:
        print(f"\n✗ Error during seeding: {e}\n")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
