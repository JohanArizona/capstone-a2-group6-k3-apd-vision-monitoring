# PPE Detection API

REST API untuk deteksi **Alat Pelindung Diri (APD)** menggunakan YOLOv8. API ini mendeteksi keberadaan dan pelanggaran penggunaan helm safety, rompi keselamatan, dan sepatu safety.

## Kelas Deteksi

| ID | Kelas | Deskripsi |
|----|-------|-----------|
| 0 | `hardhat` | Helm safety terdeteksi |
| 1 | `no_hardhat` | Tidak memakai helm |
| 2 | `vest` | Rompi keselamatan terdeteksi |
| 3 | `no_vest` | Tidak memakai rompi |
| 4 | `boots` | Sepatu safety terdeteksi |
| 5 | `no_boots` | Tidak memakai sepatu safety |

## Quick Start

### 1. Setup Environment

```bash
# Clone/masuk ke direktori
cd ppe-detection-api

# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Download Dataset

```bash
# Set Roboflow API key (dapatkan dari https://app.roboflow.com/settings/api)
export ROBOFLOW_API_KEY="your_api_key"

# Download dataset PPE-YOLO dari klema-ai
python training/merge_datasets.py --api-key $ROBOFLOW_API_KEY

# Dataset source: https://universe.roboflow.com/klema-ai/ppe-yolo-jrblc
# Classes: helmet, no-helmet, vest, no-vest, boots, no-boots (+ goggles, gloves, person)
```

### 3. Training Model

```bash
# Training dengan setting default (100 epochs, YOLOv8n)
python training/train.py --data datasets/merged/data.yaml

# Training dengan custom settings
python training/train.py \
    --data datasets/merged/data.yaml \
    --model yolov8s.pt \
    --epochs 150 \
    --batch 16 \
    --device 0

# Evaluasi model
python training/train.py --eval-only \
    --model runs/train/ppe_yolov8n_xxx/weights/best.pt \
    --data datasets/merged/data.yaml
```

### 4. Deploy Model

```bash
# Copy trained model ke folder models
cp runs/train/ppe_yolov8n_xxx/weights/best.pt models/ppe_model.pt

# Jalankan API server
python -m app.main

# Atau dengan gunicorn (production)
gunicorn -b 0.0.0.0:5000 -w 2 wsgi:app
```

### 5. Test API

```bash
# Health check
curl http://localhost:5000/health

# Deteksi dari file
curl -X POST -F "file=@test_image.jpg" http://localhost:5000/detect

# Deteksi dari URL
curl -X POST -H "Content-Type: application/json" \
    -d '{"url": "https://example.com/image.jpg"}' \
    http://localhost:5000/detect/url
```

## API Endpoints

### `GET /health`
Health check endpoint.

**Response:**
```json
{
    "status": "healthy",
    "model_loaded": true,
    "timestamp": "2026-03-05T10:30:00"
}
```

### `POST /detect`
Deteksi dari file upload.

**Request:**
- Content-Type: `multipart/form-data`
- `file`: Image file (required)
- `confidence`: Confidence threshold 0-1 (optional, default: 0.5)
- `return_image`: Return annotated image (optional, default: true)

**Response:**
```json
{
    "success": true,
    "detections": [
        {
            "class_id": 1,
            "class": "no_hardhat",
            "confidence": 0.87,
            "bbox": [120, 50, 280, 180],
            "label": "Tidak Memakai Helm",
            "is_violation": true
        }
    ],
    "total_detections": 3,
    "violations_count": 1,
    "violations": [...],
    "annotated_image": "data:image/jpeg;base64,/9j/4AAQ..."
}
```

### `POST /detect/url`
Deteksi dari URL gambar.

**Request:**
```json
{
    "url": "https://example.com/image.jpg",
    "confidence": 0.5,
    "return_image": true
}
```

### `POST /detect/base64`
Deteksi dari base64 encoded image.

**Request:**
```json
{
    "image": "data:image/jpeg;base64,/9j/4AAQ...",
    "confidence": 0.5,
    "return_image": true
}
```

### `POST /detect/violations`
Deteksi hanya pelanggaran (no_hardhat, no_vest, no_boots).

### `GET /classes`
List semua kelas deteksi.

### `GET /model/info`
Informasi model yang digunakan.

## Docker Deployment

```bash
# Build image
docker build -t ppe-detection-api .

# Run container
docker run -p 5000:5000 \
    -v ./models:/app/models:ro \
    ppe-detection-api

# Atau dengan docker-compose
docker-compose up -d
```

## Cloud Deployment

### Google Cloud Run

```bash
# Build dan push ke Container Registry
gcloud builds submit --tag gcr.io/PROJECT_ID/ppe-detection-api

# Deploy
gcloud run deploy ppe-detection-api \
    --image gcr.io/PROJECT_ID/ppe-detection-api \
    --platform managed \
    --memory 4Gi \
    --cpu 2 \
    --port 5000
```

### AWS ECS / EC2

```bash
# Push ke ECR
aws ecr get-login-password | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.REGION.amazonaws.com
docker tag ppe-detection-api:latest ACCOUNT.dkr.ecr.REGION.amazonaws.com/ppe-detection-api:latest
docker push ACCOUNT.dkr.ecr.REGION.amazonaws.com/ppe-detection-api:latest
```

## Project Structure

```
ppe-detection-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # Flask app & routes
│   ├── detector.py      # YOLOv8 inference wrapper
│   └── utils.py         # Utility functions
├── training/
│   ├── train.py         # Training script
│   ├── merge_datasets.py # Dataset merger
│   └── data.yaml        # Dataset config
├── models/
│   └── ppe_model.pt     # Trained model
├── datasets/            # Downloaded datasets
├── runs/                # Training outputs
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── wsgi.py
└── README.md
```

## Dataset Source

| Dataset | URL | Kelas |
|---------|-----|-------|
| **PPE-YOLO (klema-ai)** | https://universe.roboflow.com/klema-ai/ppe-yolo-jrblc | helmet, no-helmet, vest, no-vest, **boots**, **no-boots**, goggles, gloves, person |

**Kelas yang digunakan (6 dari 11):**
- `helmet` → `hardhat`
- `no-helmet` → `no_hardhat`
- `vest` → `vest`
- `no-vest` → `no_vest`
- `boots` → `boots`
- `no-boots` → `no_boots`

**Kelas yang di-skip:** goggles, no-goggles, gloves, no-gloves, person

## Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PPE_MODEL_PATH` | `models/ppe_model.pt` | Path ke model |
| `PPE_CONFIDENCE` | `0.5` | Confidence threshold |
| `PORT` | `5000` | Server port |
| `FLASK_DEBUG` | `false` | Debug mode |
| `ROBOFLOW_API_KEY` | - | API key untuk download dataset |

## Integration Example

### Python

```python
import requests

# Upload file
with open("test.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:5000/detect",
        files={"file": f},
        data={"confidence": 0.5}
    )

result = response.json()
print(f"Violations found: {result['violations_count']}")
for det in result['detections']:
    print(f"  - {det['class']}: {det['confidence']:.2f}")
```

### JavaScript

```javascript
// Using fetch
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:5000/detect', {
    method: 'POST',
    body: formData
});

const result = await response.json();
console.log(`Violations: ${result.violations_count}`);
```

## Performance

| Model | mAP@50 | Inference Time | Size |
|-------|--------|----------------|------|
| YOLOv8n | ~0.75 | ~30ms | 6MB |
| YOLOv8s | ~0.80 | ~50ms | 22MB |
| YOLOv8m | ~0.83 | ~90ms | 50MB |

*Tested on NVIDIA RTX 3060, 640x640 input*

## License

MIT License
