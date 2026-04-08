"""
Prepare PPE Dataset for Training
=================================
Converts and merges downloaded datasets into YOLO format.

Datasets:
1. hard_hat_detection (Kaggle) - XML format
   - helmet → hardhat (class 0)
   - head → no_hardhat (class 1)

2. construction_safety (Kaggle) - YOLO format
   - 0:Hardhat → hardhat (class 0)
   - 2:NO-Hardhat → no_hardhat (class 1)
   - 7:Safety Vest → vest (class 2)
   - 4:NO-Safety Vest → no_vest (class 3)

Output Classes (4):
0: hardhat
1: no_hardhat
2: vest
3: no_vest
"""

import os
import shutil
import random
import xml.etree.ElementTree as ET
from pathlib import Path
from tqdm import tqdm
import yaml

# Output class mapping
OUTPUT_CLASSES = {
    0: "hardhat",
    1: "no_hardhat",
    2: "vest",
    3: "no_vest",
    4: "boots",
    5: "no_boots"
}

# Construction Safety dataset class remapping
CSS_REMAP = {
    0: 0,  # Hardhat → hardhat
    2: 1,  # NO-Hardhat → no_hardhat
    7: 2,  # Safety Vest → vest
    4: 3,  # NO-Safety Vest → no_vest
    # Skip: 1(Mask), 3(NO-Mask), 5(Person), 6(Safety Cone), 8(machinery), 9(vehicle)
}

# Sepatu Safety dataset class remapping
SEPATU_REMAP = {
    0: 0,  # helm → hardhat
    3: 2,  # rompi → vest
    5: 4,  # sepatu → boots
    # Skip: 1(kacamata), 2(masker), 4(sarungtangan)
}

# Hard Hat Detection XML class mapping
HARDHAT_REMAP = {
    "helmet": 0,   # → hardhat
    "head": 1,     # → no_hardhat (exposed head without helmet)
}


def convert_xml_to_yolo(xml_path: Path, img_width: int = None, img_height: int = None) -> list:
    """Convert Pascal VOC XML annotation to YOLO format."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Get image dimensions
    size = root.find('size')
    if size is not None:
        img_width = int(size.find('width').text)
        img_height = int(size.find('height').text)
    
    if not img_width or not img_height:
        return []
    
    annotations = []
    for obj in root.findall('object'):
        name = obj.find('name').text.lower()
        if name not in HARDHAT_REMAP:
            continue
        
        class_id = HARDHAT_REMAP[name]
        bbox = obj.find('bndbox')
        xmin = float(bbox.find('xmin').text)
        ymin = float(bbox.find('ymin').text)
        xmax = float(bbox.find('xmax').text)
        ymax = float(bbox.find('ymax').text)
        
        # Convert to YOLO format (center_x, center_y, width, height) normalized
        x_center = (xmin + xmax) / 2 / img_width
        y_center = (ymin + ymax) / 2 / img_height
        width = (xmax - xmin) / img_width
        height = (ymax - ymin) / img_height
        
        annotations.append(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")
    
    return annotations


def process_hardhat_dataset(src_dir: Path, output_dir: Path) -> int:
    """Process hard_hat_detection XML dataset."""
    images_dir = src_dir / "images"
    annotations_dir = src_dir / "annotations"
    
    if not images_dir.exists() or not annotations_dir.exists():
        print(f"  ✗ Source not found: {src_dir}")
        return 0
    
    count = 0
    xml_files = list(annotations_dir.glob("*.xml"))
    
    for xml_file in tqdm(xml_files, desc="  Processing"):
        # Find corresponding image
        img_name = xml_file.stem
        img_path = None
        for ext in ['.png', '.jpg', '.jpeg']:
            candidate = images_dir / f"{img_name}{ext}"
            if candidate.exists():
                img_path = candidate
                break
        
        if not img_path:
            continue
        
        # Convert XML to YOLO
        annotations = convert_xml_to_yolo(xml_file)
        if not annotations:
            continue
        
        # Determine split (80% train, 20% val)
        split = "train" if random.random() < 0.8 else "val"
        
        # Copy image
        out_img_dir = output_dir / split / "images"
        out_img_dir.mkdir(parents=True, exist_ok=True)
        out_img_path = out_img_dir / f"hh_{img_name}{img_path.suffix}"
        shutil.copy2(img_path, out_img_path)
        
        # Write label
        out_lbl_dir = output_dir / split / "labels"
        out_lbl_dir.mkdir(parents=True, exist_ok=True)
        out_lbl_path = out_lbl_dir / f"hh_{img_name}.txt"
        with open(out_lbl_path, 'w') as f:
            f.write('\n'.join(annotations))
        
        count += 1
    
    return count


def remap_yolo_label(label_path: Path, class_remap: dict) -> list:
    """Remap class IDs in YOLO label file."""
    annotations = []
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue
            
            class_id = int(parts[0])
            if class_id not in class_remap:
                continue  # Skip unmapped classes
            
            new_class_id = class_remap[class_id]
            annotations.append(f"{new_class_id} {' '.join(parts[1:])}")
    
    return annotations


def process_construction_safety(src_dir: Path, output_dir: Path) -> int:
    """Process construction safety YOLO dataset."""
    css_data = src_dir / "css-data"
    if not css_data.exists():
        print(f"  ✗ Source not found: {css_data}")
        return 0
    
    count = 0
    
    for split_name in ["train", "valid", "test"]:
        src_split = css_data / split_name
        if not src_split.exists():
            continue
        
        images_dir = src_split / "images"
        labels_dir = src_split / "labels"
        
        if not images_dir.exists() or not labels_dir.exists():
            continue
        
        # Map valid/test to val for our output
        out_split = "val" if split_name in ["valid", "test"] else "train"
        
        label_files = list(labels_dir.glob("*.txt"))
        for label_path in tqdm(label_files, desc=f"  Processing {split_name}"):
            # Remap classes
            annotations = remap_yolo_label(label_path, CSS_REMAP)
            if not annotations:
                continue  # Skip if no valid annotations after filtering
            
            # Find image
            img_path = None
            for ext in ['.jpg', '.jpeg', '.png']:
                candidate = images_dir / f"{label_path.stem}{ext}"
                if candidate.exists():
                    img_path = candidate
                    break
            
            if not img_path:
                continue
            
            # Copy image
            out_img_dir = output_dir / out_split / "images"
            out_img_dir.mkdir(parents=True, exist_ok=True)
            out_img_path = out_img_dir / f"css_{label_path.stem}{img_path.suffix}"
            shutil.copy2(img_path, out_img_path)
            
            # Write label
            out_lbl_dir = output_dir / out_split / "labels"
            out_lbl_dir.mkdir(parents=True, exist_ok=True)
            out_lbl_path = out_lbl_dir / f"css_{label_path.stem}.txt"
            with open(out_lbl_path, 'w') as f:
                f.write('\n'.join(annotations))
            
            count += 1
    
    return count


def process_sepatu_safety(src_dir: Path, output_dir: Path) -> int:
    """Process sepatu safety YOLO dataset."""
    if not src_dir.exists():
        print(f"  ✗ Source not found: {src_dir}")
        return 0
    
    count = 0
    
    for split_name in ["train", "valid", "test"]:
        src_split = src_dir / split_name
        if not src_split.exists():
            continue
        
        images_dir = src_split / "images"
        labels_dir = src_split / "labels"
        
        if not images_dir.exists() or not labels_dir.exists():
            continue
        
        # Map valid/test to val for our output
        out_split = "val" if split_name in ["valid", "test"] else "train"
        
        label_files = list(labels_dir.glob("*.txt"))
        for label_path in tqdm(label_files, desc=f"  Processing {split_name}"):
            # Remap classes
            annotations = remap_yolo_label(label_path, SEPATU_REMAP)
            if not annotations:
                continue  # Skip if no valid annotations after filtering
            
            # Find image
            img_path = None
            for ext in ['.jpg', '.jpeg', '.png']:
                candidate = images_dir / f"{label_path.stem}{ext}"
                if candidate.exists():
                    img_path = candidate
                    break
            
            if not img_path:
                continue
            
            # Copy image
            out_img_dir = output_dir / out_split / "images"
            out_img_dir.mkdir(parents=True, exist_ok=True)
            out_img_path = out_img_dir / f"ss_{label_path.stem}{img_path.suffix}"
            shutil.copy2(img_path, out_img_path)
            
            # Write label
            out_lbl_dir = output_dir / out_split / "labels"
            out_lbl_dir.mkdir(parents=True, exist_ok=True)
            out_lbl_path = out_lbl_dir / f"ss_{label_path.stem}.txt"
            with open(out_lbl_path, 'w') as f:
                f.write('\n'.join(annotations))
            
            count += 1
    
    return count


def create_data_yaml(output_dir: Path):
    """Create data.yaml for YOLO training."""
    yaml_content = {
        'path': str(output_dir.absolute()),
        'train': 'train/images',
        'val': 'val/images',
        'nc': len(OUTPUT_CLASSES),
        'names': list(OUTPUT_CLASSES.values())
    }
    
    yaml_path = output_dir / 'data.yaml'
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    
    return yaml_path


def count_class_distribution(output_dir: Path) -> dict:
    """Count class distribution in dataset."""
    counts = {i: 0 for i in OUTPUT_CLASSES.keys()}
    
    for split in ['train', 'val']:
        labels_dir = output_dir / split / 'labels'
        if not labels_dir.exists():
            continue
        
        for label_file in labels_dir.glob('*.txt'):
            with open(label_file, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        class_id = int(parts[0])
                        if class_id in counts:
                            counts[class_id] += 1
    
    return counts


def main():
    base_dir = Path(__file__).parent.parent
    sources_dir = base_dir / "datasets" / "sources"
    output_dir = base_dir / "datasets" / "merged"
    
    # Clean output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)
    
    print("=" * 60)
    print("PREPARING PPE DETECTION DATASET")
    print("=" * 60)
    print(f"\nOutput classes: {list(OUTPUT_CLASSES.values())}")
    
    total = 0
    
    # Process hard_hat_detection
    print("\n[1/2] Processing hard_hat_detection (XML → YOLO)...")
    hardhat_dir = sources_dir / "hard_hat_detection"
    count = process_hardhat_dataset(hardhat_dir, output_dir)
    print(f"   Processed: {count} images")
    total += count
    
    # Process construction_safety
    print("\n[2/3] Processing construction_safety (YOLO remap)...")
    css_dir = sources_dir / "construction_safety"
    count = process_construction_safety(css_dir, output_dir)
    print(f"  ✓ Processed: {count} images")
    total += count
    
    # Process sepatu_safety
    print("\n[3/3] Processing sepatu_safety (YOLO remap)...")
    ss_dir = sources_dir / "sepatu_safety"
    count = process_sepatu_safety(ss_dir, output_dir)
    print(f"  ✓ Processed: {count} images")
    total += count
    
    # Create data.yaml
    yaml_path = create_data_yaml(output_dir)
    
    # Count class distribution
    class_counts = count_class_distribution(output_dir)
    
    # Summary
    print("\n" + "=" * 60)
    print("DATASET READY")
    print("=" * 60)
    
    train_imgs = len(list((output_dir / "train" / "images").glob("*")))
    val_imgs = len(list((output_dir / "val" / "images").glob("*")))
    
    print(f"\n Total Images: {train_imgs + val_imgs}")
    print(f"   - Train: {train_imgs}")
    print(f"   - Val: {val_imgs}")
    
    print(f"\n Class Distribution:")
    total_annot = sum(class_counts.values())
    for class_id, count in class_counts.items():
        name = OUTPUT_CLASSES[class_id]
        pct = count / total_annot * 100 if total_annot > 0 else 0
        print(f"   {name:12s}: {count:6d} ({pct:5.1f}%)")
    
    print(f"\n Output: {output_dir}")
    print(f"   Data config: {yaml_path}")
    print(f"\n Ready for training!")
    print(f"   Run: python training/train.py --data {yaml_path}")


if __name__ == "__main__":
    main()
