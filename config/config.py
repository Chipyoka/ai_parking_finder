"""
Central configuration for the AI Parking Space Finder.

Video sources used to be a single global setting here. They're now
per-site, stored in the `sites` table and managed through the admin
dashboard (server/site_service.py) - so this file only holds things that
are genuinely global: the model, the database, and server settings.
"""

import os

# --- Detection ----------------------------------------------------------
MODEL_PATH = os.environ.get("MODEL_PATH", "detection/model/best.pt")
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.25))
FRAME_SAMPLE_RATE_SECONDS = float(os.environ.get("FRAME_SAMPLE_RATE_SECONDS", 1.0))

# --- Server ---------------------------------------------------------------
FLASK_HOST = os.environ.get("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.environ.get("FLASK_PORT", 5000))
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me_djfs236-_-dbb12")

# --- Database ---------------------------------------------------------------
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://test:test%40123@localhost:5432/parking_db",
)