#!/usr/bin/env python3
"""Simple script to list all users - run this on Render."""

from database import get_session, User

db_session = get_session()
try:
    users = db_session.query(User).all()
    print(f"Total users: {len(users)}")
    for user in users:
        print(f"  - {user.username} (ID: {user.id}, Created: {user.created_at})")
finally:
    db_session.close()
