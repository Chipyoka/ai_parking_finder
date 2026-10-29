"""
server/routes.py

Public routes (no login required):
    GET  /api/sites            - list active sites with latest occupancy counts (for the map)
    GET  /api/sites/<id>        - single site detail + latest snapshot
    GET  /api/sites/<id>/history - recent occupancy snapshot history (for charts)

Auth routes:
    POST /api/login
    POST /api/logout
    GET  /api/session           - check current login state

Admin-only routes (require role='admin'):
    POST   /api/admin/sites          - create a site
    PUT    /api/admin/sites/<id>     - update a site
    DELETE /api/admin/sites/<id>     - delete a site
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, jsonify, request
from server import stream_worker

from server import site_service
from server.auth import (
    verify_login,
    login_user_session,
    logout_user_session,
    current_user,
    admin_required,
)

bp = Blueprint("routes", __name__)


# --- Public: sites for the map -------------------------------------------

@bp.route("/api/sites", methods=["GET"])
def get_sites():
    sites = site_service.list_sites(active_only=True)
    for site in sites:
        snapshot = site_service.get_latest_snapshot(site["id"])
        site["latest"] = snapshot  # None if no data yet - map handles that as "no data"
    return jsonify(sites)


@bp.route("/api/sites/<int:site_id>", methods=["GET"])
def get_site_detail(site_id):
    site = site_service.get_site(site_id)
    if site is None:
        return jsonify({"error": "Site not found"}), 404
    site["latest"] = site_service.get_latest_snapshot(site_id)
    return jsonify(site)


@bp.route("/api/sites/<int:site_id>/history", methods=["GET"])
def get_site_history(site_id):
    if site_service.get_site(site_id) is None:
        return jsonify({"error": "Site not found"}), 404
    return jsonify(site_service.get_snapshot_history(site_id))


# --- Auth -----------------------------------------------------------------

@bp.route("/api/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    user = verify_login(username, password)
    if user is None:
        return jsonify({"error": "Invalid username or password"}), 401

    login_user_session(user)
    return jsonify({"username": user["username"], "role": user["role"]})


@bp.route("/api/logout", methods=["POST"])
def logout():
    logout_user_session()
    return jsonify({"status": "logged out"})


@bp.route("/api/session", methods=["GET"])
def session_info():
    user = current_user()
    if user is None:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": user["username"], "role": user["role"]})


# --- Admin: manage sites ----------------------------------------------------

@bp.route("/api/admin/sites", methods=["GET"])
@admin_required
def admin_list_sites():
    # Admins see inactive sites too, unlike the public endpoint
    return jsonify(site_service.list_sites(active_only=False))


@bp.route("/api/admin/sites", methods=["POST"])
@admin_required
def admin_create_site():
    data = request.get_json(force=True)
    try:
        name = data["name"].strip()
        video_source = data["video_source"].strip()
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except (KeyError, ValueError, AttributeError):
        return jsonify({"error": "name, video_source, latitude, longitude are required"}), 400

    if not name or not video_source:
        return jsonify({"error": "name and video_source cannot be empty"}), 400

    site = site_service.create_site(name, video_source, latitude, longitude)

    stream_worker.refresh_workers()

    return jsonify(site), 201


@bp.route("/api/admin/sites/<int:site_id>", methods=["PUT"])
@admin_required
def admin_update_site(site_id):
    if site_service.get_site(site_id) is None:
        return jsonify({"error": "Site not found"}), 404

    data = request.get_json(force=True)
    fields = {}
    if "name" in data:
        fields["name"] = data["name"].strip()
    if "video_source" in data:
        fields["video_source"] = data["video_source"].strip()
    if "latitude" in data:
        fields["latitude"] = float(data["latitude"])
    if "longitude" in data:
        fields["longitude"] = float(data["longitude"])
    if "is_active" in data:
        fields["is_active"] = bool(data["is_active"])

    site = site_service.update_site(site_id, **fields)

    stream_worker.refresh_workers()

    return jsonify(site)


@bp.route("/api/admin/sites/<int:site_id>", methods=["DELETE"])
@admin_required
def admin_delete_site(site_id):
    if site_service.get_site(site_id) is None:
        return jsonify({"error": "Site not found"}), 404
    site_service.delete_site(site_id)

    stream_worker.refresh_workers()
    
    return jsonify({"status": "deleted"})