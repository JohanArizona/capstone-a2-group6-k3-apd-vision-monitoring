# Cameras Module - Documentation

## Overview

Modul ini menyediakan manajemen kamera untuk sistem monitoring APD Vision Monitoring.

## Features

### Camera Management
- ✅ List semua kamera untuk semua role
- ✅ Detail kamera spesifik untuk semua role
- ✅ Create kamera (Admin only)
- ✅ Update kamera (Admin only)
- ✅ Delete kamera (Admin only)
- ✅ Status management (Active/Inactive/Maintenance)

## Endpoints

### Camera Routes (`/api/cameras`)

#### 1. **GET /api/cameras**
Menampilkan daftar semua kamera

**Akses:** Semua role (Admin_IT, Pengawas_K3, Manager_HR)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response (200):**
```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "Lokasi Produksi A",
    "location": "Lantai 1 - Area Produksi",
    "status": "Active"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Lokasi Produksi B",
    "location": "Lantai 2 - Area Produksi",
    "status": "Active"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "name": "Lokasi Warehouse",
    "location": "Gudang - Area Penyimpanan",
    "status": "Inactive"
  }
]
```

---

#### 2. **GET /api/cameras/{id}**
Mengambil detail satu kamera spesifik

**Akses:** Semua role (Admin_IT, Pengawas_K3, Manager_HR)

**Headers:**
```
Authorization: Bearer {access_token}
```

**URL Parameter:**
```
id = 550e8400-e29b-41d4-a716-446655440000
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Lokasi Produksi A",
  "location": "Lantai 1 - Area Produksi",
  "rtsp_url": "rtsp://192.168.1.100:554/stream1",
  "status": "Active",
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-09T10:00:00"
}
```

**Error (404):**
```json
{
  "detail": "Camera not found"
}
```

---

#### 3. **POST /api/cameras**
Menambah data kamera baru

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**Request Body:**
```json
{
  "name": "Lokasi Warehouse B",
  "location": "Gudang 2 - Area Penyimpanan",
  "rtsp_url": "rtsp://192.168.1.110:554/stream1",
  "status": "Active"
}
```

**Response (201):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "name": "Lokasi Warehouse B",
  "location": "Gudang 2 - Area Penyimpanan",
  "rtsp_url": "rtsp://192.168.1.110:554/stream1",
  "status": "Active",
  "created_at": "2026-04-10T08:30:00",
  "updated_at": "2026-04-10T08:30:00"
}
```

**Error (400):**
```json
{
  "detail": "Camera dengan nama dan lokasi yang sama sudah ada"
}
```

---

#### 4. **PUT /api/cameras/{id}**
Mengubah data kamera

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**URL Parameter:**
```
id = 550e8400-e29b-41d4-a716-446655440000
```

**Request Body (semua field optional):**
```json
{
  "name": "Lokasi Produksi A - Updated",
  "location": "Lantai 1 - Area Produksi Baru",
  "rtsp_url": "rtsp://192.168.1.105:554/stream1",
  "status": "Maintenance"
}
```

**Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Lokasi Produksi A - Updated",
  "location": "Lantai 1 - Area Produksi Baru",
  "rtsp_url": "rtsp://192.168.1.105:554/stream1",
  "status": "Maintenance",
  "created_at": "2026-04-09T10:00:00",
  "updated_at": "2026-04-10T08:45:00"
}
```

---

#### 5. **DELETE /api/cameras/{id}**
Menghapus kamera

**Akses:** Hanya Admin_IT

**Headers:**
```
Authorization: Bearer {admin_token}
```

**URL Parameter:**
```
id = 550e8400-e29b-41d4-a716-446655440003
```

**Response (204):** No Content

**Error (404):**
```json
{
  "detail": "Camera not found"
}
```

---

## Data Models

### Camera Fields

| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `id` | UUID | Auto | Unique identifier (auto-generated) |
| `name` | String | ✅ | Nama kamera (max 100 chars) |
| `location` | String | ✅ | Lokasi pemasangan (max 100 chars) |
| `rtsp_url` | String | ✅ | URL stream RTSP (max 255 chars) |
| `status` | Enum | ✅ | Active / Inactive / Maintenance |
| `created_at` | DateTime | Auto | Timestamp pembuatan |
| `updated_at` | DateTime | Auto | Timestamp update terakhir |

### Camera Status

| Status | Deskripsi |
|--------|-----------|
| `Active` | Kamera aktif dan berfungsi normal |
| `Inactive` | Kamera non-aktif / tidak beroperasi |
| `Maintenance` | Kamera sedang dalam perawatan |

---

## Testing dengan cURL

### 1. Get All Cameras
```bash
curl -X GET http://localhost:8000/api/cameras \
  -H "Authorization: Bearer {token}"
```

### 2. Get Camera Detail
```bash
curl -X GET http://localhost:8000/api/cameras/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {token}"
```

### 3. Create Camera (Admin)
```bash
curl -X POST http://localhost:8000/api/cameras \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Lokasi Warehouse B",
    "location": "Gudang 2 - Area Penyimpanan",
    "rtsp_url": "rtsp://192.168.1.110:554/stream1",
    "status": "Active"
  }'
```

### 4. Update Camera (Admin)
```bash
curl -X PUT http://localhost:8000/api/cameras/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "Maintenance"
  }'
```

### 5. Delete Camera (Admin)
```bash
curl -X DELETE http://localhost:8000/api/cameras/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer {admin_token}"
```

---

## Testing via Swagger UI

1. Buka [http://localhost:8000/docs](http://localhost:8000/docs)
2. Login terlebih dahulu dengan POST `/api/auth/login`
3. Copy token, klik "Authorize" dan paste: `Bearer {token}`
4. Test endpoints di bawah "/Cameras" section

---

## Default Cameras (dari seed.py)

Setelah migration, ada 3 kamera yang sudah di-seed:

| ID | Nama | Lokasi | Status |
|----|----|--------|--------|
| (UUID) | Lokasi Produksi A | Lantai 1 - Area Produksi | Active |
| (UUID) | Lokasi Produksi B | Lantai 2 - Area Produksi | Active |
| (UUID) | Lokasi Warehouse | Gudang - Area Penyimpanan | Active |

---

## Business Rules

1. **Duplicate Camera Detection**
   - Tidak boleh ada 2 kamera dengan nama dan lokasi yang sama
   - Jika mencoba create/update dengan kombinasi yang sudah ada → Error 400

2. **Access Control**
   - GET endpoints: Semua role (memerlukan login)
   - POST/PUT/DELETE: Hanya Admin_IT
   - Non-admin role tidak bisa modify kamera

3. **Status Management**
   - Status hanya bisa: "Active", "Inactive", "Maintenance"
   - Nilai lain akan reject dengan error validasi

4. **Delete Policy**
   - Delete adalah permanent (hard delete)
   - Tidak ada soft delete untuk camera
   - Admin harus confirm sebelum delete

---

## Error Handling

### Common Errors

**400 Bad Request - Duplicate Camera:**
```json
{
  "detail": "Camera dengan nama dan lokasi yang sama sudah ada"
}
```

**400 Bad Request - Invalid ID Format:**
```json
{
  "detail": "Invalid camera ID format"
}
```

**404 Not Found:**
```json
{
  "detail": "Camera not found"
}
```

**403 Forbidden - Non-Admin:**
```json
{
  "detail": "Only admins can access this resource"
}
```

**401 Unauthorized - Invalid Token:**
```json
{
  "detail": "Invalid or expired token"
}
```

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── cameras.py          # Camera routes (5 endpoints)
│   ├── models/
│   │   └── camera.py               # Camera model & CameraStatus enum
│   └── schemas/
│       └── cameras.py              # Camera request/response schemas
├── main.py                         # Updated with cameras router
└── ...
```

---

## Next Steps

Modul berikutnya:
- [ ] Violations Management (CREATE, READ, UPDATE, DELETE, FILTER)
- [ ] Detection Stats & Analytics
- [ ] Notifications Management
- [ ] File Upload (Snapshots)
- [ ] Advanced Filtering & Pagination
