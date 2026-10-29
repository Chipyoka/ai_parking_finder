"""
scripts/clean_dataset.py

Cleans a Roboflow-exported YOLO dataset:
- Drops bounding boxes belonging to junk/malformed classes
- Remaps the remaining classes to a clean, consecutive 0..N set
- Writes the cleaned dataset to a new folder + new data.yaml

Never modifies the original dataset folder - always writes to --output.

Usage:
    python scripts\clean_dataset.py --data data\annotated --output data\annotated_clean
"""

import argparse
import os
import shutil

import yaml

# Old class id -> new class name. Anything NOT listed here is dropped.
CLASS_REMAP = {
    2: "car",
    3: "space_empty",   # merged from "empty"
    4: "space_empty",   # merged from "free"
    5: "space_occupied",
}


def build_new_names():
    seen = []
    for name in CLASS_REMAP.values():
        if name not in seen:
            seen.append(name)
    return {i: name for i, name in enumerate(seen)}


def build_old_to_new_id(new_names):
    name_to_new_id = {name: i for i, name in new_names.items()}
    return {old_id: name_to_new_id[name] for old_id, name in CLASS_REMAP.items()}


def clean_split(dataset_dir, output_dir, split_rel_path, old_to_new_id):
    images_dir = os.path.join(dataset_dir, split_rel_path)
    labels_dir = os.path.join(dataset_dir, split_rel_path.replace("images", "labels"))
    if not os.path.isdir(labels_dir):
        print(f"Skipping missing split: {labels_dir}")
        return 0, 0

    out_images_dir = os.path.join(output_dir, split_rel_path)
    out_labels_dir = os.path.join(output_dir, split_rel_path.replace("images", "labels"))
    os.makedirs(out_images_dir, exist_ok=True)
    os.makedirs(out_labels_dir, exist_ok=True)

    kept_boxes = 0
    dropped_boxes = 0

    for filename in os.listdir(labels_dir):
        if not filename.endswith(".txt"):
            continue

        label_path = os.path.join(labels_dir, filename)
        with open(label_path) as f:
            lines = f.readlines()

        new_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            old_id = int(parts[0])
            if old_id not in old_to_new_id:
                dropped_boxes += 1
                continue
            new_id = old_to_new_id[old_id]
            new_lines.append(f"{new_id} {' '.join(parts[1:])}")
            kept_boxes += 1

        # Write label file even if empty (image with zero valid boxes is
        # still a valid "background" training example)
        with open(os.path.join(out_labels_dir, filename), "w") as f:
            f.write("\n".join(new_lines) + ("\n" if new_lines else ""))

        # Copy the matching image
        image_name = None
        for ext in (".jpg", ".jpeg", ".png"):
            candidate = filename.replace(".txt", ext)
            if os.path.exists(os.path.join(images_dir, candidate)):
                image_name = candidate
                break
        if image_name:
            shutil.copy(
                os.path.join(images_dir, image_name),
                os.path.join(out_images_dir, image_name),
            )

    return kept_boxes, dropped_boxes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/annotated")
    parser.add_argument("--output", default="data/annotated_clean")
    args = parser.parse_args()

    with open(os.path.join(args.data, "data.yaml")) as f:
        config = yaml.safe_load(f)

    new_names = build_new_names()
    old_to_new_id = build_old_to_new_id(new_names)

    print("Old class ID -> new class:")
    for old_id, new_id in old_to_new_id.items():
        print(f"  {old_id} -> {new_id} ({new_names[new_id]})")
    print(f"Dropping any class IDs not in {list(old_to_new_id.keys())}\n")

    total_kept, total_dropped = 0, 0
    for split_key in ["train", "val", "test"]:
        split_rel_path = config.get(split_key)
        if not split_rel_path:
            continue
        kept, dropped = clean_split(args.data, args.output, split_rel_path, old_to_new_id)
        print(f"{split_key}: kept {kept} boxes, dropped {dropped} boxes")
        total_kept += kept
        total_dropped += dropped

    new_yaml = {
        "path": "../datasets/roboflow_clean",
        "train": config.get("train"),
        "val": config.get("val"),
        "test": config.get("test"),
        "names": new_names,
    }
    with open(os.path.join(args.output, "data.yaml"), "w") as f:
        yaml.safe_dump(new_yaml, f, default_flow_style=False, sort_keys=False)

    print(f"\nTotal: kept {total_kept} boxes, dropped {total_dropped} boxes")
    print(f"Clean dataset written to: {args.output}")
    print(f"New data.yaml names: {new_names}")


if __name__ == "__main__":
    main()