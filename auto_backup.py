#!/usr/bin/env python3
"""
Automatic backup script that creates a backup before any deployment.
Run this manually or integrate it into your deployment process.
"""

import os
from datetime import datetime
from backup import export_backup

def create_auto_backup():
    """Create an automatic backup with timestamp."""
    try:
        # Create backups directory if it doesn't exist
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Create backup with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join(backup_dir, f'auto_backup_{timestamp}.json')

        export_backup(filename)
        print(f"\n✓ Automatic backup created: {filename}")

        # Keep only last 10 backups
        cleanup_old_backups(backup_dir)

    except Exception as e:
        print(f"✗ Backup failed: {e}")

def cleanup_old_backups(backup_dir, keep_count=10):
    """Keep only the most recent backups."""
    try:
        backups = [f for f in os.listdir(backup_dir) if f.startswith('auto_backup_')]
        backups.sort(reverse=True)

        # Delete old backups
        for old_backup in backups[keep_count:]:
            os.remove(os.path.join(backup_dir, old_backup))
            print(f"  Removed old backup: {old_backup}")
    except Exception as e:
        print(f"Warning: Could not cleanup old backups: {e}")

if __name__ == '__main__':
    create_auto_backup()
