"""
PPE Edge Client - Headless Docker Mode
========================================
Runs detection inference in a loop and pushes violations
to the backend API. No GUI, no interactive input.

Environment variables:
  BACKEND_URL             - Backend API base URL (default: http://backend:8000)
  ADMIN_USERNAME          - Login username
  ADMIN_PASSWORD          - Login password
  PPE_MODEL_PATH          - Path to YOLO .pt model
  CONFIDENCE_THRESHOLD    - Model confidence threshold
  MIN_VIOLATION_CONFIDENCE - Min confidence to report a violation
  CAMERA_INDEX            - Which camera to auto-select (0-based, default: 0)
  WEBCAM_INDEX            - OpenCV VideoCapture index (default: 0)
  HEADLESS                - If "true", skip cv2.imshow (default: true)
  STARTUP_DELAY           - Seconds to wait before first connection attempt
"""

import os
import json
import sys
import cv2
import time
import queue
import logging
import threading
import requests
import numpy as np
import platform

from datetime import datetime
from typing import Dict, Tuple
from dotenv import load_dotenv

# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# =========================================================
# BACKEND API CLIENT (same as original)
# =========================================================

class EdgeAPIClient:

    def __init__(self, backend_url: str, username: str, password: str):
        self.backend_url = backend_url.rstrip("/")
        self.username = username
        self.password = password
        self.jwt_token = None
        self.session = requests.Session()

    def login(self) -> bool:
        try:
            logger.info(f"Login as {self.username} to {self.backend_url}")
            response = self.session.post(
                f"{self.backend_url}/api/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=10
            )
            if response.status_code != 200:
                logger.error(f"Login failed: {response.text}")
                return False
            data = response.json()
            self.jwt_token = data.get("access_token")
            if not self.jwt_token:
                logger.error("JWT token not found")
                return False
            logger.info("✅ Login success")
            return True
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False

    def get_headers(self):
        return {"Authorization": f"Bearer {self.jwt_token}"}

    def get_cameras(self):
        try:
            response = self.session.get(
                f"{self.backend_url}/api/cameras",
                headers=self.get_headers(),
                timeout=10
            )
            if response.status_code != 200:
                logger.error("Failed fetch cameras")
                return []
            return response.json()
        except Exception as e:
            logger.error(f"Camera fetch error: {e}")
            return []

    def send_violation(self, camera_id, missing_apd, confidence_score, image_bytes, filename) -> bool:
        try:
            files = {"snapshot": (filename, image_bytes, "image/jpeg")}
            data = {
                "camera_id": camera_id,
                "missing_apd": json.dumps(missing_apd),
                "confidence_score": confidence_score
            }
            response = self.session.post(
                f"{self.backend_url}/api/violations",
                headers=self.get_headers(),
                files=files,
                data=data,
                timeout=15
            )
            if response.status_code == 201:
                logger.info("📤 Violation uploaded")
                return True
            logger.error(f"Upload failed: {response.text}")
            return False
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False


# =========================================================
# PPE DETECTOR (same as original)
# =========================================================

class PPEDetectionClient:

    CLASS_TO_APD = {
        "hardhat": "helmet", "no_hardhat": "helmet",
        "vest": "vest", "no_vest": "vest",
        "boots": "boots", "no_boots": "boots"
    }

    CLASS_IS_MISSING = {
        "hardhat": False, "no_hardhat": True,
        "vest": False, "no_vest": True,
        "boots": False, "no_boots": True
    }

    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.load_model()

    def load_model(self):
        try:
            from ultralytics import YOLO
            import torch

            original_load = torch.load

            def patched_load(*args, **kwargs):
                if "weights_only" not in kwargs:
                    kwargs["weights_only"] = False
                return original_load(*args, **kwargs)

            torch.load = patched_load

            if not os.path.exists(self.model_path):
                logger.error(f"Model not found: {self.model_path}")
                return

            self.model = YOLO(self.model_path)
            logger.info("✅ YOLO model loaded")
        except Exception as e:
            logger.error(f"Model load error: {e}")

    def detect(self, frame: np.ndarray) -> Tuple[list, Dict, float]:
        if self.model is None:
            return [], {}, 0.0
        try:
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            detections = []
            missing_apd = {"helmet": False, "vest": False, "boots": False}
            confidences = []

            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    class_name = result.names[class_id]
                    bbox = box.xyxy[0].tolist()
                    detections.append({"class": class_name, "confidence": confidence, "bbox": bbox})
                    confidences.append(confidence)
                    if class_name in self.CLASS_TO_APD:
                        apd_key = self.CLASS_TO_APD[class_name]
                        if self.CLASS_IS_MISSING[class_name]:
                            missing_apd[apd_key] = True

            avg_confidence = np.mean(confidences) if confidences else 0.0
            return detections, missing_apd, avg_confidence
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return [], {}, 0.0

    def annotate_frame(self, frame, detections):
        annotated = frame.copy()
        colors = {
            "hardhat": (0, 255, 0), "vest": (0, 255, 0), "boots": (0, 255, 0),
            "no_hardhat": (0, 0, 255), "no_vest": (0, 0, 255), "no_boots": (0, 0, 255),
        }
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bbox"])
            color = colors.get(det["class"], (255, 255, 255))
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            label = f"{det['class']} {det['confidence']:.2f}"
            cv2.putText(annotated, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        return annotated


# =========================================================
# HEADLESS EDGE DEVICE
# =========================================================

class HeadlessEdgeDevice:

    def __init__(self):
        load_dotenv()

        self.backend_url = os.getenv("BACKEND_URL", "http://backend:8000")
        self.admin_username = os.getenv("ADMIN_USERNAME", "admin")
        self.admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        self.model_path = os.getenv("PPE_MODEL_PATH", "app/models/ppe_model.pt")
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
        self.webcam_index = int(os.getenv("WEBCAM_INDEX", "0"))
        self.camera_index = int(os.getenv("CAMERA_INDEX", "0"))
        self.min_violation_confidence = float(os.getenv("MIN_VIOLATION_CONFIDENCE", "0.5"))
        self.startup_delay = int(os.getenv("STARTUP_DELAY", "10"))

        self.frame_skip = 3
        self.violation_cooldown = 5
        self.running = False
        self.camera_id = None
        self.selected_camera_source = None
        self.last_violation_time = 0

        self.upload_queue = queue.Queue(maxsize=20)

        self.api_client = EdgeAPIClient(
            self.backend_url, self.admin_username, self.admin_password
        )
        self.detector = PPEDetectionClient(
            self.model_path, self.confidence_threshold
        )

    def resolve_video_source(self, camera_data=None):
        source = None
        if camera_data:
            source = (camera_data.get("rtsp_url") or "").strip()

        if not source:
            return self.webcam_index

        if source.startswith("local://webcam"):
            parts = source.split("/")
            if parts and parts[-1].isdigit():
                return int(parts[-1])
            return self.webcam_index

        if source.startswith("local://placeholder"):
            return self.webcam_index

        return source

    def open_capture(self, source):
        if isinstance(source, int):
            if platform.system().lower() == "windows":
                cap = cv2.VideoCapture(source, cv2.CAP_DSHOW)
                if cap.isOpened():
                    return cap
            return cv2.VideoCapture(source)
        return cv2.VideoCapture(source)

    def probe_capture(self, source, attempts=8):
        cap = self.open_capture(source)

        if not cap.isOpened():
            cap.release()
            return None

        for _ in range(attempts):
            ok, _ = cap.read()
            if ok:
                return cap
            time.sleep(0.08)

        cap.release()
        return None

    def find_working_capture(self, preferred_source):
        cap = self.probe_capture(preferred_source)
        if cap is not None:
            return cap, preferred_source

        if isinstance(preferred_source, int):
            fallbacks = [preferred_source, 0, 1, 2, 3]
            seen = set()
            for index in fallbacks:
                if index in seen:
                    continue
                seen.add(index)
                cap = self.probe_capture(index)
                if cap is not None:
                    return cap, index

        return None, preferred_source

    def wait_for_backend(self, max_retries=30, delay=5):
        """Wait until the backend health endpoint responds."""
        logger.info(f"⏳ Waiting {self.startup_delay}s before connecting to backend...")
        time.sleep(self.startup_delay)

        for attempt in range(1, max_retries + 1):
            try:
                resp = requests.get(f"{self.backend_url}/health", timeout=5)
                if resp.status_code == 200:
                    logger.info("✅ Backend is reachable")
                    return True
            except Exception:
                pass
            logger.info(f"Backend not ready (attempt {attempt}/{max_retries}), retrying in {delay}s...")
            time.sleep(delay)

        logger.error("❌ Backend not reachable after max retries")
        return False

    def setup(self) -> bool:
        logger.info("=" * 60)
        logger.info("PPE EDGE DEVICE (HEADLESS / DOCKER)")
        logger.info("=" * 60)

        if not self.wait_for_backend():
            return False

        if not self.api_client.login():
            return False

        if self.detector.model is None:
            logger.error(f"Model unavailable at path: {self.model_path}")
            return False

        logger.info(f"Model path: {self.model_path}")

        cameras = self.api_client.get_cameras()
        if not cameras:
            logger.error("No cameras registered in backend")
            return False

        idx = min(self.camera_index, len(cameras) - 1)
        selected_camera = cameras[idx]
        self.camera_id = selected_camera["id"]
        self.selected_camera_source = self.resolve_video_source(selected_camera)
        logger.info(f"Auto-selected camera: {selected_camera['name']} (ID: {self.camera_id})")
        logger.info(f"Using source: {self.selected_camera_source}")

        # Test webcam
        cap, working_source = self.find_working_capture(self.selected_camera_source)
        if cap is None:
            logger.warning("⚠️ Video source not available — will retry in main loop")
        else:
            self.selected_camera_source = working_source
            logger.info(f"Video source active: {self.selected_camera_source}")
            cap.release()

        logger.info("✅ Setup complete")
        return True

    def upload_worker(self):
        while self.running:
            try:
                item = self.upload_queue.get(timeout=1)
                self.api_client.send_violation(
                    camera_id=item["camera_id"],
                    missing_apd=item["missing_apd"],
                    confidence_score=item["confidence_score"],
                    image_bytes=item["image_bytes"],
                    filename=item["filename"]
                )
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Upload worker error: {e}")

    def run(self):
        logger.info("🎥 Starting headless detection loop")
        self.running = True

        threading.Thread(target=self.upload_worker, daemon=True).start()

        cap, working_source = self.find_working_capture(self.selected_camera_source)

        if cap is None:
            logger.error("Cannot open video source — exiting")
            return

        self.selected_camera_source = working_source
        logger.info(f"Run with source: {self.selected_camera_source}")

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        frame_count = 0
        last_detections = []
        last_confidence = 0.0

        try:
            while self.running:
                ret, frame = cap.read()
                if not ret:
                    logger.error("Cannot read frame, retrying in 2s...")
                    time.sleep(2)
                    continue

                frame_count += 1
                frame = cv2.resize(frame, (416, 416))

                if frame_count % self.frame_skip != 0:
                    continue

                detections, missing_apd, avg_confidence = self.detector.detect(frame)
                last_detections = detections
                last_confidence = avg_confidence

                if frame_count % 30 == 0:
                    missing_items = [k for k, v in missing_apd.items() if v]
                    detected_classes = [d["class"] for d in detections]
                    logger.info(
                        f"Frame {frame_count} | "
                        f"Classes: {detected_classes} | "
                        f"Missing: {missing_items} | "
                        f"Confidence: {avg_confidence:.2f}"
                    )

                has_violation = any(missing_apd.values())
                current_time = time.time()

                if (
                    has_violation
                    and avg_confidence >= self.min_violation_confidence
                    and current_time - self.last_violation_time >= self.violation_cooldown
                ):
                    missing_items = [k for k, v in missing_apd.items() if v]
                    logger.warning(f"⚠️ Missing APD: {missing_items}")

                    annotated = self.detector.annotate_frame(frame, detections)
                    timestamp_text = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(
                        annotated, timestamp_text,
                        (10, annotated.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2
                    )
                    _, buffer = cv2.imencode(".jpg", annotated)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

                    if not self.upload_queue.full():
                        self.upload_queue.put({
                            "camera_id": self.camera_id,
                            "missing_apd": missing_apd,
                            "confidence_score": avg_confidence,
                            "image_bytes": buffer.tobytes(),
                            "filename": f"violation_{timestamp}.jpg"
                        })
                        self.last_violation_time = current_time

        except KeyboardInterrupt:
            logger.info("Stopped by user")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        finally:
            self.running = False
            cap.release()
            logger.info("Application stopped")


# =========================================================
# MAIN
# =========================================================

def main():
    app = HeadlessEdgeDevice()
    if not app.setup():
        logger.error("Setup failed, exiting...")
        sys.exit(1)
    app.run()


if __name__ == "__main__":
    main()
