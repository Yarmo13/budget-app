#!/usr/bin/env python3
"""Create the two allowed user accounts."""

from database import get_session, User

ACCOUNTS = {
    'cole': 'yarmoshuk',
    'natalie': 'pinto'
}

db_session = get_session()
try:
    for username, password in ACCOUNTS.items():
        # Check if user exists
        existing = db_session.query(User).filter_by(username=username).first()
        if existing:
            print(f"✓ User '{username}' already exists")
        else:
            # Create user
            user = User(username=username)
            user.set_password(password)
            db_session.add(user)
            db_session.commit()
            print(f"✓ Created user '{username}'")

    print(f"\nTotal users in database: {db_session.query(User).count()}")
finally:
    db_session.close()
