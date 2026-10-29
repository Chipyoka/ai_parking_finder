# Pilot site deployment notes (Lusaka)

For whoever goes on-site once the Raspberry Pi is available. This should be
a same-day setup - nothing here requires the rest of the team present.

## Before you go
- [ ] `detection/model/best.pt` exists and is committed to the shared drive
      (trained back at school, not on-site)
- [ ] You know the CCTV camera's RTSP URL (ask the car park operator/technician).
      Typically looks like `rtsp://<camera-ip>:554/stream1`
- [ ] Raspberry Pi has Raspberry Pi OS (64-bit) installed, Python 3.10+, and
      internet access (for WebSocket connection back to the hosted Flask server
      if not running the server on the Pi itself)

## Steps
1. `git clone <repo-url>` onto the Pi
2. `cd ai-parking-finder`
3. `python3 -m venv venv && source venv/bin/activate`
4. `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and set:
   ```
   VIDEO_SOURCE=rtsp://<camera-ip>:554/stream1
   ```
6. Confirm the camera stream opens: `python -c "import cv2; print(cv2.VideoCapture('rtsp://<camera-ip>:554/stream1').isOpened())"`
   should print `True`
7. Run `python server/app.py`
8. From a laptop on the same network, visit `http://<pi-ip>:5000` to confirm
   bay updates are coming through

## If the RTSP stream can't be reached directly
Some CCTV systems only expose their stream through an NVR (network video
recorder) web interface rather than a raw RTSP URL. If so, ask the site
technician for the NVR's RTSP path format (usually documented per-brand,
e.g. Hikvision/Dahua) rather than trying to guess it.

## Fallback
If the RTSP feed isn't accessible on the day, a USB webcam pointed at the
bays works as an interim substitute - just set `VIDEO_SOURCE=0`. This keeps
the pilot demonstration possible even if network/camera access is delayed.
