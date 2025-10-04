#!/usr/bin/env python3
"""
Initialize required accounts if they don't exist.
This runs automatically to ensure cole and natalie accounts always exist.
"""

from database import get_session, User

def ensure_accounts_exist():
    """Ensure the two required accounts exist in the database."""
    REQUIRED_ACCOUNTS = {
        'cole': 'yarmoshuk',
        'natalie': 'pinto'
    }

    db_session = get_session()
    try:
        for username, password in REQUIRED_ACCOUNTS.items():
            existing = db_session.query(User).filter_by(username=username).first()
            if not existing:
                user = User(username=username)
                user.set_password(password)
                db_session.add(user)
                db_session.commit()
                print(f"✓ Created required account: {username}")
            else:
                print(f"✓ Account exists: {username}")
    except Exception as e:
        print(f"Error ensuring accounts: {e}")
        db_session.rollback()
    finally:
        db_session.close()

if __name__ == '__main__':
    ensure_accounts_exist()
