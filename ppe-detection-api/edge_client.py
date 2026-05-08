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
from http import server as http_server
from socketserver import ThreadingMixIn

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
# BACKEND API CLIENT
# =========================================================

class EdgeAPIClient:

    def __init__(
        self,
        backend_url: str,
        username: str,
        password: str
    ):

        self.backend_url = backend_url.rstrip("/")
        self.username = username
        self.password = password

        self.jwt_token = None

        self.session = requests.Session()

    def login(self) -> bool:

        try:

            logger.info(f"Login as {self.username}")

            response = self.session.post(
                f"{self.backend_url}/api/auth/login",
                json={
                    "username": self.username,
                    "password": self.password
                },
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

        return {
            "Authorization": f"Bearer {self.jwt_token}"
        }

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

    def send_violation(
        self,
        camera_id: str,
        missing_apd: Dict[str, bool],
        confidence_score: float,
        image_bytes: bytes,
        filename: str
    ) -> bool:

        try:

            files = {
                "snapshot": (
                    filename,
                    image_bytes,
                    "image/jpeg"
                )
            }

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
# PPE DETECTOR
# =========================================================

class PPEDetectionClient:

    CLASS_TO_APD = {
        "hardhat": "helmet",
        "no_hardhat": "helmet",

        "vest": "vest",
        "no_vest": "vest",

        "boots": "boots",
        "no_boots": "boots"
    }

    CLASS_IS_MISSING = {
        "hardhat": False,
        "no_hardhat": True,

        "vest": False,
        "no_vest": True,

        "boots": False,
        "no_boots": True
    }

    def __init__(
        self,
        model_path: str,
        confidence_threshold: float = 0.5
    ):

        self.model_path = model_path

        self.confidence_threshold = confidence_threshold

        self.model = None

        self.load_model()

    def load_model(self):

        try:

            from ultralytics import YOLO
            import torch

            # compatibility patch
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

    def detect(
        self,
        frame: np.ndarray
    ) -> Tuple[list, Dict, float]:

        if self.model is None:
            return [], {}, 0.0

        try:

            results = self.model(
                frame,
                conf=self.confidence_threshold,
                verbose=False
            )

            detections = []

            missing_apd = {
                "helmet": False,
                "vest": False,
                "boots": False
            }

            confidences = []

            for result in results:

                if result.boxes is None:
                    continue

                for box in result.boxes:

                    class_id = int(box.cls[0])

                    confidence = float(box.conf[0])

                    class_name = result.names[class_id]

                    bbox = box.xyxy[0].tolist()

                    detections.append({
                        "class": class_name,
                        "confidence": confidence,
                        "bbox": bbox
                    })

                    confidences.append(confidence)

                    if class_name in self.CLASS_TO_APD:

                        apd_key = self.CLASS_TO_APD[class_name]

                        is_missing = self.CLASS_IS_MISSING[class_name]

                        if is_missing:
                            missing_apd[apd_key] = True

            avg_confidence = (
                np.mean(confidences)
                if confidences
                else 0.0
            )

            return detections, missing_apd, avg_confidence

        except Exception as e:

            logger.error(f"Detection error: {e}")

            return [], {}, 0.0

    def annotate_frame(self, frame, detections):

        annotated = frame.copy()

        colors = {
            "hardhat": (0, 255, 0),
            "vest": (0, 255, 0),
            "boots": (0, 255, 0),

            "no_hardhat": (0, 0, 255),
            "no_vest": (0, 0, 255),
            "no_boots": (0, 0, 255),
        }

        for det in detections:

            class_name = det["class"]

            confidence = det["confidence"]

            bbox = det["bbox"]

            x1, y1, x2, y2 = map(int, bbox)

            color = colors.get(
                class_name,
                (255, 255, 255)
            )

            cv2.rectangle(
                annotated,
                (x1, y1),
                (x2, y2),
                color,
                2
            )

            label = f"{class_name} {confidence:.2f}"

            cv2.putText(
                annotated,
                label,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                color,
                2
            )

        return annotated


# =========================================================
# EDGE DEVICE APP
# =========================================================

class EdgeDeviceApp:

    def __init__(self):

        load_dotenv()

        # =====================================================
        # ENV CONFIG
        # =====================================================

        self.backend_url = os.getenv(
            "BACKEND_URL",
            "http://localhost:8000"
        )

        self.admin_username = os.getenv(
            "ADMIN_USERNAME",
            "admin"
        )

        self.admin_password = os.getenv(
            "ADMIN_PASSWORD",
            "admin123"
        )

        self.model_path = os.getenv(
            "PPE_MODEL_PATH",
            "app/models/ppe_model.pt"
        )

        self.confidence_threshold = float(
            os.getenv("CONFIDENCE_THRESHOLD", "0.5")
        )

        self.webcam_index = int(
            os.getenv("WEBCAM_INDEX", "0")
        )

        self.min_violation_confidence = float(
            os.getenv("MIN_VIOLATION_CONFIDENCE", "0.5")
        )

        self.edge_stream_host = os.getenv(
            "EDGE_STREAM_HOST",
            "0.0.0.0"
        )

        self.edge_stream_port = int(
            os.getenv("EDGE_STREAM_PORT", "8765")
        )

        self.edge_stream_path = os.getenv(
            "EDGE_STREAM_PATH",
            "/stream.mjpg"
        )

        # =====================================================
        # PERFORMANCE SETTINGS
        # =====================================================

        self.frame_skip = 3

        self.violation_cooldown = 5

        self.running = False

        self.camera_id = None

        self.last_violation_time = 0

        self.last_detections = []

        self.last_confidence = 0.0
        self.selected_camera_source = None

        self.stream_server = None
        self.stream_server_thread = None
        self.latest_stream_frame = None
        self.stream_lock = threading.Lock()

        # =====================================================
        # UPLOAD QUEUE
        # =====================================================

        self.upload_queue = queue.Queue(maxsize=20)

        # =====================================================
        # CLIENTS
        # =====================================================

        self.api_client = EdgeAPIClient(
            self.backend_url,
            self.admin_username,
            self.admin_password
        )

        self.detector = PPEDetectionClient(
            self.model_path,
            self.confidence_threshold
        )

    def update_stream_frame(self, frame):

        ok, buffer = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, 80]
        )

        if not ok:
            return

        with self.stream_lock:
            self.latest_stream_frame = buffer.tobytes()

    def start_stream_server(self):

        app = self

        class ThreadedHTTPServer(ThreadingMixIn, http_server.HTTPServer):
            daemon_threads = True

        class StreamHandler(http_server.BaseHTTPRequestHandler):

            def log_message(self, format, *args):
                return

            def do_GET(self):

                if self.path in ["/", "/health"]:
                    payload = b'{"status":"ok","service":"edge-stream"}'
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                    return

                if self.path != app.edge_stream_path:
                    self.send_error(404)
                    return

                self.send_response(200)
                self.send_header("Age", "0")
                self.send_header("Cache-Control", "no-cache, private")
                self.send_header("Pragma", "no-cache")
                self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=frame")
                self.end_headers()

                try:
                    while app.running:
                        with app.stream_lock:
                            frame = app.latest_stream_frame

                        if frame is None:
                            time.sleep(0.05)
                            continue

                        self.wfile.write(b"--frame\r\n")
                        self.wfile.write(b"Content-Type: image/jpeg\r\n")
                        self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode())
                        self.wfile.write(frame)
                        self.wfile.write(b"\r\n")
                        time.sleep(0.04)

                except (BrokenPipeError, ConnectionResetError):
                    return
                except Exception as e:
                    logger.debug(f"Stream client disconnected: {e}")

        self.stream_server = ThreadedHTTPServer(
            (self.edge_stream_host, self.edge_stream_port),
            StreamHandler
        )

        self.stream_server_thread = threading.Thread(
            target=self.stream_server.serve_forever,
            daemon=True
        )
        self.stream_server_thread.start()

        logger.info(
            f"Edge stream server: http://localhost:{self.edge_stream_port}{self.edge_stream_path}"
        )

    def stop_stream_server(self):

        if self.stream_server is None:
            return

        try:
            self.stream_server.shutdown()
            self.stream_server.server_close()
        except Exception:
            pass

        self.stream_server = None
        self.stream_server_thread = None

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

        # Windows webcam devices are often more stable on DirectShow than MSMF.
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

        # Try selected source first.
        cap = self.probe_capture(preferred_source)
        if cap is not None:
            return cap, preferred_source

        # For local webcam testing, scan common indexes.
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

    # =====================================================
    # SETUP
    # =====================================================

    def setup(self):

        logger.info("=" * 60)
        logger.info("PPE EDGE DEVICE")
        logger.info("=" * 60)

        if not self.api_client.login():
            return False

        if self.detector.model is None:
            logger.error(f"Model unavailable at path: {self.model_path}")
            return False

        logger.info(f"Model path: {self.model_path}")

        cameras = self.api_client.get_cameras()

        if not cameras:
            logger.error("No cameras available")
            return False

        logger.info("\nAvailable cameras:\n")

        for idx, cam in enumerate(cameras):

            print(f"[{idx}] {cam['name']}")
            print(f"     ID: {cam['id']}")
            print(f"     Location: {cam['location']}")
            print()

        choice = input("Select camera index: ").strip()

        try:

            idx = int(choice)

            selected_camera = cameras[idx]

            self.camera_id = selected_camera["id"]
            self.selected_camera_source = self.resolve_video_source(selected_camera)

        except:
            logger.error("Invalid camera")
            return False

        logger.info(f"Using camera ID: {self.camera_id}")
        logger.info(f"Using source: {self.selected_camera_source}")

        # =====================================================
        # TEST WEBCAM
        # =====================================================

        cap, working_source = self.find_working_capture(self.selected_camera_source)
        if cap is None:
            logger.error("Video source failed")
            return False

        self.selected_camera_source = working_source
        logger.info(f"Video source active: {self.selected_camera_source}")
        cap.release()

        logger.info("✅ Video source OK")
        logger.info("✅ Setup complete")

        return True

    # =====================================================
    # BACKGROUND UPLOAD THREAD
    # =====================================================

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

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def run(self):

        logger.info("🎥 Starting detection")

        self.running = True

        self.start_stream_server()

        # =====================================================
        # START BACKGROUND THREAD
        # =====================================================

        threading.Thread(
            target=self.upload_worker,
            daemon=True
        ).start()

        # =====================================================
        # OPEN WEBCAM
        # =====================================================

        cap, working_source = self.find_working_capture(self.selected_camera_source)

        if cap is None:
            logger.error("Cannot open video source")
            return

        self.selected_camera_source = working_source
        logger.info(f"Run with source: {self.selected_camera_source}")

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        frame_count = 0

        try:

            while self.running:

                ret, frame = cap.read()

                if not ret:
                    logger.error("Cannot read frame")
                    break

                frame_count += 1

                # =================================================
                # RESIZE FOR PERFORMANCE
                # =================================================

                frame = cv2.resize(frame, (416, 416))

                # =================================================
                # FRAME SKIP
                # =================================================

                if frame_count % self.frame_skip != 0:

                    annotated_skip = self.detector.annotate_frame(
                        frame,
                        self.last_detections
                    )

                    status_text = (
                        f"Detection: {len(self.last_detections)} | "
                        f"Conf: {self.last_confidence:.2f}"
                    )

                    cv2.putText(
                        annotated_skip,
                        status_text,
                        (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 255, 0),
                        2
                    )

                    cv2.imshow(
                        "PPE Detection - Press Q to Exit",
                        annotated_skip
                    )

                    self.update_stream_frame(annotated_skip)

                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break

                    continue

                # =================================================
                # DETECTION
                # =================================================

                detections, missing_apd, avg_confidence = (
                    self.detector.detect(frame)
                )

                self.last_detections = detections

                self.last_confidence = avg_confidence

                # =================================================
                # ANNOTATION
                # =================================================

                annotated = self.detector.annotate_frame(
                    frame,
                    detections
                )

                # =================================================
                # STATUS TEXT
                # =================================================

                status_text = (
                    f"Detection: {len(detections)} | "
                    f"Conf: {avg_confidence:.2f}"
                )

                cv2.putText(
                    annotated,
                    status_text,
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )

                # =================================================
                # DETAIL LOG
                # =================================================

                if frame_count % 30 == 0:

                    missing_items = [
                        k for k, v in missing_apd.items()
                        if v
                    ]

                    detected_classes = [
                        det["class"]
                        for det in detections
                    ]

                    logger.info(
                        f"Frame {frame_count} | "
                        f"Classes: {detected_classes} | "
                        f"Missing: {missing_items} | "
                        f"Confidence: {avg_confidence:.2f}"
                    )

                # =================================================
                # CHECK VIOLATION
                # =================================================

                has_violation = any(missing_apd.values())

                current_time = time.time()

                if (
                    has_violation and
                    avg_confidence >= self.min_violation_confidence and
                    current_time - self.last_violation_time >= self.violation_cooldown
                ):

                    missing_items = [
                        k for k, v in missing_apd.items()
                        if v
                    ]

                    logger.warning(
                        f"⚠️ Missing APD: {missing_items}"
                    )

                    # =============================================
                    # ANNOTATED SNAPSHOT
                    # =============================================

                    snapshot = annotated.copy()

                    timestamp_text = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )

                    cv2.putText(
                        snapshot,
                        timestamp_text,
                        (10, snapshot.shape[0] - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )

                    _, buffer = cv2.imencode(
                        ".jpg",
                        snapshot
                    )

                    timestamp = datetime.now().strftime(
                        "%Y%m%d_%H%M%S"
                    )

                    # =============================================
                    # BACKGROUND QUEUE
                    # =============================================

                    if not self.upload_queue.full():

                        self.upload_queue.put({

                            "camera_id": self.camera_id,

                            "missing_apd": missing_apd,

                            "confidence_score": avg_confidence,

                            "image_bytes": buffer.tobytes(),

                            "filename":
                                f"violation_{timestamp}.jpg"
                        })

                        self.last_violation_time = current_time

                # =================================================
                # DISPLAY
                # =================================================

                cv2.imshow(
                    "PPE Detection - Press Q to Exit",
                    annotated
                )

                self.update_stream_frame(annotated)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

        except KeyboardInterrupt:

            logger.info("Stopped by user")

        except Exception as e:

            logger.error(f"Runtime error: {e}")

        finally:

            self.running = False

            self.stop_stream_server()

            cap.release()

            cv2.destroyAllWindows()

            logger.info("Application stopped")


# =========================================================
# MAIN
# =========================================================

def main():

    app = EdgeDeviceApp()

    if not app.setup():
        sys.exit(1)

    app.run()


if __name__ == "__main__":
    main()