# Capstone A2 Group6 - APD Vision Monitoring

PROJECT UNTUK MONITORING VISION APD

## Setup dengan Docker

### Requirements
- Docker
- Docker Compose

### 🔐 Keamanan - PENTING!

**SEBELUM menjalankan project, setup environment variables:**

1. **Copy .env.docker-compose.example ke .env:**
```bash
cp .env.docker-compose.example .env
```

2. **Edit file .env dan ganti dengan values yang aman:**
```bash
# Database password - gunakan password yang kuat
DB_PASSWORD=your_secure_password_here

# JWT Secret - generate random string
# python -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your_random_jwt_secret_here

# Telegram credentials (opsional untuk development, wajib untuk production)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

3. **JANGAN PERNAH commit .env ke repository!**
   - File `.env` sudah di `.gitignore`
   - Gunakan `.env.example` atau `.env.docker-compose.example` untuk sharing template

### Cara Menjalankan

1. **Setup environment variables (lihat section Keamanan di atas)**

2. **Build dan run semua services:**
```bash
docker-compose up --build
```

3. **Jalankan di background mode:**
```bash
docker-compose up -d --build
```

4. **Lihat logs:**
```bash
docker-compose logs -f
```

5. **Stop services:**
```bash
docker-compose down
```

### Akses Services

- **Backend (FastAPI)**: http://localhost:8000
  - API Test: http://localhost:8000/test
  - Docs: http://localhost:8000/docs

- **Frontend (React + Vite)**: http://localhost:5173

### Services

#### Database (PostgreSQL)
- Type: PostgreSQL 16 Alpine
- Port: 5432
- Username: Dari `DB_USER` di .env
- Password: Dari `DB_PASSWORD` di .env
- Database: Dari `DB_NAME` di .env
- Data persistence: `capstone-db-data` volume

#### Backend
- Framework: FastAPI
- Port: 8000
- Database: SQLAlchemy + PostgreSQL
- Auto-reload diaktifkan untuk development
- Environment: DATABASE_URL, TELEGRAM credentials dari .env

#### Frontend
- Framework: React 19 + Vite
- Port: 5173
- Auto-reload diaktifkan untuk development

### Struktur Project

```
capstone-a2-group6-k3-apd-vision-monitoring/
├── backend/          # FastAPI application
├── frontend/         # React application
├── docker-compose.yml
├── .env.docker-compose.example  # Template untuk environment variables
├── .env              # JANGAN DI-COMMIT (sudah di .gitignore)
└── README.md
```

## Database Migrations & Seeding

Migrations dan seeding berjalan **OTOMATIS** saat container start:

1. **Entrypoint script** menunggu database ready
2. **Alembic migrations** membuat tables, indexes, ENUMs
3. **Seed script** populate initial data (users, cameras)
4. **FastAPI** aplikasi dimulai

### Initial Data (dari seed.py)

**Users:**
- Username: `admin` | Password: `admin123` | Role: Admin_IT
- Username: `pengawas` | Password: `pengawas123` | Role: Pengawas_K3
- Username: `manager` | Password: `manager123` | Role: Manager_HR

⚠️ **Production Note:** Ganti password ini setelah first login!

**Cameras:** 3 lokasi monitoring (predefined)

### Membuat Migration Baru

Jika menambah model baru di `app/models/`:
```bash
# Masuk ke container backend
docker exec -it capstone-backend bash

# Generate migration auto
alembic revision --autogenerate -m "Add new table"

# Jalankan migration
alembic upgrade head
```

Untuk detail lengkap lihat: [backend/MIGRATION_GUIDE.md](backend/MIGRATION_GUIDE.md)

### Troubleshooting

**Port sudah digunakan:**
```bash
# Ubah port di docker-compose.yml
ports:
  - "8001:8000"  # ubah 8001 ke port lain jika diperlukan
```

**Database connection failed:**
- Pastikan database service sudah running: `docker-compose ps`
- Cek logs: `docker-compose logs db`
- Tunggu database fully initialized (healthcheck harus passing)

**Akses PostgreSQL dari host:**
```bash
# Menggunakan psql
psql -h localhost -U capstone_user -d capstone_db

# Password: capstone_password
```

**Migration failed:**
```bash
# Lihat current migration status
docker exec -it capstone-backend alembic current

# Rollback 1 step
docker exec -it capstone-backend alembic downgrade -1
```

**Clear database (hapus semua data):**
```bash
docker-compose down -v
docker-compose up --build
```

**Rebuild services:**
```bash
docker-compose down
docker-compose up --build
```

