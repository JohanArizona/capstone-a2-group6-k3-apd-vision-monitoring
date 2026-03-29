"""
Dataset Merger for PPE Detection
=================================
Script untuk mendownload dan memproses dataset PPE dari Roboflow.

Dataset Source:
- klema-ai/ppe-yolo-jrblc
- URL: https://universe.roboflow.com/klema-ai/ppe-yolo-jrblc

Classes (6 yang digunakan dari 11):
- hardhat (helmet)
- no_hardhat (no-helmet)
- vest
- no_vest (no-vest)
- boots
- no_boots (no-boots)

Classes yang di-skip: goggles, no-goggles, gloves, no-gloves, person

Output: Dataset dalam format YOLO
"""

import os
import shutil
import random
import yaml
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm

# Standard class mapping for our PPE detection model
# Full version: 6 classes with boots (using klema-ai/ppe-yolo-jrblc dataset)
STANDARD_CLASSES = {
    0: "hardhat",
    1: "no_hardhat", 
    2: "vest",
    3: "no_vest",
    4: "boots",
    5: "no_boots"
}

# Mapping from source dataset classes to our standard classes
# Each source may have different naming conventions
CLASS_MAPPINGS = {
    "hard_hat_workers": {
        "helmet": 0,      # hardhat
        "head": 1,        # no_hardhat
        "hardhat": 0,
        "no-hardhat": 1,
        "no_hardhat": 1,
        "person": None,   # skip person class
    },
    "construction_safety": {
        "Hardhat": 0,
        "NO-Hardhat": 1,
        "Safety Vest": 2,
        "NO-Safety Vest": 3,
        "vest": 2,
        "no_vest": 3,
        "no-vest": 3,
    },
    "ppe_detection": {
        "helmet": 0,
        "no_helmet": 1,
        "vest": 2,
        "no_vest": 3,
        "boots": 4,
        "no_boots": 5,
        "footwear": 4,
        "no_footwear": 5,
        "safety_boots": 4,
    },
    # Dataset: https://universe.roboflow.com/klema-ai/ppe-yolo-jrblc
    "ppe_yolo_klema": {
        "helmet": 0,
        "no-helmet": 1,
        "vest": 2,
        "no-vest": 3,
        "boots": 4,
        "no-boots": 5,
        # Skip classes not needed
        "goggles": None,
        "no-goggles": None,
        "gloves": None,
        "no-gloves": None,
        "person": None,
        "safety-boots": 4,
        "Boots": 4,
        "NO-Boots": 5,
    },
    "ppe_v2": {
        "hardhat": 0,
        "no-hardhat": 1,
        "vest": 2,
        "no-vest": 3,
        "boots": 4,
        "no-boots": 5,
    }
}


def download_roboflow_dataset(
    workspace: str,
    project: str,
    version: int,
    api_key: str,
    output_dir: str,
    format: str = "yolov8"
) -> str:
    """
    Download dataset dari Roboflow menggunakan Roboflow API.
    
    Args:
        workspace: Roboflow workspace name
        project: Project name
        version: Dataset version
        api_key: Roboflow API key
        output_dir: Output directory
        format: Export format (yolov8, yolov5, etc)
    
    Returns:
        Path to downloaded dataset
    """
    try:
        from roboflow import Roboflow
        
        rf = Roboflow(api_key=api_key)
        project = rf.workspace(workspace).project(project)
        dataset = project.version(version).download(format, location=output_dir)
        
        print(f"✓ Downloaded: {workspace}/{project} v{version}")
        return output_dir
        
    except ImportError:
        print("⚠ Roboflow not installed. Install with: pip install roboflow")
        return None
    except Exception as e:
        print(f"✗ Error downloading {workspace}/{project}: {e}")
        return None


def download_kaggle_dataset(
    dataset_slug: str,
    output_dir: str
) -> str:
    """
    Download dataset dari Kaggle.
    
    Args:
        dataset_slug: Kaggle dataset slug (e.g., "username/dataset-name")
        output_dir: Output directory
    
    Returns:
        Path to downloaded dataset
    """
    try:
        import kaggle
        
        os.makedirs(output_dir, exist_ok=True)
        kaggle.api.dataset_download_files(dataset_slug, path=output_dir, unzip=True)
        
        print(f"✓ Downloaded from Kaggle: {dataset_slug}")
        return output_dir
        
    except ImportError:
        print("⚠ Kaggle not installed. Install with: pip install kaggle")
        print("  Also configure ~/.kaggle/kaggle.json with your API key")
        return None
    except Exception as e:
        print(f"✗ Error downloading {dataset_slug}: {e}")
        return None


def remap_labels(
    label_file: Path,
    source_classes: Dict[str, int],
    class_mapping: Dict,
    output_file: Path
) -> int:
    """
    Remap class IDs dalam file label YOLO ke standard format.
    
    Args:
        label_file: Path to source label file
        source_classes: Original class names from source dataset {id: name}
        class_mapping: Mapping from source names to target IDs
        output_file: Path to output label file
    
    Returns:
        Number of annotations processed
    """
    annotations = []
    
    with open(label_file, 'r') as f:
        lines = f.readlines()
    
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 5:
            continue
            
        original_class_id = int(parts[0])
        
        # Get original class name
        original_class_name = source_classes.get(original_class_id, str(original_class_id))
        
        # Map to new class ID
        new_class_id = class_mapping.get(original_class_name)
        
        # Also try lowercase
        if new_class_id is None:
            new_class_id = class_mapping.get(original_class_name.lower())
        
        # Skip if class should be ignored (mapped to None)
        if new_class_id is None:
            continue
        
        # Keep bbox coordinates
        bbox = parts[1:5]
        annotations.append(f"{new_class_id} {' '.join(bbox)}")
    
    # Write remapped labels
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        f.write('\n'.join(annotations))
    
    return len(annotations)


def parse_data_yaml(yaml_path: Path) -> Tuple[Dict[int, str], str, str]:
    """
    Parse data.yaml dari dataset YOLO.
    
    Returns:
        Tuple of (class_names_dict, train_path, val_path)
    """
    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)
    
    # Class names can be list or dict
    names = data.get('names', [])
    if isinstance(names, list):
        class_names = {i: name for i, name in enumerate(names)}
    else:
        class_names = names
    
    train_path = data.get('train', 'images/train')
    val_path = data.get('val', 'images/val')
    
    return class_names, train_path, val_path


def merge_datasets(
    source_dirs: List[Tuple[str, str]],  # [(path, mapping_key), ...]
    output_dir: str,
    train_ratio: float = 0.8
) -> Dict:
    """
    Merge multiple YOLO datasets into one.
    
    Args:
        source_dirs: List of (dataset_path, mapping_key) tuples
        output_dir: Output directory for merged dataset
        train_ratio: Ratio of training data (default 0.8)
    
    Returns:
        Statistics dictionary
    """
    output_path = Path(output_dir)
    
    # Create output structure
    (output_path / "images" / "train").mkdir(parents=True, exist_ok=True)
    (output_path / "images" / "val").mkdir(parents=True, exist_ok=True)
    (output_path / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (output_path / "labels" / "val").mkdir(parents=True, exist_ok=True)
    
    stats = {
        "total_images": 0,
        "train_images": 0,
        "val_images": 0,
        "class_counts": {name: 0 for name in STANDARD_CLASSES.values()},
        "source_stats": {}
    }
    
    all_image_label_pairs = []
    
    for source_dir, mapping_key in source_dirs:
        source_path = Path(source_dir)
        source_name = source_path.name
        
        print(f"\n📂 Processing: {source_name}")
        
        if not source_path.exists():
            print(f"  ⚠ Directory not found: {source_path}")
            continue
        
        # Find data.yaml
        yaml_files = list(source_path.glob("**/data.yaml")) + list(source_path.glob("**/*.yaml"))
        if not yaml_files:
            print(f"  ⚠ No data.yaml found in {source_path}")
            continue
        
        yaml_file = yaml_files[0]
        source_classes, train_rel, val_rel = parse_data_yaml(yaml_file)
        
        print(f"  Classes found: {list(source_classes.values())}")
        
        class_mapping = CLASS_MAPPINGS.get(mapping_key, CLASS_MAPPINGS.get("ppe_detection"))
        
        source_stats = {"images": 0, "annotations": 0}
        
        # Process both train and val directories from source
        for split_rel in [train_rel, val_rel]:
            # Find images directory
            images_dir = source_path / split_rel
            if not images_dir.exists():
                # Try alternative paths
                for alt in ["images/train", "images/val", "train/images", "val/images"]:
                    alt_path = source_path / alt
                    if alt_path.exists():
                        images_dir = alt_path
                        break
            
            if not images_dir.exists():
                continue
            
            # Find corresponding labels directory
            labels_dir = Path(str(images_dir).replace("images", "labels"))
            
            # Process each image
            for img_ext in ["*.jpg", "*.jpeg", "*.png", "*.JPG", "*.JPEG", "*.PNG"]:
                for img_file in images_dir.glob(img_ext):
                    # Find corresponding label
                    label_file = labels_dir / f"{img_file.stem}.txt"
                    
                    if label_file.exists():
                        all_image_label_pairs.append({
                            "image": img_file,
                            "label": label_file,
                            "source_classes": source_classes,
                            "class_mapping": class_mapping,
                            "source": source_name
                        })
                        source_stats["images"] += 1
        
        stats["source_stats"][source_name] = source_stats
        print(f"  Found {source_stats['images']} images with labels")
    
    # Shuffle and split
    random.shuffle(all_image_label_pairs)
    
    split_idx = int(len(all_image_label_pairs) * train_ratio)
    train_pairs = all_image_label_pairs[:split_idx]
    val_pairs = all_image_label_pairs[split_idx:]
    
    print(f"\n📊 Splitting: {len(train_pairs)} train / {len(val_pairs)} val")
    
    # Copy and remap
    img_counter = 0
    
    for split_name, pairs in [("train", train_pairs), ("val", val_pairs)]:
        print(f"\n📝 Processing {split_name} set...")
        
        for pair in tqdm(pairs, desc=f"  {split_name}"):
            img_counter += 1
            new_filename = f"img_{img_counter:06d}"
            
            # Get extension from original
            ext = pair["image"].suffix
            
            # Copy image
            new_img_path = output_path / "images" / split_name / f"{new_filename}{ext}"
            shutil.copy2(pair["image"], new_img_path)
            
            # Remap and copy label
            new_label_path = output_path / "labels" / split_name / f"{new_filename}.txt"
            num_annotations = remap_labels(
                pair["label"],
                pair["source_classes"],
                pair["class_mapping"],
                new_label_path
            )
            
            # Update class counts
            if new_label_path.exists():
                with open(new_label_path, 'r') as f:
                    for line in f:
                        class_id = int(line.split()[0])
                        class_name = STANDARD_CLASSES.get(class_id)
                        if class_name:
                            stats["class_counts"][class_name] += 1
    
    stats["total_images"] = img_counter
    stats["train_images"] = len(train_pairs)
    stats["val_images"] = len(val_pairs)
    
    # Create merged data.yaml
    merged_yaml = {
        "path": str(output_path.absolute()),
        "train": "images/train",
        "val": "images/val",
        "nc": len(STANDARD_CLASSES),
        "names": list(STANDARD_CLASSES.values())
    }
    
    with open(output_path / "data.yaml", 'w') as f:
        yaml.dump(merged_yaml, f, default_flow_style=False)
    
    return stats


def download_all_datasets(api_key: str, output_base: str) -> List[Tuple[str, str]]:
    """
    Download PPE detection datasets from Kaggle.
    
    Datasets:
    1. andrewmvd/hard-hat-detection - Hardhat detection
    2. snehilsanyal/construction-site-safety-image-dataset-roboflow - Full PPE
    
    Args:
        api_key: Not used for Kaggle (uses ~/.kaggle/kaggle.json)
        output_base: Base output directory
    
    Returns:
        List of (dataset_path, mapping_key) tuples
    """
    datasets = []
    output_base = Path(output_base)
    output_base.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("DOWNLOADING PPE DETECTION DATASETS FROM KAGGLE")
    print("=" * 60)
    print("\nDatasets to download:")
    print("  1. andrewmvd/hard-hat-detection")
    print("  2. snehilsanyal/construction-site-safety-image-dataset-roboflow")
    print("\nClasses to extract:")
    print("  ✓ hardhat/helmet, no_hardhat/head")
    print("  ✓ vest, no_vest")
    print("  ✓ boots (if available)")
    
    # Dataset 1: Hard Hat Detection
    print("\n[1/2] Hard Hat Detection (andrewmvd)...")
    hardhat_path = output_base / "hard_hat_detection"
    if not hardhat_path.exists():
        downloaded = download_kaggle_dataset(
            dataset_slug="andrewmvd/hard-hat-detection",
            output_dir=str(hardhat_path)
        )
        if downloaded:
            datasets.append((str(hardhat_path), "hard_hat_workers"))
            print(f"  ✓ Downloaded to: {hardhat_path}")
    else:
        print(f"  ✓ Already exists: {hardhat_path}")
        datasets.append((str(hardhat_path), "hard_hat_workers"))
    
    # Dataset 2: Construction Site Safety (has vest, hardhat, boots)
    print("\n[2/2] Construction Site Safety (snehilsanyal)...")
    construction_path = output_base / "construction_safety"
    if not construction_path.exists():
        downloaded = download_kaggle_dataset(
            dataset_slug="snehilsanyal/construction-site-safety-image-dataset-roboflow",
            output_dir=str(construction_path)
        )
        if downloaded:
            datasets.append((str(construction_path), "ppe_detection"))
            print(f"  ✓ Downloaded to: {construction_path}")
    else:
        print(f"  ✓ Already exists: {construction_path}")
        datasets.append((str(construction_path), "ppe_detection"))
    
    return datasets


def print_stats(stats: Dict):
    """Print merge statistics."""
    print("\n" + "=" * 60)
    print("MERGE STATISTICS")
    print("=" * 60)
    
    print(f"\n📊 Total Images: {stats['total_images']}")
    print(f"   - Train: {stats['train_images']} ({stats['train_images']/stats['total_images']*100:.1f}%)")
    print(f"   - Val: {stats['val_images']} ({stats['val_images']/stats['total_images']*100:.1f}%)")
    
    print(f"\n📋 Class Distribution:")
    total_annotations = sum(stats['class_counts'].values())
    for class_name, count in stats['class_counts'].items():
        pct = count / total_annotations * 100 if total_annotations > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"   {class_name:12s}: {count:6d} ({pct:5.1f}%) {bar}")
    
    print(f"\n📁 Source Datasets:")
    for source, source_stats in stats['source_stats'].items():
        print(f"   - {source}: {source_stats['images']} images")


def main():
    parser = argparse.ArgumentParser(description="Download and merge PPE detection datasets")
    parser.add_argument(
        "--api-key",
        type=str,
        help="Roboflow API key (or set ROBOFLOW_API_KEY env variable)"
    )
    parser.add_argument(
        "--download-dir",
        type=str,
        default="./datasets/sources",
        help="Directory to download source datasets"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./datasets/merged",
        help="Output directory for merged dataset"
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Ratio of training data (default: 0.8)"
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download, only merge existing datasets"
    )
    parser.add_argument(
        "--sources",
        nargs="+",
        help="Manual source directories (path:mapping_key format)"
    )
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or os.environ.get("ROBOFLOW_API_KEY")
    
    if args.sources:
        # Manual source specification
        datasets = []
        for source in args.sources:
            if ":" in source:
                path, mapping = source.split(":", 1)
            else:
                path = source
                mapping = "ppe_detection"
            datasets.append((path, mapping))
    elif args.skip_download:
        # Use existing downloads
        download_dir = Path(args.download_dir)
        datasets = [
            (str(download_dir / "hard_hat_workers"), "hard_hat_workers"),
            (str(download_dir / "construction_safety"), "construction_safety"),
            (str(download_dir / "ppe_detection"), "ppe_detection"),
            (str(download_dir / "ppe_v2"), "ppe_v2"),
        ]
    else:
        # Download all using Kaggle (no API key needed, uses ~/.kaggle/kaggle.json)
        datasets = download_all_datasets(api_key, args.download_dir)
    
    if not datasets:
        print("No datasets to merge!")
        return
    
    print("\n" + "=" * 60)
    print("MERGING DATASETS")
    print("=" * 60)
    
    stats = merge_datasets(
        source_dirs=datasets,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio
    )
    
    print_stats(stats)
    
    print(f"\n✅ Merged dataset saved to: {args.output_dir}")
    print(f"   Use this in training: --data {args.output_dir}/data.yaml")


if __name__ == "__main__":
    main()
