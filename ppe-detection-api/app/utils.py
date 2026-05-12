"""
Utility functions for PPE Detection API
"""

import os
import io
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple
import requests

logger = logging.getLogger(__name__)

# Supported image formats
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16 MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and \
           filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def validate_image_file(file) -> Tuple[bool, str]:
    """
    Validate uploaded image file.
    
    Args:
        file: FileStorage object from Flask
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if file is None:
        return False, "No file provided"
    
    if file.filename == "":
        return False, "No file selected"
    
    if not allowed_file(file.filename):
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size (read and reset position)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, ""


def download_image(url: str, timeout: int = 10) -> Optional[bytes]:
    """
    Download image from URL.
    
    Args:
        url: Image URL
        timeout: Request timeout in seconds
    
    Returns:
        Image bytes or None if failed
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "PPE-Detection-API/1.0"}
        )
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            logger.warning(f"Invalid content type: {content_type}")
            return None
        
        # Validate size
        if len(response.content) > MAX_FILE_SIZE:
            logger.warning(f"Image too large: {len(response.content)} bytes")
            return None
        
        return response.content
        
    except requests.RequestException as e:
        logger.error(f"Failed to download image: {e}")
        return None


def save_temp_image(image_bytes: bytes, suffix: str = ".jpg") -> str:
    """
    Save image bytes to temporary file.
    
    Args:
        image_bytes: Image data
        suffix: File suffix
    
    Returns:
        Path to temporary file
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        os.write(fd, image_bytes)
    finally:
        os.close(fd)
    return path


def cleanup_temp_file(path: str):
    """Remove temporary file."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as e:
        logger.warning(f"Failed to cleanup temp file: {e}")


def ensure_directory(path: str):
    """Ensure directory exists."""
    Path(path).mkdir(parents=True, exist_ok=True)


def format_response(
    success: bool,
    data: dict = None,
    error: str = None,
    status_code: int = None
) -> Tuple[dict, int]:
    """
    Format API response.
    
    Args:
        success: Success status
        data: Response data
        error: Error message
        status_code: HTTP status code
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {"success": success}
    
    if data:
        response.update(data)
    
    if error:
        response["error"] = error
    
    if status_code is None:
        status_code = 200 if success else 400
    
    return response, status_code


def get_model_info(detector) -> dict:
    """
    Get model information.
    
    Args:
        detector: PPEDetector instance
    
    Returns:
        Model info dictionary
    """
    info = {
        "loaded": detector.is_loaded,
        "model_path": detector.model_path,
        "confidence_threshold": detector.confidence_threshold,
        "classes": detector.classes
    }
    
    if detector.model is not None:
        try:
            # Get model details if available
            info["model_type"] = type(detector.model).__name__
        except Exception:
            pass
    
    return info
