"""
tests/verify_environment.py

Run this once after setup to confirm the whole stack is working:
Python version, Flask/SocketIO, OpenCV, Ultralytics (YOLOv8), and the
PostgreSQL connection - all in one command.

Usage:
    python tests\verify_environment.py
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RESULTS = []


def check(label, fn):
    try:
        detail = fn()
        RESULTS.append((label, True, detail or "OK"))
    except Exception as e:
        RESULTS.append((label, False, str(e)))


def check_python_version():
    v = sys.version_info
    if v.major == 3 and v.minor in (11, 12):
        return f"Python {v.major}.{v.minor}.{v.micro}"
    raise RuntimeError(
        f"Python {v.major}.{v.minor}.{v.micro} - expected 3.11 or 3.12 "
        f"(3.13 lacks wheels for some packages used here)"
    )


def check_flask():
    import flask
    import flask_socketio
    return f"flask {flask.__version__}, flask-socketio installed"


def check_opencv():
    import cv2
    return f"opencv {cv2.__version__}"


def check_ultralytics():
    from ultralytics import YOLO
    import ultralytics
    return f"ultralytics {ultralytics.__version__}"


def check_postgres():
    import psycopg2
    from config import config
    conn = psycopg2.connect(config.DATABASE_URL, connect_timeout=3)
    with conn.cursor() as cur:
        cur.execute("SELECT 1;")
        cur.fetchone()
    conn.close()
    return "connected to " + config.DATABASE_URL.split("@")[-1]


def check_schema():
    import psycopg2
    from config import config
    conn = psycopg2.connect(config.DATABASE_URL, connect_timeout=3)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name IN ('bays','occupancy_events');
        """)
        found = {row[0] for row in cur.fetchall()}
    conn.close()
    missing = {"bays", "occupancy_events"} - found
    if missing:
        raise RuntimeError(f"missing tables: {missing} - run database\\schema.sql")
    return "bays + occupancy_events tables present"


def main():
    check("Python version", check_python_version)
    check("Flask + Flask-SocketIO", check_flask)
    check("OpenCV", check_opencv)
    check("Ultralytics (YOLOv8)", check_ultralytics)
    check("PostgreSQL connection", check_postgres)
    check("Database schema", check_schema)

    print("\n--- Environment check results ---")
    all_ok = True
    for label, ok, detail in RESULTS:
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"[{status}] {label:<28} {detail}")

    print()
    if all_ok:
        print("Everything is set up. You're ready to build.")
    else:
        print("Some checks failed - see messages above. Fix those before continuing.")
        sys.exit(1)


if __name__ == "__main__":
    main()