# APD Vision Monitoring System

Sistem monitoring kepatuhan Alat Pelindung Diri (APD) berbasis AI menggunakan YOLOv8, FastAPI, React, dan Edge Device streaming.

---

# Fitur Utama

- Login autentikasi JWT
- Monitoring dashboard real-time
- Live camera feed
- Deteksi APD menggunakan YOLOv8
- Event processing pelanggaran APD
- Notifikasi pelanggaran real-time
- Analytics dan riwayat pelanggaran
- Export laporan Excel
- Edge relay MJPEG stream
- Dukungan webcam lokal dan CCTV RTSP

---

# Arsitektur Sistem

## Backend
- FastAPI
- PostgreSQL
- JWT Authentication
- REST API

## Frontend
- React + Vite
- Dashboard monitoring
- Analytics & reporting

## Edge Client
- YOLOv8 inference
- Webcam/CCTV reader
- Violation uploader
- MJPEG relay stream server

---

# Struktur Sistem

```text
Frontend Dashboard
        │
        ▼
MJPEG Relay Stream
(http://localhost:8765/stream.mjpg)
        ▲
        │
Edge Client (YOLO Detection)
        │
        ▼
Backend API (FastAPI)
        │
        ▼
PostgreSQL Database
```

---

# Prasyarat

Pastikan sudah terinstall:

- Docker Desktop
- Python 3.10+
- Git
- Webcam lokal atau CCTV RTSP

---

# Menjalankan Sistem

## 1. Clone Repository

```powershell
git clone https://github.com/JohanArizona/capstone-a2-group6-k3-apd-vision-monitoring.git
```

Masuk ke project:

```powershell
cd capstone-a2-group6-k3-apd-vision-monitoring
```

---

# 2. Jalankan Backend + Frontend

Jalankan Docker Compose dari root project:

```powershell
docker compose up --build
```

Jika berhasil, akan muncul container:

```text
✔ Container capstone-db
✔ Container capstone-backend
✔ Container capstone-frontend
```

Service yang berjalan:

| Service | URL |
|---|---|
| Frontend Dashboard | http://localhost:5173 |
| Backend API | http://localhost:8001 |
| Swagger API Docs | http://localhost:8001/docs |

Untuk menjalankan di background:

```powershell
docker compose up -d --build
```

Untuk menghentikan service:

```powershell
docker compose down
```

---

# 3. Setup Edge Client

Masuk folder edge client:

```powershell
cd ppe-detection-api
```

Pastikan file `.env` tersedia dan minimal berisi:

```env
BACKEND_URL=http://localhost:8001

ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123

PPE_MODEL_PATH=app/models/ppe_model.pt

CONFIDENCE_THRESHOLD=0.5
MIN_VIOLATION_CONFIDENCE=0.5

WEBCAM_INDEX=0

EDGE_STREAM_HOST=0.0.0.0
EDGE_STREAM_PORT=8765
EDGE_STREAM_PATH=/stream.mjpg
```

Install dependency (sekali saja):

```powershell
py -m pip install -r requirements.txt
```

---

# 4. Jalankan Edge Client

Masih di folder `ppe-detection-api`:

```powershell
py edge_client.py
```

Jika berhasil, akan muncul log seperti:

```text
✅ YOLO model loaded
✅ Login success
✅ Video source OK
🎥 Starting detection
Edge stream server: http://localhost:8765/stream.mjpg
```

---

# 5. Pilih Kamera

Saat aplikasi berjalan, daftar kamera akan muncul:

```text
Available cameras:

[0] Lokasi Produksi A
[1] Lokasi Produksi B
[2] Lokasi Warehouse
[3] tes webcam
```

Pilih index kamera:

```text
Select camera index: 3
```

Contoh:
- `0` → Kamera produksi A
- `3` → Webcam lokal

---

# 6. Verifikasi Stream Relay

Cek health endpoint:

```powershell
Invoke-WebRequest -Uri "http://localhost:8765/health" -UseBasicParsing
```

Jika berhasil, MJPEG stream aktif di:

```text
http://localhost:8765/stream.mjpg
```

---

# 7. Akses Dashboard

Buka browser:

```text
http://localhost:5173
```

Login menggunakan akun yang tersedia.

---

# 8. Uji Full Flow Sistem

## Live Monitoring

- Buka halaman Live Monitoring
- Pastikan live feed tampil
- Feed berasal dari edge relay stream

## AI Detection

Lakukan simulasi:
- Tidak memakai helm
- Tidak memakai vest

Contoh log detection:

```text
⚠️ Missing APD: ['helmet']
📤 Violation uploaded
```

## Event Dashboard

Pastikan:
- Event pelanggaran muncul
- Analytics bertambah
- Riwayat tersimpan

---

# Troubleshooting

## Live Feed Tidak Tampil

Pastikan edge client berjalan:

```powershell
py edge_client.py
```

Cek health endpoint:

```text
http://localhost:8765/health
```

---

## Frontend Tidak Bisa Akses Stream

Pastikan frontend menggunakan:

```env
VITE_EDGE_MJPEG_URL=http://localhost:8765/stream.mjpg
```

Restart frontend/container setelah mengubah `.env`.

---

## Edge Client Gagal Login

Periksa:

```env
BACKEND_URL=http://localhost:8001
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
```

Pastikan backend container berjalan.

---

## Webcam Tidak Terdeteksi

- Tutup aplikasi lain yang memakai webcam
- Ubah:

```env
WEBCAM_INDEX=0
```

ke index lain.

---

# Catatan Penting

- Frontend tidak membuka webcam langsung.
- Webcam hanya digunakan oleh edge client.
- Frontend menerima stream dari MJPEG relay edge client.
- Sistem dapat menggunakan webcam lokal maupun CCTV RTSP.
- Pada deployment nyata, webcam dapat diganti dengan CCTV IP camera.

---

# Teknologi Yang Digunakan

| Teknologi | Fungsi |
|---|---|
| FastAPI | Backend API |
| PostgreSQL | Database |
| React + Vite | Frontend Dashboard |
| YOLOv8 | AI Detection |
| OpenCV | Video Processing |
| Docker Compose | Container orchestration |
| JWT | Authentication |

---

# Pengujian Sistem

Pengujian dilakukan secara fungsional dengan memastikan:

- Login berjalan
- Live feed tampil
- YOLO inference berjalan
- Pelanggaran terdeteksi
- Event tersimpan ke database
- Dashboard menampilkan data real-time
- Export laporan berhasil

---

# Lisensi

Project ini dikembangkan untuk kebutuhan Capstone Project APD Vision Monitoring System.
