"""
scripts/create_admin.py

Creates an admin user in the database. Run this once to bootstrap your
first login - there's no public signup for admin accounts by design.

Usage:
    python scripts\create_admin.py
"""

import os
import sys
import getpass

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.auth import get_user_by_username, create_user


def main():
    print("Create an admin user for the AI Parking Space Finder dashboard.\n")
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        return

    if get_user_by_username(username) is not None:
        print(f"A user named '{username}' already exists.")
        return

    password = getpass.getpass("Password: ")
    confirm = getpass.getpass("Confirm password: ")
    if password != confirm:
        print("Passwords do not match.")
        return
    if len(password) < 6:
        print("Password should be at least 6 characters.")
        return

    user_id = create_user(username, password, role="admin")
    print(f"\nAdmin user '{username}' created (id={user_id}). You can log in now.")


if __name__ == "__main__":
    main()