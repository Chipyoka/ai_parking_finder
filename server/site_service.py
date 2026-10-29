"""
server/site_service.py

CRUD operations for registered sites, plus reading/writing aggregate
occupancy snapshots. This is the one place that knows about the `sites`
and `occupancy_snapshots` tables - routes.py and stream_worker.py both
go through here rather than writing SQL themselves.
"""

import os
import sys
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.db import _get_connection


def _row_to_site(row):
    return {
        "id": row[0],
        "name": row[1],
        "video_source": row[2],
        "latitude": row[3],
        "longitude": row[4],
        "is_active": row[5],
        "created_at": row[6].isoformat() if row[6] else None,
    }


def list_sites(active_only: bool = False):
    conn = _get_connection()
    query = "SELECT id, name, video_source, latitude, longitude, is_active, created_at FROM sites"
    if active_only:
        query += " WHERE is_active = TRUE"
    query += " ORDER BY id"
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return [_row_to_site(r) for r in rows]


def get_site(site_id: int):
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            "SELECT id, name, video_source, latitude, longitude, is_active, created_at "
            "FROM sites WHERE id = %s",
            (site_id,),
        )
        row = cur.fetchone()
    return _row_to_site(row) if row else None


def create_site(name: str, video_source: str, latitude: float, longitude: float):
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sites (name, video_source, latitude, longitude, is_active)
            VALUES (%s, %s, %s, %s, TRUE)
            RETURNING id
            """,
            (name, video_source, latitude, longitude),
        )
        new_id = cur.fetchone()[0]
    conn.commit()
    return get_site(new_id)


def update_site(site_id: int, **fields):
    """Updates only the fields provided, e.g. update_site(3, name="New name")."""
    allowed = {"name", "video_source", "latitude", "longitude", "is_active"}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return get_site(site_id)

    conn = _get_connection()
    set_clause = ", ".join(f"{col} = %s" for col in updates)
    values = list(updates.values()) + [site_id]
    with conn.cursor() as cur:
        cur.execute(f"UPDATE sites SET {set_clause} WHERE id = %s", values)
    conn.commit()
    return get_site(site_id)


def delete_site(site_id: int):
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM sites WHERE id = %s", (site_id,))
    conn.commit()


def log_snapshot(site_id: int, free_count: int, occupied_count: int):
    conn = _get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO occupancy_snapshots (site_id, free_count, occupied_count, event_time)
                VALUES (%s, %s, %s, %s)
                """,
                (site_id, free_count, occupied_count, datetime.datetime.utcnow()),
            )
        conn.commit()
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        print(f"[site_service] Skipped logging snapshot for site {site_id}: {e}")


def get_latest_snapshot(site_id: int):
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT free_count, occupied_count, event_time
            FROM occupancy_snapshots
            WHERE site_id = %s
            ORDER BY event_time DESC
            LIMIT 1
            """,
            (site_id,),
        )
        row = cur.fetchone()
    if row is None:
        return None
    return {"free_count": row[0], "occupied_count": row[1], "event_time": row[2].isoformat()}


def get_snapshot_history(site_id: int, limit: int = 50):
    conn = _get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT free_count, occupied_count, event_time
            FROM occupancy_snapshots
            WHERE site_id = %s
            ORDER BY event_time DESC
            LIMIT %s
            """,
            (site_id, limit),
        )
        rows = cur.fetchall()
    return [
        {"free_count": r[0], "occupied_count": r[1], "event_time": r[2].isoformat()}
        for r in reversed(rows)
    ]