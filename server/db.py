"""
server/db.py

Shared PostgreSQL connection helper. Per-bay logging is gone - occupancy
is now logged as aggregate site-level snapshots via server/site_service.py,
and users/auth queries live in server/auth.py. This module just owns the
single shared connection both of those import.
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config

_connection = None


def _get_connection():
    global _connection
    if _connection is None:
        import psycopg2
        _connection = psycopg2.connect(config.DATABASE_URL)
    return _connection