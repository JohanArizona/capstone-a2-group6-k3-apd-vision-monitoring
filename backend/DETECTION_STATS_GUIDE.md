# Detection Statistics Module - Documentation

## Overview

Modul ini menyediakan sistem pengumpulan dan visualisasi statistik deteksi pekerja untuk dashboard monitoring real-time.

## Features

### Detection Statistics Collection
- ✅ Menerima data agregasi dari Edge AI
- ✅ Menyimpan statistik per camera dengan timestamp
- ✅ Track jumlah pekerja, compliance, dan violations
- ✅ Query dengan date range untuk analysis

### Dashboard Analytics
- ✅ Get statistics dengan filter by camera & date range
- ✅ Pagination support untuk large datasets
- ✅ Summary statistics (average, peak, compliance rate)
- ✅ Data siap untuk chart visualization

## Endpoints

### Detection Statistics Routes (`/api/detections`)

#### 1. **POST /api/detections/stats**
Menerima data agregasi jumlah pekerja dari Edge AI

**Akses:** Edge AI / System Integration (no auth required)

**Request Body:**
```json
{
  "camera_id": "3fcdb055-c636-4130-b8ce-78365e679d05",
  "total_workers": 15,
  "compliant_workers": 12,
  "violating_workers": 3,
  "timestamp": "2026-04-10T14:30:00Z"
}
```

**Field Descriptions:**
- `camera_id`: UUID dari kamera (required)
- `total_workers`: Total pekerja terdeteksi (required, ≥0)
- `compliant_workers`: Pekerja yang sesuai APD (required, ≥0)
- `violating_workers`: Pekerja yang tidak sesuai APD (required, ≥0)
- `timestamp`: Waktu capture data (optional, auto-generate jika None)

**Validation Rules:**
```
compliant_workers + violating_workers ≤ total_workers
```

**Response (201 Created):**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440100",
  "camera_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_workers": 15,
  "compliant_workers": 12,
  "violating_workers": 3,
  "timestamp": "2026-04-10T14:30:00"
}
```

**Error (400) - Invalid validation:**
```json
{
  "detail": "compliant_workers + violating_workers tidak boleh lebih besar dari total_workers"
}
```

**Error (404) - Camera not found:**
```json
{
  "detail": "Camera not found"
}
```

---

#### 2. **GET /api/detections/stats**
Mengambil data statistik deteksi untuk Line/Bar Chart

**Akses:** Semua role (Admin_IT, Pengawas_K3, Manager_HR)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters (optional):**
| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `camera_id` | UUID | Filter by specific camera | (all cameras) |
| `start_date` | ISO DateTime | Start of date range | (no limit) |
| `end_date` | ISO DateTime | End of date range | (no limit) |
| `limit` | Integer | Max records (1-5000) | 500 |
| `offset` | Integer | Pagination offset | 0 |

**Example Request:**
```
GET /api/detections/stats?camera_id=550e8400-e29b-41d4-a716-446655440000&start_date=2026-04-10T00:00:00&end_date=2026-04-10T23:59:59&limit=100&offset=0
```

**Response (200):**
```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440100",
    "camera_id": "3fcdb055-c636-4130-b8ce-78365e679d05",
    "timestamp": "2026-04-10T14:30:00",
    "total_workers": 15,
    "compliant_workers": 12,
    "violating_workers": 3
  },
]
```

---

#### 3. **GET /api/detections/stats/summary**
Mengambil summary statistik untuk analytics dashboard

**Akses:** Semua role (Admin_IT, Pengawas_K3, Manager_HR)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters (optional):**
| Parameter | Type | Description |
|-----------|------|-------------|
| `camera_id` | UUID | Filter by specific camera |
| `start_date` | ISO DateTime | Start of analysis period |
| `end_date` | ISO DateTime | End of analysis period |

**Example Request:**
```
GET /api/detections/stats/summary?camera_id=550e8400-e29b-41d4-a716-446655440000&start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59
```

**Response (200):**
```json
{
  "total_records": 2880,
  "average_workers": 16.45,
  "average_compliance_rate": 89.5,
  "peak_workers": 42,
  "total_violations": 3240
}
```

**Error (404) - No data for period:**
```json
{
  "detail": "No statistics data found for the given period"
}
```

---

## Data Models

### DetectionStats Table

| Field | Type | Required | Deskripsi |
|-------|------|----------|-----------|
| `id` | UUID | Auto | Unique identifier |
| `camera_id` | UUID | ✅ | Foreign key ke Camera |
| `timestamp` | DateTime | ✅ | Waktu data capture |
| `total_workers` | Integer | ✅ | Total pekerja terdeteksi |
| `compliant_workers` | Integer | ✅ | Pekerja sesuai APD |
| `violating_workers` | Integer | ✅ | Pekerja tidak sesuai APD |

### DetectionStatsSummary Response

| Field | Type | Deskripsi |
|-------|------|-----------|
| `total_records` | Integer | Jumlah records dalam periode |
| `average_workers` | Float | Rata-rata jumlah pekerja |
| `average_compliance_rate` | Float | Rata-rata % compliance |
| `peak_workers` | Integer | Puncak tertinggi jumlah pekerja |
| `total_violations` | Integer | Total violations dalam periode |

---

## Testing dengan cURL

### 1. Send Stats from Edge AI
```bash
curl -X POST http://localhost:8000/api/detections/stats \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "550e8400-e29b-41d4-a716-446655440000",
    "total_workers": 15,
    "compliant_workers": 12,
    "violating_workers": 3
  }'
```

### 2. Get Stats for Today
```bash
curl -X GET "http://localhost:8000/api/detections/stats?start_date=2026-04-10T00:00:00&end_date=2026-04-10T23:59:59&limit=100" \
  -H "Authorization: Bearer {token}"
```

### 3. Get Stats by Camera
```bash
curl -X GET "http://localhost:8000/api/detections/stats?camera_id=550e8400-e29b-41d4-a716-446655440000&limit=500" \
  -H "Authorization: Bearer {token}"
```

### 4. Get Summary Statistics
```bash
curl -X GET "http://localhost:8000/api/detections/stats/summary?camera_id=550e8400-e29b-41d4-a716-446655440000&start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59" \
  -H "Authorization: Bearer {token}"
```

---

## Testing via Swagger UI

1. Buka [http://localhost:8000/docs](http://localhost:8000/docs)
2. Login dengan POST `/api/auth/login`
3. Copy token dan klik "Authorize"
4. Test endpoints di section "Detection Statistics"

---

## Use Cases

### Edge AI Integration
Edge device mengirim detection stats setiap 5 detik:
```python
async def send_stats_to_backend():
    stats = {
        "camera_id": "550e8400-e29b-41d4-a716-446655440000",
        "total_workers": count_workers(),
        "compliant_workers": count_compliant(),
        "violating_workers": count_violations()
    }
    response = requests.post("http://backend:8000/api/detections/stats", json=stats)
```

### Dashboard - Real-time Chart
```javascript
// Fetch last hour stats
const response = await fetch('/api/detections/stats?start_date=2026-04-10T13:00:00&end_date=2026-04-10T14:00:00');
const data = await response.json();
// Plot on line chart
```

### Analytics - Monthly Report
```javascript
// Get summary for April
const response = await fetch('/api/detections/stats/summary?start_date=2026-04-01T00:00:00&end_date=2026-04-30T23:59:59');
const summary = await response.json();
// Display KPIs: average_compliance_rate, peak_workers, total_violations
```

### Multi-Camera Comparison
```javascript
// Get stats for all cameras in period
const response = await fetch('/api/detections/stats?start_date=2026-04-10T00:00:00&limit=5000');
const stats = await response.json();
// Group by camera_id and analyze per camera
```

---

## Business Rules

1. **Data Validation**
   - `compliant_workers + violating_workers` tidak boleh > `total_workers`
   - All fields harus ≥ 0

2. **Camera Validation**
   - Camera ID harus valid (exist di database)
   - Jika camera tidak ada → Error 404

3. **Access Control**
   - POST stats: No auth (dari trusted edge device)
   - GET stats: Auth required (dashboard users)
   - All roles bisa akses GET

4. **Timestamp Handling**
   - Jika POST tanpa timestamp: gunakan server time
   - Untuk query use ISO format with timezone

5. **Pagination**
   - Default limit: 500 records
   - Max limit: 5000 records
   - Offset mulai dari 0

---

## Error Handling

### HTTP Status Codes

| Code | Scenario |
|------|----------|
| 201 | POST stats successful |
| 200 | GET stats / summary successful |
| 400 | Validation error (workers constraint) |
| 404 | Camera not found / No data for period |
| 401 | Unauthorized (GET endpoints) |
| 422 | Invalid query parameter format |

---

## File Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── detection_stats.py     # Detection stats routes (2 endpoints)
│   ├── models/
│   │   └── detection_stats.py         # DetectionStats model & table
│   └── schemas/
│       └── detection_stats.py         # Request/response schemas
├── main.py                           # Updated with detection_stats router
└── ...
```

---

## Performance Notes

1. **Indexing**
   - `timestamp` column sudah di-index untuk fast range queries
   - Consider adding index on `camera_id` + `timestamp` untuk heavy usage

2. **Pagination**
   - Selalu gunakan limit/offset untuk large datasets
   - Default 500 records cukup untuk most use cases

3. **Date Range Filtering**
   - Lebih spesifik date range = lebih cepat query
   - Avoid querying 1 year data sekaligus

4. **Database Growth**
   - Dengan 5-second intervals: ~17,280 records/camera/day
   - Implement data retention policy (archive old data)

---

## Next Steps

Modul berikutnya:
- [ ] Violations Management (dengan detailed tracking)
- [ ] Notifications & Alerts
- [ ] File Upload (Snapshots)
- [ ] Advanced Reporting & Export
