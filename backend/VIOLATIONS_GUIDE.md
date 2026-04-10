# Violations Module - Documentation

## Overview

Modul ini menangani manajemen pelanggaran APD dengan integrasi telegram notifikasi, file upload, dan export functionality.

## Features

### Violation Tracking
- ✅ Menerima data pelanggaran + snapshot dari Edge AI
- ✅ Automatic Telegram notification saat ada pelanggaran
- ✅ Status management (Unverified, Verified, False_Positive)
- ✅ Snapshot storage dan retrieval
- ✅ Query dengan filter & pagination

### Dashboard Analytics
- ✅ List violations dengan filter by camera, status, date range
- ✅ Detail violation dengan snapshot untuk pop-up
- ✅ Verify/reject violations dengan notes
- ✅ Export ke Excel (.xlsx) dengan formatting

### Telegram Integration
- ✅ Real-time alert saat ada pelanggaran
- ✅ Notification saat verifikasi
- ✅ Display APD yang hilang dengan emoji
- ✅ Confidence score display

## Prerequisites (Setup Telegram Bot)

### 1. Create Telegram Bot
```
1. Open Telegram, search @BotFather
2. Send /start
3. Send /newbot
4. Follow instructions, give bot a name
5. Copy BOT_TOKEN (contoh: 123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefg)
```

### 2. Get Chat ID
```
1. Add bot ke group chat tempat ingin receive notifications
2. atau buat private chat dengan bot (/start)
3. Send message ke bot
4. Get Chat ID via: https://api.telegram.org/botYOUR_TOKEN/getUpdates
5. Look untuk "chat":{"id": YOUR_CHAT_ID}
```

### 3. Configure Environment
```env  
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZabcdefg
TELEGRAM_CHAT_ID=-987654321
```

---

## Endpoints

### Violations Routes (`/api/violations`)

#### 1. **POST /api/violations**
Menerima data pelanggaran dan file snapshot dari Edge AI

**Akses:** Edge AI / System Integration (no auth)

**Content-Type:** `multipart/form-data`

**Form Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `camera_id` | String (UUID) | ✅ | UUID kamera |
| `missing_apd` | String (JSON) | ✅ | JSON missing APD |
| `confidence_score` | Float | ✅ | Score 0.0-1.0 |
| `snapshot` | File (image) | ✅ | PNG/JPG snapshot |

**Example with cURL:**
```bash
curl -X POST http://localhost:8000/api/violations \
  -F "camera_id=550e8400-e29b-41d4-a716-446655440000" \
  -F 'missing_apd={"helmet":true,"vest":false}' \
  -F "confidence_score=0.92" \
  -F "snapshot=@/path/to/image.jpg"
```

**Response (201 Created):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440200",
  "camera_id": "550e8400-e29b-41d4-a716-446655440000",
  "missing_apd": {
    "helmet": true,
    "vest": false
  },
  "confidence_score": 0.92,
  "snapshot_path": "/uploads/violations/violation_20260410_143000_image.jpg",
  "timestamp": "2026-04-10T14:30:00",
  "status": "Unverified",
  "created_at": "2026-04-10T14:30:00"
}
```

**Automatic Actions:**
- ✅ File snapshot di-save ke directory
- ✅ Telegram notification dikirim otomatis

**Error (400) - Invalid missing_apd:**
```json
{
  "detail": "Invalid missing_apd JSON: Expecting value: line 1 column 1 (char 0)"
}
```

**Error (400) - Invalid file type:**
```json
{
  "detail": "File type not allowed. Allowed: .jpg, .jpeg, .png, .gif, .bmp"
}
```

---

#### 2. **GET /api/violations**
Mengambil riwayat pelanggaran dengan pagination & filter

**Akses:** Semua role

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters (all optional):**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `camera_id` | UUID | Filter by camera | (all) |
| `status_filter` | String | Filter: Unverified, Verified, False_Positive | (all) |
| `start_date` | ISO DateTime | Start range | (no limit) |
| `end_date` | ISO DateTime | End range | (no limit) |
| `limit` | Integer | Max records (1-500) | 50 |
| `offset` | Integer | Pagination offset | 0 |

**Example Request:**
```
GET /api/violations?camera_id=550e8400-e29b-41d4-a716-446655440000&status_filter=Unverified&limit=20&offset=0
```

**Response (200):**
```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440200",
    "camera_id": "550e8400-e29b-41d4-a716-446655440000",
    "missing_apd": {
      "helmet": true,
      "vest": false,
      "gloves": false
    },
    "confidence_score": 0.92,
    "snapshot_path": "/uploads/violations/violation_20260410_143000_image.jpg",
    "timestamp": "2026-04-10T14:30:00",
    "status": "Unverified"
  },
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440201",
    "camera_id": "550e8400-e29b-41d4-a716-446655440000",
    "missing_apd": {
      "helmet": false,
      "vest": true,
      "gloves": true
    },
    "confidence_score": 0.85,
    "snapshot_path": "/uploads/violations/violation_20260410_141500_image.jpg",
    "timestamp": "2026-04-10T14:15:00",
    "status": "Verified"
  }
]
```

---

#### 3. **GET /api/violations/{id}**
Mengambil detail satu pelanggaran spesifik

**Akses:** Semua role

**Headers:**
```
Authorization: Bearer {access_token}
```

**URL Parameter:**
```
id = 990e8400-e29b-41d4-a716-446655440200 (UUID)
```

**Response (200):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440200",
  "camera_id": "550e8400-e29b-41d4-a716-446655440000",
  "missing_apd": {
    "helmet": true,
    "vest": false,
    "gloves": false,
    "shoes": false
  },
  "confidence_score": 0.92,
  "snapshot_path": "/uploads/violations/violation_20260410_143000_image.jpg",
  "timestamp": "2026-04-10T14:30:00",
  "status": "Unverified",
  "created_at": "2026-04-10T14:30:00"
}
```

**Snapshot Path Usage (Frontend):**
```javascript
// Di React component
const snapshotUrl = `http://localhost:8000${violation.snapshot_path}`;
// atau mounting di static folder dengan nginx
```

---

#### 4. **PUT /api/violations/{id}/status**
Mengubah status pelanggaran menjadi Verified atau False Positive

**Akses:** Semua role

**Headers:**
```
Authorization: Bearer {access_token}
```

**URL Parameter:**
```
id = 990e8400-e29b-41d4-a716-446655440200
```

**Request Body:**
```json
{
  "status": "Verified",
  "notes": "Confirmed - worker tidak memakai safety helmet"
}
```

atau

```json
{
  "status": "False_Positive",
  "notes": "False alarm - worker memakai helmet, system error"
}
```

**Response (200):**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440200",
  "camera_id": "550e8400-e29b-41d4-a716-446655440000",
  "missing_apd": {
    "helmet": true,
    "vest": false
  },
  "confidence_score": 0.92,
  "snapshot_path": "/uploads/violations/violation_20260410_143000_image.jpg",
  "timestamp": "2026-04-10T14:30:00",
  "status": "Verified",
  "created_at": "2026-04-10T14:30:00"
}
```

**Automatic Actions:**
- ✅ Status di-update ke database
- ✅ Telegram notification dikirim dengan nama verifier dan status

---

#### 5. **GET /api/violations/export/xlsx**
Mengunduh file .xlsx berisi riwayat pelanggaran

**Akses:** Semua role

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters (all optional):**
| Parameter | Type | Description |
|-----------|------|-------------|
| `camera_id` | UUID | Filter by camera |
| `status_filter` | String | Filter by status |
| `start_date` | ISO DateTime | Start range |
| `end_date` | ISO DateTime | End range |

**Example Request:**
```
GET /api/violations/export/xlsx?start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59
```

**Response (200):**
- Binary `.xlsx` file auto-downloaded sebagai attachment
- Filename: `violations_export_YYYYMMDD_HHMMSS.xlsx`
- Columns: ID, Camera ID, Timestamp, Missing APD, Confidence Score, Status, Snapshot Path, Notes
- Header formatting: Blue background, white text, centered
- Auto-sized columns untuk readability
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`

**Error (404) - No data:**
```json
{
  "detail": "No violations found for export"
}
```

---

## Data Models

### Violation Table

| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `id` | UUID | Auto | Unique identifier |
| `camera_id` | UUID | ✅ | Foreign key to Camera |
| `missing_apd` | JSON | ✅ | {"helmet": bool, "vest": bool, ...} |
| `confidence_score` | Decimal(5,4) | ✅ | 0.0 - 1.0 |
| `snapshot_path` | String | ✅ | Path ke file snapshot |
| `timestamp` | DateTime | ✅ | Waktu pelanggaran terdeteksi |
| `status` | Enum | ✅ | Unverified / Verified / False_Positive |
| `notes` | String(500) | ❌ | Catatan verifikasi (opsional) |
| `created_at` | DateTime | Auto | Record creation timestamp |

### Status Values

| Status | Meaning | Color |
|--------|---------|-------|
| `Unverified` | Belum diverifikasi | 🟡 Yellow |
| `Verified` | Pelanggaran terkonfirmasi | 🔴 Red |
| `False_Positive` | Bukan pelanggaran | ✅ Green |

---

## Telegram Notifications

### Format Notifikasi Pelanggaran
```
🚨 **PELANGGARAN APD TERDETEKSI**

📹 Kamera: Lokasi Produksi A
🕐 Waktu: 2026-04-10T14:30:00
⚠️ APD Hilang:
❌ HELMET
❌ VEST

📊 Confidence Score: 92.0%

🔗 Lihat detail di dashboard untuk verifikasi.
```

### Format Notifikasi Verifikasi
```
✅ **PELANGGARAN TERVERIFIKASI**

📹 Kamera: Lokasi Produksi A
👤 Diverifikasi oleh: admin
📝 Catatan: Confirmed - worker tidak memakai safety helmet
```

atau

```
⛔ **BUKAN PELANGGARAN**

📹 Kamera: Lokasi Produksi A
👤 Diverifikasi oleh: pengawas
📝 Catatan: False alarm - worker memakai helmet
```

---

## File Upload Configuration

### Directory Structure
```
/app/uploads/
├── violations/
│   ├── violation_20260410_143000_image.jpg
│   ├── violation_20260410_141500_image.jpg
│   └── ...
```

### Allowed File Types
- `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`

### Upload Size Limit
- Default: 50 MB (configurable via MAX_UPLOAD_SIZE_MB)

### File Naming
- Format: `violation_YYYYMMDD_HHMMSS_originalname.ext`
- Prevents naming conflicts
- Preserved original filename for reference

---

## Frontend Integration Example

### React Component - Violations List
```jsx
import { useState, useEffect } from 'react';

function ViolationsList() {
  const [violations, setViolations] = useState([]);
  const [statusFilter, setStatusFilter] = useState('Unverified');
  const [loading, setLoading] = useState(false);
  
  const fetchViolations = async () => {
    setLoading(true);
    const response = await fetch(
      `/api/violations?status_filter=${statusFilter}&limit=50`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      }
    );
    const data = await response.json();
    setViolations(data);
    setLoading(false);
  };
  
  useEffect(() => {
    fetchViolations();
  }, [statusFilter]);
  
  return (
    <div>
      <select onChange={(e) => setStatusFilter(e.target.value)}>
        <option value="Unverified">Unverified</option>
        <option value="Verified">Verified</option>
        <option value="False_Positive">False Positive</option>
      </select>
      
      {violations.map(v => (
        <div key={v.id} className="violation-card">
          <img src={`http://localhost:8000${v.snapshot_path}`} />
          <p>Confidence: {(v.confidence_score * 100).toFixed(1)}%</p>
          <div>Missing: {Object.keys(v.missing_apd).filter(k => v.missing_apd[k]).join(', ')}</div>
          <button onClick={() => verifyViolation(v.id, 'Verified')}>Verify</button>
          <button onClick={() => verifyViolation(v.id, 'False_Positive')}>False Positive</button>
        </div>
      ))}
    </div>
  );
}
```

### React Component - Export
```jsx
const exportViolations = async (startDate, endDate) => {
  const response = await fetch(
    `/api/violations/export/xlsx?start_date=${startDate}&end_date=${endDate}`,
    {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      }
    }
  );
  
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'violations_export.xlsx';
  link.click();
};
```

---

## Performance & Best Practices

1. **Snapshot Storage**
   - Simpan di `/app/uploads/violations/` (atau cloud storage)
   - Implement cleanup/archival untuk old files
   - Consider CDN untuk image delivery

2. **Database Indexes**
   - `violations.timestamp` sudah di-index
   - Add index on `camera_id` + `status` untuk filter query

3. **Pagination**
   - Default limit 50, max 500
   - Always use offset/limit untuk large result sets

4. **Telegram Rate Limiting**
   - API Telegram: 30 requests/second
   - Batch notifications jika banyak violations

5. **File Upload**
   - Validate file type + size on both frontend & backend
   - Use async file upload dengan progress tracking
   - Store full path untuk retrieval

---

## Troubleshooting

### Telegram Tidak Ada Notifikasi
1. Check BOT_TOKEN and CHAT_ID di .env
2. Verify bot di-invite ke group chat
3. Check Telegram API response: `https://api.telegram.org/botTOKEN/getMe`

### File Upload Error
1. Check directory permissions: `/app/uploads/violations/`
2. Check file size < 50MB
3. Validate file extension

### Export Excel Tidak Bisa Dibuka
1. Ensure openpyxl ver 3.1.2
2. Check corrupted data di database
3. Try dengan smaller date range

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── violations.py           # 5 violation endpoints
│   ├── core/
│   │   └── telegram_utils.py           # Telegram integration
│   ├── models/
│   │   └── violation.py                # Violation model
│   └── schemas/
│       └── violations.py               # Violation schemas
├── uploads/
│   └── violations/                     # Snapshot storage
├── main.py                            # Updated with violations router
├── requirements.txt                   # Updated with openpyxl, requests
└── .env.example                       # Updated with Telegram config
```

---

## Next Steps

- [ ] Implement notification filtering/preferences
- [ ] Add violation statistics/dashboard
- [ ] Implement snapshot cleanup/retention policy
- [ ] Add advanced filtering (date ranges, APD type, etc.)
- [ ] Integrate with object detection model
