"""
server/stream_worker.py

Runs one background detection loop per active site, instead of a single
hardcoded video source. Each site's video_source (webcam index, file path,
or RTSP URL - same values config.VIDEO_SOURCE used to hold) is read
independently, run through the shared ParkingDetector, and the aggregate
free/occupied counts are broadcast over WebSocket tagged with that site's id.

Since sites are managed live through the admin dashboard (add/edit/delete
while the server is running), this module exposes refresh_workers() to
start new site workers and stop removed/deactivated ones without needing
a server restart.
"""

import os
import sys
import time
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config
from detection.detector import ParkingDetector
from server import site_service

# One shared detector instance - the model itself doesn't depend on the
# site, only the video source does.
_detector = None

# site_id -> {"thread": Thread, "stop_event": Event}
_workers = {}
_workers_lock = threading.Lock()

_socketio = None  # set once in start_all()


def _get_detector():
    global _detector
    if _detector is None:
        _detector = ParkingDetector()
    return _detector


def _open_video_source(video_source):
    try:
        import cv2
    except ImportError:
        print("[stream_worker] OpenCV not installed - running in mock-only mode "
              "(install the full requirements.txt to enable real video capture).")
        return None

    source = video_source
    if isinstance(source, str) and source.isdigit():
        source = int(source)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[stream_worker] Could not open video source '{source}'. "
              f"Falling back to mock-only updates for this site.")
        return None
    return cap


def _site_loop(site_id, video_source, stop_event):
    """Runs until stop_event is set. One of these runs per active site,
    in its own thread, so a stuck/slow camera on one site never blocks
    another site's updates."""
    detector = _get_detector()
    cap = _open_video_source(video_source)

    while not stop_event.is_set():
        frame = None
        if cap is not None:
            ok, frame = cap.read()
            if not ok:
                frame = None

        detections = detector.process_frame(frame)
        free_count = sum(1 for d in detections if not d["occupied"])
        occupied_count = sum(1 for d in detections if d["occupied"])

        if _socketio is not None:
            _socketio.emit("site_update", {
                "site_id": site_id,
                "free_count": free_count,
                "occupied_count": occupied_count,
            })

        site_service.log_snapshot(site_id, free_count, occupied_count)

        stop_event.wait(config.FRAME_SAMPLE_RATE_SECONDS)

    if cap is not None:
        cap.release()
    print(f"[stream_worker] Stopped worker for site {site_id}")


def _start_worker(site):
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_site_loop,
        args=(site["id"], site["video_source"], stop_event),
        daemon=True,
    )
    _workers[site["id"]] = {"thread": thread, "stop_event": stop_event}
    thread.start()
    print(f"[stream_worker] Started worker for site {site['id']} ({site['name']})")


def _stop_worker(site_id):
    worker = _workers.pop(site_id, None)
    if worker is not None:
        worker["stop_event"].set()


def refresh_workers():
    """Reconciles running workers against the current active site list.
    Call this after any admin add/edit/delete of a site. Safe to call
    repeatedly - only starts/stops what actually changed."""
    with _workers_lock:
        active_sites = {s["id"]: s for s in site_service.list_sites(active_only=True)}

        # Stop workers for sites that were deleted or deactivated
        for site_id in list(_workers.keys()):
            if site_id not in active_sites:
                _stop_worker(site_id)

        # Start workers for newly added/activated sites
        for site_id, site in active_sites.items():
            if site_id not in _workers:
                _start_worker(site)


def start_all(socketio):
    """Call once at server startup. Starts a worker for every currently
    active site, and stores the socketio instance for emitting updates."""
    global _socketio
    _socketio = socketio
    refresh_workers()