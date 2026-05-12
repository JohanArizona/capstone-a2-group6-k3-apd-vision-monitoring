# Auth & Users Module - Documentation

## Overview

Modul ini menyediakan authentication, authorization, dan user management untuk aplikasi APD Vision Monitoring.

## Features

### Authentication
- ✅ JWT Token-based authentication
- ✅ Password hashing dengan bcrypt
- ✅ Secure login/logout
- ✅ Token expiration (30 minutes default)

### Authorization
- ✅ Role-based access control (Admin_IT, Pengawas_K3, Manager_HR)
- ✅ Admin-only endpoints
- ✅ User self-profile management
- ✅ Admin user management (CRUD)

## Endpoints

### Authentication Routes (`/api/auth`)

#### 1. **POST /api/auth/login**
Login dan dapatkan JWT Token

**Request Body:**
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "full_name": "Admin System",
    "email": "admin@apd-vision.com",
    "role": "Admin_IT"
  }
}
```

**Error (401):**
```json
{
  "detail": "Username atau password salah"
}
```

---

#### 2. **GET /api/auth/me**
Ambil profil user yang sedang login

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "full_name": "Admin System",
  "email": "admin@apd-vision.com",
  "telegram_id": null,
  "role": "Admin_IT",
  "is_active": true,
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-09T10:00:00"
}
```

---

### User Routes (`/api/users`)

#### 3. **PUT /api/users/me**
Update profil sendiri (All Role)

**Akses:** Semua role (Admin_IT, Pengawas_K3, Manager_HR)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "full_name": "Nama Baru",
  "email": "email_baru@apd-vision.com",
  "password": "password_baru123",
  "telegram_id": "123456789"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "admin",
  "full_name": "Nama Baru",
  "email": "email_baru@apd-vision.com",
  "telegram_id": "123456789",
  "role": "Admin_IT",
  "is_active": true,
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-09T10:05:00"
}
```

---

#### 4. **GET /api/users**
Lihat daftar semua user (Admin Only)

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "admin",
    "full_name": "Admin System",
    "email": "admin@apd-vision.com",
    "role": "Admin_IT",
    "is_active": true
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "username": "pengawas",
    "full_name": "Pengawas K3",
    "email": "pengawas@apd-vision.com",
    "role": "Pengawas_K3",
    "is_active": true
  }
]
```

---

#### 5. **GET /api/users/{id}**
Lihat detail satu user spesifik (Admin Only)

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "username": "pengawas",
  "full_name": "Pengawas K3",
  "email": "pengawas@apd-vision.com",
  "telegram_id": null,
  "role": "Pengawas_K3",
  "is_active": true,
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-09T10:00:00"
}
```

---

#### 6. **POST /api/users**
Buat user baru (Admin Only)

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**Request Body:**
```json
{
  "username": "user_baru",
  "password": "password123",
  "full_name": "User Baru",
  "email": "user_baru@apd-vision.com",
  "telegram_id": "987654321",
  "role": "Pengawas_K3"
}
```

**Response (200):**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "username": "user_baru",
  "full_name": "User Baru",
  "email": "user_baru@apd-vision.com",
  "telegram_id": "987654321",
  "role": "Pengawas_K3",
  "is_active": true,
  "created_at": "2026-04-09T10:10:00",
  "updated_at": "2026-04-09T10:10:00"
}
```

---

#### 7. **PUT /api/users/{id}**
Ubah data user (Admin Only)

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**Request Body:**
```json
{
  "full_name": "Nama Updated",
  "email": "email_updated@apd-vision.com",
  "password": "password_baru123",
  "role": "Manager_HR",
  "is_active": true,
  "telegram_id": "111111111"
}
```

**Response (200):**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "username": "pengawas",
  "full_name": "Nama Updated",
  "email": "email_updated@apd-vision.com",
  "telegram_id": "111111111",
  "role": "Manager_HR",
  "is_active": true,
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-09T10:15:00"
}
```

---

#### 8. **DELETE /api/users/{id}**
Hapus/deactivate user (Admin Only, Soft Delete)

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**Response (204):** No Content

---

## Architecture

### File Structure
```
backend/
├── app/
│   ├── core/
│   │   ├── security.py          # Password hashing & JWT utilities
│   │   ├── dependencies.py      # FastAPI dependencies (auth, admin)
│   │   └── ...
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Auth routes (login, me)
│   │       ├── users.py         # Users routes (CRUD)
│   │       └── ...
│   ├── schemas/
│   │   ├── auth.py              # Auth schemas (LoginRequest, etc)
│   │   ├── users_admin.py       # Users admin schemas
│   │   └── ...
│   └── models/
│       └── user.py              # User model
├── main.py                      # FastAPI app
└── requirements.txt
```

### Security Features

1. **Password Hashing**
   - Using bcrypt algorithm
   - Function: `get_password_hash()`, `verify_password()`

2. **JWT Token**
   - Algorithm: HS256
   - Expiration: 30 minutes (configurable)
   - Payload: `{"sub": user_id, "exp": expiration_time}`

3. **Database**
   - User passwords hashed sebelum disimpan
   - Email unique constraint
   - Username unique constraint

4. **Validation**
   - Email validation (RFC 5322)
   - Username/email duplication check
   - Role validation
   - Active user check

## Testing dengan Endpoints

### 1. Login
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

### 2. Get Current User
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer {token}"
```

### 3. List All Users (Admin)
```bash
curl -X GET http://localhost:8000/api/users \
  -H "Authorization: Bearer {admin_token}"
```

### 4. Create User (Admin)
```bash
curl -X POST http://localhost:8000/api/users \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "password": "pass123",
    "full_name": "New User",
    "email": "newuser@example.com",
    "role": "Pengawas_K3"
  }'
```

## Environment Variables

```env
# JWT Configuration
SECRET_KEY=your-secret-key-for-jwt

# Atau di alembic.ini atau .env:
DATABASE_URL=postgresql://...
```

## Default Users (dari seed.py)

Setelah migration, ada 3 admin users:

| Username | Password | Role | Email |
|----------|----------|------|-------|
| admin | admin123 | Admin_IT | admin@apd-vision.com |
| pengawas | pengawas123 | Pengawas_K3 | pengawas@apd-vision.com |
| manager | manager123 | Manager_HR | manager@apd-vision.com |

## Error Handling

### Common Errors

**401 Unauthorized:**
```json
{
  "detail": "Username atau password salah"
}
```

**403 Forbidden:**
```json
{
  "detail": "Only admins can access this resource"
}
```

**404 Not Found:**
```json
{
  "detail": "User not found"
}
```

**400 Bad Request:**
```json
{
  "detail": "Email sudah digunakan"
}
```

## Next Steps

Modul berikutnya:
- [ ] Camera Management (GET, POST, PUT, DELETE)
- [ ] Violations Management
- [ ] Statistics & Analytics
- [ ] Notifications
- [ ] File Upload (Snapshots)
