#!/usr/bin/env python3
"""
Database backup and restore script for Budget Tracker
Usage:
    python backup.py export          # Create backup
    python backup.py import <file>   # Restore from backup
"""

import sys
import json
from datetime import datetime
from database import get_session, User, Expense, Budget, Settings

def export_backup(filename=None):
    """Export all data to JSON file."""
    if not filename:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'backup_{timestamp}.json'

    db_session = get_session()
    try:
        data = {
            'export_date': datetime.now().isoformat(),
            'users': [],
            'expenses': [],
            'budgets': [],
            'settings': []
        }

        # Export users (without password hashes for security)
        users = db_session.query(User).all()
        for user in users:
            data['users'].append({
                'id': user.id,
                'username': user.username,
                'created_at': user.created_at.isoformat() if user.created_at else None
            })

        # Export expenses
        expenses = db_session.query(Expense).all()
        for expense in expenses:
            data['expenses'].append({
                'id': expense.id,
                'user_id': expense.user_id,
                'date': expense.date.isoformat(),
                'category': expense.category,
                'amount': expense.amount,
                'description': expense.description
            })

        # Export budgets
        budgets = db_session.query(Budget).all()
        for budget in budgets:
            data['budgets'].append({
                'id': budget.id,
                'user_id': budget.user_id,
                'category': budget.category,
                'monthly_limit': budget.monthly_limit
            })

        # Export settings
        settings = db_session.query(Settings).all()
        for setting in settings:
            data['settings'].append({
                'id': setting.id,
                'user_id': setting.user_id,
                'key': setting.key,
                'value': setting.value
            })

        # Write to file
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Backup created successfully: {filename}")
        print(f"  Users: {len(data['users'])}")
        print(f"  Expenses: {len(data['expenses'])}")
        print(f"  Budgets: {len(data['budgets'])}")
        print(f"  Settings: {len(data['settings'])}")

        return filename

    finally:
        db_session.close()

def import_backup(filename):
    """Restore data from JSON backup file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"✗ Error: Backup file '{filename}' not found")
        return False
    except json.JSONDecodeError:
        print(f"✗ Error: Invalid JSON in backup file")
        return False

    db_session = get_session()
    try:
        print(f"Restoring from backup: {filename}")
        print(f"Backup date: {data.get('export_date', 'Unknown')}")

        # Note: Users must be recreated manually with passwords
        # This only restores expenses, budgets, and settings for existing users

        user_map = {}
        for user_data in data['users']:
            existing_user = db_session.query(User).filter_by(username=user_data['username']).first()
            if existing_user:
                user_map[user_data['id']] = existing_user.id
                print(f"  Found existing user: {user_data['username']}")
            else:
                print(f"  ⚠ Warning: User '{user_data['username']}' not found. Create account first.")

        # Restore expenses
        expense_count = 0
        for expense_data in data['expenses']:
            if expense_data['user_id'] in user_map:
                expense = Expense(
                    user_id=user_map[expense_data['user_id']],
                    date=datetime.fromisoformat(expense_data['date']).date(),
                    category=expense_data['category'],
                    amount=expense_data['amount'],
                    description=expense_data.get('description', '')
                )
                db_session.add(expense)
                expense_count += 1

        # Restore budgets
        budget_count = 0
        for budget_data in data['budgets']:
            if budget_data['user_id'] in user_map:
                budget = Budget(
                    user_id=user_map[budget_data['user_id']],
                    category=budget_data['category'],
                    monthly_limit=budget_data['monthly_limit']
                )
                db_session.add(budget)
                budget_count += 1

        # Restore settings
        setting_count = 0
        for setting_data in data['settings']:
            if setting_data['user_id'] in user_map:
                setting = Settings(
                    user_id=user_map[setting_data['user_id']],
                    key=setting_data['key'],
                    value=setting_data['value']
                )
                db_session.add(setting)
                setting_count += 1

        db_session.commit()

        print(f"✓ Restore completed successfully!")
        print(f"  Expenses restored: {expense_count}")
        print(f"  Budgets restored: {budget_count}")
        print(f"  Settings restored: {setting_count}")

        return True

    except Exception as e:
        db_session.rollback()
        print(f"✗ Error during restore: {str(e)}")
        return False

    finally:
        db_session.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup.py export              # Create backup")
        print("  python backup.py import <file>       # Restore from backup")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == 'export':
        export_backup()
    elif command == 'import':
        if len(sys.argv) < 3:
            print("Error: Please specify backup file to import")
            print("Usage: python backup.py import <backup_file.json>")
            sys.exit(1)
        import_backup(sys.argv[2])
    else:
        print(f"Unknown command: {command}")
        print("Use 'export' or 'import'")
        sys.exit(1)
