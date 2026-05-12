"""
PPE Detection Model Training Script
====================================
Train YOLOv8 model untuk deteksi APD (Alat Pelindung Diri).

Kelas yang dideteksi:
- hardhat / no_hardhat  (helm safety)
- vest / no_vest        (rompi keselamatan)
- boots / no_boots      (sepatu safety)

Usage:
    python train.py --data datasets/merged/data.yaml --epochs 100
    python train.py --data datasets/merged/data.yaml --model yolov8s.pt --epochs 150
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
import yaml
import shutil

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_dataset(data_yaml: str) -> bool:
    """Validate dataset structure and contents."""
    data_path = Path(data_yaml)
    
    if not data_path.exists():
        print(f"✗ Dataset config not found: {data_yaml}")
        return False
    
    with open(data_path, 'r') as f:
        config = yaml.safe_load(f)
    
    base_path = data_path.parent
    if 'path' in config:
        base_path = Path(config['path'])
    
    # Check train/val directories
    train_path = base_path / config.get('train', 'images/train')
    val_path = base_path / config.get('val', 'images/val')
    
    issues = []
    
    if not train_path.exists():
        issues.append(f"Train images not found: {train_path}")
    else:
        train_count = len(list(train_path.glob("*.*")))
        print(f"  ✓ Train images: {train_count}")
    
    if not val_path.exists():
        issues.append(f"Val images not found: {val_path}")
    else:
        val_count = len(list(val_path.glob("*.*")))
        print(f"  ✓ Val images: {val_count}")
    
    # Check classes
    nc = config.get('nc', 0)
    names = config.get('names', [])
    print(f"  ✓ Classes: {nc} - {names}")
    
    if issues:
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    
    return True


def train_model(
    data_yaml: str,
    model: str = "yolov8n.pt",
    epochs: int = 100,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "",
    project: str = "runs/train",
    name: str = None,
    patience: int = 20,
    save_period: int = 10,
    resume: bool = False,
    pretrained: bool = True,
    optimizer: str = "auto",
    lr0: float = 0.01,
    augment: bool = True,
    cache: bool = False,
    workers: int = 8,
    verbose: bool = True
):
    """
    Train YOLOv8 model for PPE detection.
    
    Args:
        data_yaml: Path to dataset YAML config
        model: Base model (yolov8n.pt, yolov8s.pt, yolov8m.pt, etc.)
        epochs: Number of training epochs
        imgsz: Input image size
        batch: Batch size (-1 for auto)
        device: CUDA device ('' for auto, 'cpu' for CPU)
        project: Project directory for saving results
        name: Experiment name
        patience: Early stopping patience (epochs)
        save_period: Save checkpoint every N epochs
        resume: Resume from last checkpoint
        pretrained: Use pretrained weights
        optimizer: Optimizer (SGD, Adam, AdamW, auto)
        lr0: Initial learning rate
        augment: Enable data augmentation
        cache: Cache images in RAM
        workers: Number of data loader workers
        verbose: Verbose output
    
    Returns:
        Trained model and results
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("✗ ultralytics not installed. Install with: pip install ultralytics")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("PPE DETECTION MODEL TRAINING")
    print("=" * 60)
    
    # Validate dataset
    print(f"\n📂 Dataset: {data_yaml}")
    if not validate_dataset(data_yaml):
        print("\n✗ Dataset validation failed!")
        sys.exit(1)
    
    # Generate experiment name
    if name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"ppe_{Path(model).stem}_{timestamp}"
    
    print(f"\n🔧 Configuration:")
    print(f"   Model: {model}")
    print(f"   Epochs: {epochs}")
    print(f"   Image Size: {imgsz}")
    print(f"   Batch Size: {batch}")
    print(f"   Device: {device or 'auto'}")
    print(f"   Experiment: {project}/{name}")
    
    # Load model
    print(f"\n📥 Loading base model: {model}")
    yolo = YOLO(model)
    
    # Configure augmentation
    augmentation_config = {}
    if augment:
        augmentation_config = {
            "hsv_h": 0.015,      # Hue augmentation
            "hsv_s": 0.7,        # Saturation augmentation
            "hsv_v": 0.4,        # Value augmentation
            "degrees": 10.0,     # Rotation (+/- deg)
            "translate": 0.1,   # Translation (+/- fraction)
            "scale": 0.5,       # Scale (+/- gain)
            "shear": 5.0,       # Shear (+/- deg)
            "flipud": 0.0,      # Flip up-down (probability)
            "fliplr": 0.5,      # Flip left-right (probability)
            "mosaic": 1.0,      # Mosaic augmentation
            "mixup": 0.1,       # Mixup augmentation
        }
    
    # Start training
    print(f"\n🚀 Starting training...")
    print("-" * 60)
    
    results = yolo.train(
        data=data_yaml,
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device if device else None,
        project=project,
        name=name,
        patience=patience,
        save_period=save_period,
        resume=resume,
        pretrained=pretrained,
        optimizer=optimizer,
        lr0=lr0,
        cache=cache,
        workers=workers,
        verbose=verbose,
        **augmentation_config
    )
    
    # Training complete
    print("\n" + "=" * 60)
    print("TRAINING COMPLETE")
    print("=" * 60)
    
    # Get best model path
    best_model = Path(project) / name / "weights" / "best.pt"
    last_model = Path(project) / name / "weights" / "last.pt"
    
    print(f"\n📁 Results saved to: {project}/{name}")
    print(f"   Best model: {best_model}")
    print(f"   Last model: {last_model}")
    
    # Print metrics if available
    if hasattr(results, 'results_dict'):
        print(f"\n📊 Final Metrics:")
        metrics = results.results_dict
        for key, value in metrics.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.4f}")
    
    return yolo, results


def export_model(
    model_path: str,
    format: str = "onnx",
    imgsz: int = 640,
    output_dir: str = None
):
    """
    Export trained model to different formats.
    
    Args:
        model_path: Path to trained .pt model
        format: Export format (onnx, torchscript, tflite, etc.)
        imgsz: Image size for export
        output_dir: Output directory (default: same as model)
    """
    from ultralytics import YOLO
    
    print(f"\n📤 Exporting model to {format.upper()} format...")
    
    model = YOLO(model_path)
    exported = model.export(format=format, imgsz=imgsz)
    
    print(f"   ✓ Exported: {exported}")
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_path = Path(exported)
        dest = output_path / exported_path.name
        shutil.copy2(exported_path, dest)
        print(f"   ✓ Copied to: {dest}")
    
    return exported


def evaluate_model(
    model_path: str,
    data_yaml: str,
    split: str = "val",
    imgsz: int = 640,
    batch: int = 16,
    device: str = ""
):
    """
    Evaluate model on validation/test set.
    
    Args:
        model_path: Path to trained model
        data_yaml: Dataset config
        split: Dataset split to evaluate (val, test)
        imgsz: Image size
        batch: Batch size
        device: CUDA device
    """
    from ultralytics import YOLO
    
    print(f"\n📊 Evaluating model on {split} set...")
    
    model = YOLO(model_path)
    results = model.val(
        data=data_yaml,
        split=split,
        imgsz=imgsz,
        batch=batch,
        device=device if device else None
    )
    
    print(f"\n📈 Evaluation Results:")
    print(f"   mAP50: {results.box.map50:.4f}")
    print(f"   mAP50-95: {results.box.map:.4f}")
    print(f"   Precision: {results.box.mp:.4f}")
    print(f"   Recall: {results.box.mr:.4f}")
    
    # Per-class metrics
    print(f"\n   Per-class AP50:")
    if hasattr(results.box, 'ap50') and results.names:
        for i, ap in enumerate(results.box.ap50):
            class_name = results.names.get(i, f"class_{i}")
            print(f"     {class_name}: {ap:.4f}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Train YOLOv8 model for PPE detection",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "--data",
        type=str,
        default="datasets/merged/data.yaml",
        help="Path to dataset YAML configuration"
    )
    
    # Model arguments
    parser.add_argument(
        "--model",
        type=str,
        default="yolov8n.pt",
        choices=["yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"],
        help="Base model to use"
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs"
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Input image size"
    )
    parser.add_argument(
        "--batch",
        type=int,
        default=16,
        help="Batch size (-1 for auto)"
    )
    
    # Training arguments
    parser.add_argument(
        "--device",
        type=str,
        default="",
        help="CUDA device (e.g., '0' or '0,1') or 'cpu'"
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=20,
        help="Early stopping patience (epochs without improvement)"
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        default="auto",
        choices=["SGD", "Adam", "AdamW", "auto"],
        help="Optimizer to use"
    )
    parser.add_argument(
        "--lr0",
        type=float,
        default=0.01,
        help="Initial learning rate"
    )
    
    # Output arguments
    parser.add_argument(
        "--project",
        type=str,
        default="runs/train",
        help="Project directory for saving results"
    )
    parser.add_argument(
        "--name",
        type=str,
        default=None,
        help="Experiment name (auto-generated if not provided)"
    )
    
    # Flags
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume training from last checkpoint"
    )
    parser.add_argument(
        "--no-augment",
        action="store_true",
        help="Disable data augmentation"
    )
    parser.add_argument(
        "--cache",
        action="store_true",
        help="Cache images in RAM for faster training"
    )
    parser.add_argument(
        "--export",
        type=str,
        nargs="*",
        choices=["onnx", "torchscript", "tflite", "coreml"],
        help="Export formats after training"
    )
    parser.add_argument(
        "--eval-only",
        action="store_true",
        help="Only run evaluation (requires --model to be trained model)"
    )
    
    args = parser.parse_args()
    
    # Evaluation only mode
    if args.eval_only:
        if not Path(args.model).exists():
            print(f"✗ Model not found for evaluation: {args.model}")
            sys.exit(1)
        evaluate_model(
            model_path=args.model,
            data_yaml=args.data,
            imgsz=args.imgsz,
            batch=args.batch,
            device=args.device
        )
        return
    
    # Train model
    model, results = train_model(
        data_yaml=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        patience=args.patience,
        optimizer=args.optimizer,
        lr0=args.lr0,
        augment=not args.no_augment,
        cache=args.cache,
        resume=args.resume
    )
    
    # Export if requested
    if args.export:
        best_model = Path(args.project) / (args.name or "exp") / "weights" / "best.pt"
        
        # Find actual best model path
        if not best_model.exists():
            # List recent experiments
            exp_dirs = sorted(Path(args.project).glob("*"), key=os.path.getmtime, reverse=True)
            for exp_dir in exp_dirs:
                candidate = exp_dir / "weights" / "best.pt"
                if candidate.exists():
                    best_model = candidate
                    break
        
        if best_model.exists():
            for fmt in args.export:
                export_model(str(best_model), format=fmt, imgsz=args.imgsz)
        else:
            print(f"⚠ Best model not found for export")
    
    print("\n✅ Training pipeline complete!")


if __name__ == "__main__":
    main()
