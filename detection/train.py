"""
detection/train.py

One-off YOLOv8 fine-tuning script (Sprint 1). Run this locally or on
Google Colab once bay-annotated training images are exported from Roboflow
into data/annotated_clean/. Not part of the running server - just produces
detection/model/best.pt.

Usage:
    python detection/train.py
"""

from ultralytics import YOLO


def main():
    model = YOLO("yolov8n.pt")  # start from the small pretrained checkpoint
    model.train(
        data="data/annotated_clean/data.yaml",
        epochs=50,
        imgsz=640,
        project="detection/runs",
        name="parking_bays",
    )
    print("Training complete. Copy the best.pt weights to detection/model/best.pt")


if __name__ == "__main__":
    main()