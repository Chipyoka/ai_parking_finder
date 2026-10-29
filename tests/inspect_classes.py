"""
scripts/inspect_classes.py

Counts how many bounding boxes exist per class across the dataset splits,
so you can decide how to clean up a messy data.yaml before training.

Usage:
    python scripts\inspect_classes.py --data data\annotated
"""

import argparse
import os
from collections import Counter

import yaml


def count_classes(dataset_dir):
    yaml_path = os.path.join(dataset_dir, "data.yaml")
    with open(yaml_path) as f:
        data_config = yaml.safe_load(f)

    names = data_config["names"]
    counts = Counter()
    image_counts = Counter()

    for split_key in ["train", "val", "test"]:
        split_rel_path = data_config.get(split_key)
        if not split_rel_path:
            continue
        # labels live in the same structure as images, just "labels" instead of "images"
        labels_dir = os.path.join(dataset_dir, split_rel_path.replace("images", "labels"))
        if not os.path.isdir(labels_dir):
            print(f"Skipping missing folder: {labels_dir}")
            continue

        for filename in os.listdir(labels_dir):
            if not filename.endswith(".txt"):
                continue
            path = os.path.join(labels_dir, filename)
            seen_classes_in_file = set()
            with open(path) as label_file:
                for line in label_file:
                    parts = line.strip().split()
                    if not parts:
                        continue
                    class_id = int(parts[0])
                    counts[class_id] += 1
                    seen_classes_in_file.add(class_id)
            for class_id in seen_classes_in_file:
                image_counts[class_id] += 1

    print(f"\n{'Class ID':<10}{'Name':<15}{'Box count':<12}{'Images containing it':<22}")
    for class_id in sorted(names.keys()):
        name = names[class_id]
        print(f"{class_id:<10}{name:<15}{counts.get(class_id, 0):<12}{image_counts.get(class_id, 0):<22}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/annotated", help="Path to the dataset folder containing data.yaml")
    args = parser.parse_args()
    count_classes(args.data)