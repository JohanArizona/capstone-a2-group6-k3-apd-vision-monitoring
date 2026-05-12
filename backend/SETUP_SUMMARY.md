# Database Setup Summary

## Selesai! ✓

Berikut apa yang telah di-setup untuk auto migrations dan seeding:

## Struktur Backend

```
backend/
├── main.py                          # FastAPI app with Base.metadata.create_all()
├── entrypoint.sh                    # Auto-run migrations → seed → start app
├── seed.py                          # Seed initial data (users, cameras)
├── db_init.py                       # Quick DB check/reset utility
├── Dockerfile                       # Updated dengan entrypoint
├── requirements.txt                 # Added: psycopg2, bcrypt, pydantic[email]
├── alembic.ini                      # Updated DATABASE_URL
│
├── alembic/
│   ├── env.py                       # Updated untuk load models
│   └── versions/
│       ├── 001_initial.py           # Complete schema creation
│       └── __init__.py
│
├── app/
│   ├── core/
│   │   ├── database.py              # SQLAlchemy setup (engine, SessionLocal)
│   │   └── __init__.py
│   │
│   ├── models/
│   │   ├── __init__.py              # Import all models
│   │   ├── user.py                  # User model + roles
│   │   ├── camera.py                # Camera model + status
│   │   ├── violation.py             # Violation model + status
│   │   ├── detection_stats.py       # Detection stats model
│   │   └── notification.py          # Notification model
│   │
│   ├── schemas/
│   │   ├── __init__.py              # Export all schemas
│   │   ├── user.py                  # User Pydantic models
│   │   ├── camera.py                # Camera Pydantic models
│   │   └── violation.py             # Violation Pydantic models
│   │
│   ├── api/                         # API routes (untuk development)
│   ├── services/                    # Business logic services
│   └── __init__.py
│
├── MIGRATION_GUIDE.md               # Detailed migration documentation
└── .dockerignore
```

## Database Schema

```sql
Enums:
- user_role: Admin_IT, Pengawas_K3, Manager_HR
- camera_status: Active, Inactive, Maintenance
- violation_status: Unverified, Verified, False_Positive

Tables:
1. users           - Admin, pengawas, manager
2. camera          - RTSP streams dari berbagai lokasi
3. violations      - Detected APD violations
4. detection_stats - Stats per camera per timestamp
5. notification    - Alerts untuk users

Indexes:
- violations(timestamp)
- detection_stats(timestamp)
- notification(user_id)
- users(username, email) - UNIQUE
- camera(name) - UNIQUE via constraints
```

## Otomasi

### Saat `docker-compose up --build`:

1. **entrypoint.sh** (main.py tidak langsung jalan)
   ```bash
   wait for database...
   run alembic upgrade head   # Create tables, indexes, enums
   python seed.py             # Populate initial data
   exec uvicorn main:application ...
   ```

2. **seed.py** membuat:
   - 3 admin users (admin, pengawas, manager)
   - 3 cameras (Produksi A, B, Warehouse)

3. **main.py** on startup:
   ```python
   Base.metadata.create_all(bind=engine)  # Redundant but safe
   ```

## Quick Commands

```bash
# Start everything (auto includes migrations + seeding)
docker-compose up --build

# Check DB status
docker exec -it capstone-backend python db_init.py

# Create new migration (masuk container dulu)
docker exec -it capstone-backend bash
alembic revision --autogenerate -m "Add new table"
alembic upgrade head

# Seed saja (jika sudah ada tables)
docker exec -it capstone-backend python seed.py

# Reset DB (delete all data)
docker-compose down -v
docker-compose up --build
```

## Requirements Added

```
psycopg2-binary==2.9.9     # PostgreSQL driver
python-dotenv==1.0.0       # Load .env
bcrypt==4.1.2              # Password hashing
python-multipart==0.0.6    # FastAPI form data
pydantic==2.5.0            # Data validation
pydantic-settings==2.1.0   # Settings management
pydantic[email]==2.5.0     # Email validation
```

## Database Credentials

```
Host: db
Port: 5432
Username: capstone_user
Password: capstone_password
Database: capstone_db
```

## DBeaver Connection

```
Server Host: localhost
Port: 5432
Username: capstone_user  
Password: capstone_password
Database: capstone_db
```

## Next Steps

1. ✓ Migrations & seeding otomatis
2. ✓ Database models + schemas
3. Next: Create API endpoints (GET, POST, PUT, DELETE)
4. Next: Create auth system (login, JWT)
5. Next: Connect to vision detection service
