"""
PPE Detector - YOLOv8 Inference Wrapper
========================================
Wrapper class untuk menjalankan inferensi model YOLOv8
untuk deteksi APD (Alat Pelindung Diri).

Kelas yang dideteksi:
- 0: hardhat     (helm safety terdeteksi)
- 1: no_hardhat  (tidak memakai helm)
- 2: vest        (rompi keselamatan terdeteksi)
- 3: no_vest     (tidak memakai rompi)
- 4: boots       (sepatu safety terdeteksi)
- 5: no_boots    (tidak memakai sepatu safety)
"""

import os
import io
import base64
import logging
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger(__name__)


# Class definitions
CLASS_NAMES = {
    0: "hardhat",
    1: "no_hardhat",
    2: "vest",
    3: "no_vest",
    4: "boots",
    5: "no_boots"
}

# Violation classes (classes indicating PPE not worn)
VIOLATION_CLASSES = {"no_hardhat", "no_vest", "no_boots"}

# Human-readable labels (Indonesian)
CLASS_LABELS = {
    "hardhat": "Helm Safety Terdeteksi",
    "no_hardhat": "Tidak Memakai Helm",
    "vest": "Rompi Terdeteksi",
    "no_vest": "Tidak Memakai Rompi",
    "boots": "Sepatu Safety Terdeteksi",
    "no_boots": "Tidak Memakai Sepatu Safety"
}

# Colors for bounding boxes (BGR format for OpenCV)
CLASS_COLORS = {
    "hardhat": (0, 255, 0),      # Green
    "no_hardhat": (0, 0, 255),   # Red
    "vest": (0, 255, 0),         # Green
    "no_vest": (0, 0, 255),      # Red
    "boots": (0, 255, 0),        # Green
    "no_boots": (0, 0, 255),     # Red
}

# Alternative class name mappings from different model formats
CLASS_ALIASES = {
    "hardhat": ["hardhat", "helmet", "hard_hat", "hard-hat", "safety_helmet"],
    "no_hardhat": ["no_hardhat", "no_helmet", "no-hardhat", "head", "without_helmet"],
    "vest": ["vest", "safety_vest", "safety-vest", "hi_vis", "reflective_vest", "jacket"],
    "no_vest": ["no_vest", "no-vest", "no_safety_vest", "without_vest"],
    "boots": ["boots", "safety_boots", "safety-boots", "footwear", "safety_shoes", "work_boots"],
    "no_boots": ["no_boots", "no-boots", "no_safety_boots", "without_boots", "no_footwear"],
}


@dataclass
class Detection:
    """Single detection result."""
    class_id: int
    class_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]
    label: str
    is_violation: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "class_id": self.class_id,
            "class": self.class_name,
            "confidence": round(self.confidence, 3),
            "bbox": self.bbox,
            "label": self.label,
            "is_violation": self.is_violation
        }


class PPEDetector:
    """
    YOLOv8 wrapper for PPE detection.
    
    Example usage:
        detector = PPEDetector("models/ppe_model.pt")
        detections = detector.detect("image.jpg")
        annotated_img = detector.annotate("image.jpg", detections)
    """
    
    def __init__(
        self,
        model_path: str = "models/ppe_model.pt",
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        device: str = ""
    ):
        """
        Initialize PPE Detector.
        
        Args:
            model_path: Path to YOLOv8 .pt model file
            confidence_threshold: Minimum confidence for detections
            iou_threshold: IoU threshold for NMS
            device: Device to run on ('' for auto, 'cpu', '0' for GPU)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.device = device
        self.model = None
        self._class_map = None
        
        self._load_model()
    
    def _load_model(self):
        """Load YOLOv8 model."""
        try:
            from ultralytics import YOLO
            import torch
            
            # Patch torch.load for PyTorch 2.6+ compatibility
            original_load = torch.load
            def patched_load(*args, **kwargs):
                if 'weights_only' not in kwargs:
                    kwargs['weights_only'] = False
                return original_load(*args, **kwargs)
            torch.load = patched_load
            
            if os.path.exists(self.model_path):
                self.model = YOLO(self.model_path)
                logger.info(f"Model loaded: {self.model_path}")
                
                # Build class mapping
                self._build_class_map()
            else:
                # Use default YOLOv8n for demo
                logger.warning(f"Model not found: {self.model_path}")
                logger.warning("Using default YOLOv8n (limited detection)")
                self.model = YOLO("yolov8n.pt")
                self._class_map = {}
            
        except ImportError as e:
            logger.error(f"Failed to import ultralytics: {e}")
            logger.error("Install with: pip install ultralytics")
            self.model = None
    
    def _build_class_map(self):
        """Build mapping from model class names to standard class names."""
        if self.model is None:
            return
        
        self._class_map = {}
        model_names = self.model.names
        
        for model_id, model_name in model_names.items():
            model_name_lower = model_name.lower().strip()
            
            # Try to find matching standard class
            for std_name, aliases in CLASS_ALIASES.items():
                if model_name_lower in [a.lower() for a in aliases]:
                    self._class_map[model_id] = std_name
                    break
            else:
                # Direct match attempt
                if model_name_lower in CLASS_NAMES.values():
                    self._class_map[model_id] = model_name_lower
        
        logger.debug(f"Class mapping: {self._class_map}")
    
    def _normalize_class(self, model_class_id: int, model_class_name: str) -> Optional[str]:
        """
        Normalize model class to standard class name.
        
        Args:
            model_class_id: Class ID from model output
            model_class_name: Class name from model
        
        Returns:
            Standard class name or None if not recognized
        """
        # First try the pre-built map
        if self._class_map and model_class_id in self._class_map:
            return self._class_map[model_class_id]
        
        # Try direct name lookup
        name_lower = model_class_name.lower().strip()
        
        for std_name, aliases in CLASS_ALIASES.items():
            if name_lower in [a.lower() for a in aliases]:
                return std_name
        
        # Not a recognized class
        return None
    
    def detect(
        self,
        image: Union[str, np.ndarray, bytes],
        confidence: float = None,
        classes: List[str] = None
    ) -> List[Detection]:
        """
        Run detection on an image.
        
        Args:
            image: Image path, numpy array, or bytes
            confidence: Override confidence threshold
            classes: Filter to specific classes (e.g., ["no_hardhat", "no_vest"])
        
        Returns:
            List of Detection objects
        """
        if self.model is None:
            logger.warning("Model not loaded, returning empty results")
            return []
        
        conf = confidence or self.confidence_threshold
        
        # Handle bytes input
        if isinstance(image, bytes):
            import cv2
            nparr = np.frombuffer(image, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        try:
            results = self.model(
                image,
                conf=conf,
                iou=self.iou_threshold,
                device=self.device if self.device else None,
                verbose=False
            )
            
            detections = []
            
            for result in results:
                for box in result.boxes:
                    model_class_id = int(box.cls[0])
                    model_class_name = result.names[model_class_id]
                    confidence_score = float(box.conf[0])
                    bbox = [int(x) for x in box.xyxy[0].tolist()]
                    
                    # Normalize to standard class
                    std_class = self._normalize_class(model_class_id, model_class_name)
                    
                    if std_class is None:
                        continue
                    
                    # Filter by requested classes
                    if classes and std_class not in classes:
                        continue
                    
                    # Get standard class ID
                    std_class_id = list(CLASS_NAMES.values()).index(std_class)
                    
                    detection = Detection(
                        class_id=std_class_id,
                        class_name=std_class,
                        confidence=confidence_score,
                        bbox=bbox,
                        label=CLASS_LABELS.get(std_class, std_class),
                        is_violation=std_class in VIOLATION_CLASSES
                    )
                    detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Detection error: {e}")
            return []
    
    def detect_violations(
        self,
        image: Union[str, np.ndarray, bytes],
        confidence: float = None
    ) -> List[Detection]:
        """
        Detect only violations (no_hardhat, no_vest, no_boots).
        
        Args:
            image: Image input
            confidence: Confidence threshold
        
        Returns:
            List of violation detections only
        """
        return self.detect(
            image,
            confidence=confidence,
            classes=list(VIOLATION_CLASSES)
        )
    
    def annotate(
        self,
        image: Union[str, np.ndarray, bytes],
        detections: List[Detection],
        show_labels: bool = True,
        show_confidence: bool = True,
        line_thickness: int = 2,
        font_scale: float = 0.6
    ) -> np.ndarray:
        """
        Draw bounding boxes on image.
        
        Args:
            image: Image input
            detections: List of detections to draw
            show_labels: Show class labels
            show_confidence: Show confidence scores
            line_thickness: Bounding box line thickness
            font_scale: Label font scale
        
        Returns:
            Annotated image as numpy array
        """
        import cv2
        
        # Load image if path
        if isinstance(image, str):
            img = cv2.imread(image)
        elif isinstance(image, bytes):
            nparr = np.frombuffer(image, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            img = image.copy()
        
        if img is None:
            raise ValueError("Could not load image")
        
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            color = CLASS_COLORS.get(det.class_name, (255, 255, 0))
            
            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), color, line_thickness)
            
            if show_labels:
                # Build label text
                label_parts = [det.class_name]
                if show_confidence:
                    label_parts.append(f"{det.confidence:.2f}")
                label = " ".join(label_parts)
                
                # Calculate label position
                (label_w, label_h), baseline = cv2.getTextSize(
                    label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 1
                )
                
                # Draw label background
                cv2.rectangle(
                    img,
                    (x1, y1 - label_h - 10),
                    (x1 + label_w + 5, y1),
                    color,
                    -1
                )
                
                # Draw label text
                cv2.putText(
                    img,
                    label,
                    (x1 + 2, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    font_scale,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )
        
        return img
    
    def image_to_base64(
        self,
        image: np.ndarray,
        format: str = "jpeg",
        quality: int = 90
    ) -> str:
        """
        Convert numpy image to base64 string.
        
        Args:
            image: Numpy array image
            format: Output format (jpeg, png)
            quality: JPEG quality (1-100)
        
        Returns:
            Base64 encoded string with data URI prefix
        """
        import cv2
        
        if format.lower() == "jpeg":
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, quality]
            ext = "jpeg"
        else:
            encode_param = [cv2.IMWRITE_PNG_COMPRESSION, 6]
            ext = "png"
        
        _, buffer = cv2.imencode(f".{ext}", image, encode_param)
        b64_string = base64.b64encode(buffer).decode("utf-8")
        
        return f"data:image/{ext};base64,{b64_string}"
    
    def process(
        self,
        image: Union[str, np.ndarray, bytes],
        confidence: float = None,
        return_annotated: bool = True,
        annotated_format: str = "jpeg"
    ) -> Dict:
        """
        Complete processing pipeline: detect + annotate.
        
        Args:
            image: Image input
            confidence: Confidence threshold
            return_annotated: Include annotated image in response
            annotated_format: Format for annotated image (jpeg, png)
        
        Returns:
            Dictionary with detections and optional annotated image
        """
        # Run detection
        detections = self.detect(image, confidence=confidence)
        
        # Count violations
        violations = [d for d in detections if d.is_violation]
        
        result = {
            "success": True,
            "detections": [d.to_dict() for d in detections],
            "total_detections": len(detections),
            "violations_count": len(violations),
            "violations": [d.to_dict() for d in violations]
        }
        
        # Generate annotated image
        if return_annotated and detections:
            annotated = self.annotate(image, detections)
            result["annotated_image"] = self.image_to_base64(
                annotated, format=annotated_format
            )
        
        return result
    
    @property
    def classes(self) -> Dict[int, str]:
        """Get class definitions."""
        return CLASS_NAMES.copy()
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.model is not None


# Singleton instance for API use
_detector_instance: Optional[PPEDetector] = None


def get_detector(
    model_path: str = None,
    confidence: float = 0.5,
    force_reload: bool = False
) -> PPEDetector:
    """
    Get or create detector instance (singleton pattern).
    
    Args:
        model_path: Path to model (uses default if None)
        confidence: Confidence threshold
        force_reload: Force reload model
    
    Returns:
        PPEDetector instance
    """
    global _detector_instance
    
    if _detector_instance is None or force_reload:
        path = model_path or os.environ.get("PPE_MODEL_PATH", "models/ppe_model.pt")
        _detector_instance = PPEDetector(
            model_path=path,
            confidence_threshold=confidence
        )
    
    return _detector_instance
