#!/usr/bin/env python3
"""Check and clean up users in the database."""

from database import get_session, User

ALLOWED_USERS = ['cole', 'natalie']

db_session = get_session()
try:
    all_users = db_session.query(User).all()

    print(f"Found {len(all_users)} user(s) in database:")
    print("-" * 50)

    for user in all_users:
        print(f"ID: {user.id}, Username: {user.username}, Created: {user.created_at}")

        if user.username not in ALLOWED_USERS:
            print(f"  ⚠️  WARNING: User '{user.username}' is not in allowed list!")
            response = input(f"  Delete user '{user.username}'? (yes/no): ")
            if response.lower() == 'yes':
                db_session.delete(user)
                db_session.commit()
                print(f"  ✓ Deleted user '{user.username}'")
            else:
                print(f"  Skipped deletion")
        else:
            print(f"  ✓ Allowed user")

    print("-" * 50)
    remaining = db_session.query(User).count()
    print(f"\nTotal users remaining: {remaining}")

finally:
    db_session.close()
