#!/usr/bin/env python3
"""
Delete all users except 'cole' and 'natalie'.
Run this on Render shell to clean up any unauthorized accounts.

WARNING: This will permanently delete users and all their data!
"""

from database import get_session, User

ALLOWED_USERS = ['cole', 'natalie']

db_session = get_session()
try:
    all_users = db_session.query(User).all()

    print(f"Found {len(all_users)} user(s) in database")
    print("=" * 60)

    deleted_count = 0
    kept_count = 0

    for user in all_users:
        if user.username in ALLOWED_USERS:
            print(f"✓ KEEPING: {user.username} (ID: {user.id})")
            kept_count += 1
        else:
            print(f"✗ DELETING: {user.username} (ID: {user.id})")
            db_session.delete(user)
            deleted_count += 1

    if deleted_count > 0:
        db_session.commit()
        print("=" * 60)
        print(f"Deleted {deleted_count} unauthorized user(s)")
        print(f"Kept {kept_count} authorized user(s)")
    else:
        print("=" * 60)
        print("No unauthorized users found. Database is clean!")
        print(f"Total users: {kept_count}")

finally:
    db_session.close()
