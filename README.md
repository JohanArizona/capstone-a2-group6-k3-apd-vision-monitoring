# APD Vision Monitoring - Full Test Guide

Panduan ini untuk menjalankan sistem end-to-end:
1. Backend API aktif.
2. Edge client aktif untuk deteksi model + stream relay MJPEG.
3. Frontend menampilkan live feed dari edge relay (bukan buka webcam langsung).

## Arsitektur Singkat

- Backend: FastAPI + PostgreSQL.
- Edge client: baca kamera, inferensi YOLO, kirim violation ke backend.
- Frontend: dashboard monitoring, events, analytics, live feed dari edge relay.

Live feed browser membaca:
- `http://localhost:8765/stream.mjpg`

## Prasyarat

- Windows 10/11.
- Python 3.10+.
- Node.js 18+.
- Git.
- Kamera/webcam lokal.

## 1) Jalankan Backend

Gunakan flow backend yang sudah ada di folder `backend/`.

Pilihan paling mudah (Docker):
1. Masuk ke folder `backend`.
2. Siapkan `.env` sesuai contoh yang tersedia di backend.
3. Jalankan:

```powershell
docker compose up --build
```

Jika backend berjalan di port 8001 (sesuai setup Anda), gunakan URL itu di frontend dan edge.

## 2) Siapkan Environment Edge Client

Masuk folder:

```powershell
cd ppe-detection-api
```

Pastikan `.env` minimal berisi:

```env
BACKEND_URL=http://localhost:8001
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
PPE_MODEL_PATH=app/models/ppe_model.pt
CONFIDENCE_THRESHOLD=0.5
MIN_VIOLATION_CONFIDENCE=0.5
WEBCAM_INDEX=0

# Edge relay stream untuk frontend
EDGE_STREAM_HOST=0.0.0.0
EDGE_STREAM_PORT=8765
EDGE_STREAM_PATH=/stream.mjpg
```

Install dependency (sekali saja):

```powershell
py -m pip install -r requirements.txt
```

## 3) Jalankan Edge Client (Deteksi + Relay)

Jalankan:

```powershell
py edge_client.py
```

Pilih kamera saat diminta.

Verifikasi relay hidup:

```powershell
Invoke-WebRequest -Uri "http://localhost:8765/health" -UseBasicParsing
```

Jika sukses, endpoint stream siap:
- `http://localhost:8765/stream.mjpg`

## 4) Jalankan Frontend

Masuk folder:

```powershell
cd frontend
```

Pastikan file `.env` berisi:

```env
VITE_API_BASE_URL=http://localhost:8001
VITE_EDGE_MJPEG_URL=http://localhost:8765/stream.mjpg
```

Install dan jalankan:

```powershell
npm install
npm run dev
```

Buka:
- `http://localhost:5173`

## 5) Uji Full Flow

1. Login dashboard.
2. Pilih kamera `tes webcam` (atau kamera local).
3. Cek halaman Live:
	- Feed harus tampil dari edge relay.
4. Cek Events:
	- Violation yang dikirim edge client muncul.
5. Cek Analytics:
	- Data statistik muncul mengikuti kamera terpilih.

## Troubleshooting Cepat

1. Live feed kosong, edge window berjalan:
	- Restart `edge_client.py` supaya pakai versi relay terbaru.
	- Cek `http://localhost:8765/health`.

2. Browser tetap tidak tampil, tapi `/health` OK:
	- Cek `VITE_EDGE_MJPEG_URL` di `frontend/.env`.
	- Restart `npm run dev` setelah ubah `.env`.

3. Edge gagal kirim violation:
	- Pastikan `BACKEND_URL` benar.
	- Cek login edge client berhasil.

4. Kamera tidak kebaca:
	- Tutup aplikasi lain yang memakai webcam.
	- Ubah `WEBCAM_INDEX`.

## Catatan Penting

- Frontend tidak lagi membuka webcam lokal langsung untuk mode local camera.
- Webcam dipegang edge client saja untuk mencegah konflik device.
- Frontend hanya konsumsi stream relay dari edge client.
