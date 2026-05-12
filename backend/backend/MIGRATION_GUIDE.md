# Migration Guide - APD Vision Monitoring

## Database Migrations and Seeding

Project ini menggunakan **Alembic** untuk database migrations (seperti Laravel migrations) dan **seed.py** untuk initial data seeding.

## Architecture

```
Database Setup Flow:
1. Entrypoint Script menunggu database ready
2. Run Alembic migrations (create tables, indexes, enums)
3. Run seed.py (populate initial data)
4. Start FastAPI application
```

## Alembic Structure

```
alembic/
├── versions/          # Migration files
│   ├── 001_initial.py # Initial schema (users, cameras, violations, etc)
│   └── ...
├── env.py            # Alembic environment configuration
└── script.py.mako    # Migration template
```

## Seed Struktur

Seed script (`seed.py`) automatically membuat:
- **Admin users** (admin, pengawas, manager)
- **Initial cameras** (3 lokasi)

## Cara Menggunakan

### 1. Development Mode

**Run docker-compose** - semuanya otomatis:
```bash
docker-compose up --build
```

Entrypoint script akan:
- ✓ Tunggu database ready
- ✓ Run migrations (`alembic upgrade head`)
- ✓ Run seeding (`python seed.py`)
- ✓ Start FastAPI

### 2. Membuat Migration Baru

Jika menambah model baru:

```bash
# Generate migration script
alembic revision --autogenerate -m "Add new table"

# Ini akan membuat file baru di alembic/versions/
# EDIT file tersebut jika diperlukan

# Jalankan migration
alembic upgrade head
```

### 3. Rollback Migration

```bash
# Rollback 1 step
alembic downgrade -1

# Rollback ke revision tertentu
alembic downgrade 001_initial
```

### 4. Seed Data Saja

```bash
# Masuk ke container
docker exec -it capstone-backend bash

# Jalankan seeding
python seed.py
```

## Models dan Schema

Semua models di-define di `app/models/`:
- `user.py`        - Users table
- `camera.py`      - Cameras table
- `violation.py`   - Violations table
- `detection_stats.py` - Detection statistics
- `notification.py` - Notifications

Models menggunakan SQLAlchemy ORM dan automatically dideteksi oleh Alembic.

## Environment Variables

Database configuration di `.env`:
```
DATABASE_URL=postgresql://capstone_user:capstone_password@db:5432/capstone_db
```

## Initial Data

### Users (dari seed.py)
| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin_IT |
| pengawas | pengawas123 | Pengawas_K3 |
| manager | manager123 | Manager_HR |

### Cameras
- Lokasi Produksi A (Lantai 1)
- Lokasi Produksi B (Lantai 2)
- Lokasi Warehouse

## Troubleshooting

**Migration failed - "relation already exists"**
```bash
docker-compose down -v  # Clear volumes
docker-compose up --build
```

**Need to modify migration**
```bash
# Edit file di alembic/versions/
# Kemudian re-run container
docker-compose restart capstone-backend
```

**Check migration status**
```bash
docker exec -it capstone-backend bash
alembic current       # Current version
alembic history       # Semua versions
```

## Best Practices

1. **Selalu generate migration** setelah menambah/mengubah models
2. **Test migration** sebelum push ke production
3. **Version control** semua migration files
4. **Seed script** untuk dev/testing data
5. **Production data** tidak perlu di-seed (buat secara manual)
