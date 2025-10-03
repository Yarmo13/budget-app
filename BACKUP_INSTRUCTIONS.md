# Budget Tracker - Backup & Restore Guide

## Creating a Backup

To backup all your expense data, budgets, and settings:

```bash
cd /Users/coleyarmoshuk/Documents/budget-app
python backup.py export
```

This creates a file like `backup_20250103_143022.json` with the current date and time.

**Important:** Backups should be created regularly, especially:
- Before making major changes to budgets
- At the end of each month
- Before updating the application

## Restoring from a Backup

If you need to restore your data:

```bash
python backup.py import backup_20250103_143022.json
```

**Note:** User accounts must already exist (cole and natalie need to be signed up first). The restore will then add all the expenses, budgets, and settings to those accounts.

## Automatic Backup on Render

For the cloud deployment at cona.me, you can download the database file directly:

1. Go to your Render dashboard
2. Select your budget-tracker service
3. Go to Shell tab
4. Run: `python backup.py export`
5. Download the generated JSON file using the file browser

## Storage Recommendations

- Keep backups in multiple locations (local computer, cloud storage)
- Use a naming convention like: `budget_backup_YYYY-MM-DD.json`
- Store backups in a secure location (they contain your financial data)
- Keep at least 3 recent backups

## What's Included in Backups

✓ All expenses with dates, categories, and amounts
✓ All budget limits by category
✓ User settings
✗ Passwords (must be recreated manually for security)

## Example Backup Schedule

- **Weekly:** Every Sunday night
- **Monthly:** Last day of each month
- **Before updates:** Whenever you update the app
