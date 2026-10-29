"""
scripts/visualize_class_samples.py

Draws bounding boxes for a specific class ID onto a handful of sample
images, so you can visually confirm what an ambiguous class actually
represents before deciding how to remap it.

Usage:
    python scripts\visualize_class_samples.py --data data\annotated --class-id 0 --samples 5
"""

import argparse
import os
import random

import cv2
import yaml


def find_images_with_class(dataset_dir, split, class_id):
    data_yaml = os.path.join(dataset_dir, "data.yaml")
    with open(data_yaml) as f:
        config = yaml.safe_load(f)

    images_rel = config[split]
    labels_dir = os.path.join(dataset_dir, images_rel.replace("images", "labels"))
    images_dir = os.path.join(dataset_dir, images_rel)

    matches = []
    for filename in os.listdir(labels_dir):
        if not filename.endswith(".txt"):
            continue
        label_path = os.path.join(labels_dir, filename)
        with open(label_path) as f:
            lines = f.readlines()
        boxes = [l.strip().split() for l in lines if l.strip()]
        if any(int(b[0]) == class_id for b in boxes):
            image_name = filename.replace(".txt", ".jpg")
            image_path = os.path.join(images_dir, image_name)
            if os.path.exists(image_path):
                matches.append((image_path, boxes))
    return matches


def draw_and_save(image_path, boxes, class_id, out_dir):
    img = cv2.imread(image_path)
    h, w = img.shape[:2]

    for box in boxes:
        cid, cx, cy, bw, bh = int(box[0]), *map(float, box[1:5])
        x1 = int((cx - bw / 2) * w)
        y1 = int((cy - bh / 2) * h)
        x2 = int((cx + bw / 2) * w)
        y2 = int((cy + bh / 2) * h)
        color = (0, 0, 255) if cid == class_id else (200, 200, 200)
        thickness = 3 if cid == class_id else 1
        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        if cid == class_id:
            cv2.putText(img, str(cid), (x1, max(y1 - 5, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, os.path.basename(image_path))
    cv2.imwrite(out_path, img)
    return out_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/annotated")
    parser.add_argument("--class-id", type=int, required=True)
    parser.add_argument("--samples", type=int, default=5)
    parser.add_argument("--split", default="train", choices=["train", "val", "test"])
    args = parser.parse_args()

    matches = find_images_with_class(args.data, args.split, args.class_id)
    print(f"Found {len(matches)} images containing class {args.class_id}")

    sample = random.sample(matches, min(args.samples, len(matches)))
    out_dir = f"data/annotated/class_{args.class_id}_samples"

    for image_path, boxes in sample:
        saved = draw_and_save(image_path, boxes, args.class_id, out_dir)
        print(f"Saved: {saved}")

    print(f"\nOpen the images in {out_dir} - the class {args.class_id} boxes are drawn in thick red.")