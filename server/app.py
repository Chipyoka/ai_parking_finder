"""
server/app.py

Entry point for the AI Parking Space Finder backend.

Run it with:
    python server/app.py

Serves:
    /            - public map (webmap/index.html)
    /admin       - admin dashboard (webmap/admin.html) - login required for
                   its API calls, but the page itself loads for anyone;
                   the page's own JS gates what's shown based on /api/session
    /hello       - plain-text sanity check
    /api/health  - JSON health check
    /api/*       - see server/routes.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, send_from_directory
from flask_socketio import SocketIO

from config import config
from server.routes import bp as api_bp
from server import stream_worker

WEBMAP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "webmap")

app = Flask(__name__, static_folder=WEBMAP_DIR, static_url_path="")
app.config["SECRET_KEY"] = config.SECRET_KEY
app.register_blueprint(api_bp)

socketio = SocketIO(app, cors_allowed_origins="*")


@app.route("/")
def index():
    return send_from_directory(WEBMAP_DIR, "index.html")


@app.route("/admin")
def admin_page():
    return send_from_directory(WEBMAP_DIR, "admin.html")


@app.route("/hello")
def hello():
    """Plain-text sanity check - no static files, no dependencies.
    If this doesn't work, the problem is Flask/venv setup, not the project."""
    return "Hello, World! The AI Parking Space Finder server is running."


@app.route("/api/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Hello from the AI Parking Space Finder server!",
    })


@socketio.on("connect")
def handle_connect():
    print("[server] Client connected")


if __name__ == "__main__":
    stream_worker.start_all(socketio)
    print(f"[server] Starting on http://{config.FLASK_HOST}:{config.FLASK_PORT}")
    socketio.run(
        app,
        host=config.FLASK_HOST,
        port=config.FLASK_PORT,
        debug=True,
        use_reloader=False,
        allow_unsafe_werkzeug=True,  # fine for local/dev use; production would run behind eventlet/gunicorn
    )