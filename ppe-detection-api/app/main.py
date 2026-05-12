"""
PPE Detection Flask API
========================
REST API untuk deteksi APD (Alat Pelindung Diri) menggunakan YOLOv8.

Endpoints:
- POST /detect          : Deteksi dari file upload
- POST /detect/url      : Deteksi dari URL gambar
- POST /detect/base64   : Deteksi dari base64 image
- GET  /health          : Health check
- GET  /classes         : List kelas yang dideteksi
- GET  /model/info      : Informasi model

Environment Variables:
- PPE_MODEL_PATH   : Path ke model .pt (default: models/ppe_model.pt)
- PPE_CONFIDENCE   : Confidence threshold (default: 0.5)
- FLASK_DEBUG      : Enable debug mode (default: False)
- PORT             : Server port (default: 5000)
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from .detector import PPEDetector, get_detector, CLASS_NAMES, CLASS_LABELS
from .utils import (
    validate_image_file,
    download_image,
    save_temp_image,
    cleanup_temp_file,
    format_response,
    get_model_info
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration from environment
MODEL_PATH = os.environ.get("PPE_MODEL_PATH", "models/ppe_model.pt")
CONFIDENCE = float(os.environ.get("PPE_CONFIDENCE", "0.5"))

# Initialize detector lazily
_detector = None


def get_detector_instance() -> PPEDetector:
    """Get or create detector instance."""
    global _detector
    if _detector is None:
        logger.info(f"Initializing detector with model: {MODEL_PATH}")
        _detector = PPEDetector(
            model_path=MODEL_PATH,
            confidence_threshold=CONFIDENCE
        )
    return _detector


# ============================================================
# API Routes
# ============================================================

@app.route("/", methods=["GET"])
def index():
    """Root endpoint - API info."""
    return jsonify({
        "name": "PPE Detection API",
        "version": "1.0.0",
        "description": "Deteksi APD (Alat Pelindung Diri) menggunakan YOLOv8",
        "endpoints": {
            "POST /detect": "Deteksi dari file upload",
            "POST /detect/url": "Deteksi dari URL gambar",
            "POST /detect/base64": "Deteksi dari base64 image",
            "GET /health": "Health check",
            "GET /classes": "List kelas deteksi",
            "GET /model/info": "Informasi model"
        },
        "classes": list(CLASS_NAMES.values())
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    detector = get_detector_instance()
    
    return jsonify({
        "status": "healthy" if detector.is_loaded else "degraded",
        "model_loaded": detector.is_loaded,
        "timestamp": datetime.utcnow().isoformat()
    })


@app.route("/classes", methods=["GET"])
def classes():
    """Get list of detection classes."""
    return jsonify({
        "classes": CLASS_NAMES,
        "labels": CLASS_LABELS,
        "total": len(CLASS_NAMES)
    })


@app.route("/model/info", methods=["GET"])
def model_info():
    """Get model information."""
    detector = get_detector_instance()
    info = get_model_info(detector)
    return jsonify(info)


@app.route("/detect", methods=["POST"])
def detect_upload():
    """
    Detect PPE from uploaded image file.
    
    Request:
        - Content-Type: multipart/form-data
        - file: Image file (required)
        - confidence: Confidence threshold (optional, default: 0.5)
        - return_image: Return annotated image (optional, default: true)
    
    Response:
        {
            "success": true,
            "detections": [...],
            "violations_count": 1,
            "annotated_image": "data:image/jpeg;base64,..."
        }
    """
    # Validate file
    if "file" not in request.files:
        return jsonify(*format_response(False, error="No file provided"))
    
    file = request.files["file"]
    is_valid, error = validate_image_file(file)
    
    if not is_valid:
        return jsonify(*format_response(False, error=error))
    
    # Get parameters
    confidence = request.form.get("confidence", type=float)
    return_image = request.form.get("return_image", "true").lower() == "true"
    
    # Run detection
    try:
        detector = get_detector_instance()
        image_bytes = file.read()
        
        result = detector.process(
            image=image_bytes,
            confidence=confidence,
            return_annotated=return_image
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify(*format_response(False, error=str(e), status_code=500))


@app.route("/detect/url", methods=["POST"])
def detect_url():
    """
    Detect PPE from image URL.
    
    Request:
        - Content-Type: application/json
        - url: Image URL (required)
        - confidence: Confidence threshold (optional)
        - return_image: Return annotated image (optional, default: true)
    
    Response:
        Same as /detect
    """
    data = request.get_json()
    
    if not data or "url" not in data:
        return jsonify(*format_response(False, error="URL is required"))
    
    url = data["url"]
    confidence = data.get("confidence")
    return_image = data.get("return_image", True)
    
    # Download image
    image_bytes = download_image(url)
    
    if image_bytes is None:
        return jsonify(*format_response(
            False, 
            error="Failed to download image from URL"
        ))
    
    # Run detection
    try:
        detector = get_detector_instance()
        
        result = detector.process(
            image=image_bytes,
            confidence=confidence,
            return_annotated=return_image
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify(*format_response(False, error=str(e), status_code=500))


@app.route("/detect/base64", methods=["POST"])
def detect_base64():
    """
    Detect PPE from base64 encoded image.
    
    Request:
        - Content-Type: application/json
        - image: Base64 encoded image (required)
        - confidence: Confidence threshold (optional)
        - return_image: Return annotated image (optional, default: true)
    
    Response:
        Same as /detect
    """
    import base64
    
    data = request.get_json()
    
    if not data or "image" not in data:
        return jsonify(*format_response(False, error="Image is required"))
    
    image_data = data["image"]
    confidence = data.get("confidence")
    return_image = data.get("return_image", True)
    
    # Remove data URI prefix if present
    if "," in image_data:
        image_data = image_data.split(",", 1)[1]
    
    # Decode base64
    try:
        image_bytes = base64.b64decode(image_data)
    except Exception as e:
        return jsonify(*format_response(False, error=f"Invalid base64: {e}"))
    
    # Run detection
    try:
        detector = get_detector_instance()
        
        result = detector.process(
            image=image_bytes,
            confidence=confidence,
            return_annotated=return_image
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify(*format_response(False, error=str(e), status_code=500))


@app.route("/detect/violations", methods=["POST"])
def detect_violations_only():
    """
    Detect only PPE violations (no_hardhat, no_vest, no_boots).
    
    Request:
        Same as /detect
    
    Response:
        Same as /detect, but only violation detections
    """
    if "file" not in request.files:
        return jsonify(*format_response(False, error="No file provided"))
    
    file = request.files["file"]
    is_valid, error = validate_image_file(file)
    
    if not is_valid:
        return jsonify(*format_response(False, error=error))
    
    confidence = request.form.get("confidence", type=float)
    return_image = request.form.get("return_image", "true").lower() == "true"
    
    try:
        detector = get_detector_instance()
        image_bytes = file.read()
        
        # Detect violations only
        violations = detector.detect_violations(image_bytes, confidence=confidence)
        
        result = {
            "success": True,
            "detections": [v.to_dict() for v in violations],
            "violations_count": len(violations)
        }
        
        # Annotate if requested
        if return_image and violations:
            annotated = detector.annotate(image_bytes, violations)
            result["annotated_image"] = detector.image_to_base64(annotated)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify(*format_response(False, error=str(e), status_code=500))


# ============================================================
# Error Handlers
# ============================================================

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"success": False, "error": "Bad request"}), 400


@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"success": False, "error": "Method not allowed"}), 405


@app.errorhandler(413)
def request_entity_too_large(e):
    return jsonify({"success": False, "error": "File too large"}), 413


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return jsonify({"success": False, "error": "Internal server error"}), 500


# ============================================================
# Main Entry Point
# ============================================================

def create_app():
    """Application factory."""
    return app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║             PPE Detection API Server                     ║
╠══════════════════════════════════════════════════════════╣
║  Model: {MODEL_PATH:<48} ║
║  Confidence: {CONFIDENCE:<44} ║
║  Port: {port:<50} ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Pre-load model
    logger.info("Pre-loading model...")
    get_detector_instance()
    
    app.run(host="0.0.0.0", port=port, debug=debug)
