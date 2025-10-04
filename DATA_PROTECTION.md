# Data Protection Guide

## Your Data is Protected! 🛡️

Your budget app now has **multiple layers of protection** to ensure your account and data are never lost:

## 1. Automatic Account Creation ✅

**What happens:** Every time the app starts, it automatically ensures your accounts exist.

- Username `cole` with password `yarmoshuk`
- Username `natalie` with password `pinto`

**Location:** `/Users/coleyarmoshuk/Documents/budget-app/init_accounts.py`

**When it runs:** Automatically when you start the app (locally or on Render)

## 2. Production Database (cona.me) 🌐

**What happens:** On cona.me, your database is **persistent** and stored on Render's servers.

- Data **never** gets deleted unless you manually do it
- Survives app restarts and code deployments
- Independent from local development

**Important:** You only need to sign up ONCE on cona.me. After that, always use "Log in".

## 3. Manual Backups 💾

### Create a Backup

```bash
cd /Users/coleyarmoshuk/Documents/budget-app
python backup.py export
```

This creates a file like `backup_20250104_143022.json` with ALL your data.

### Restore from Backup

```bash
python backup.py import backup_20250104_143022.json
```

**Note:** Make sure your accounts exist first (sign up or run `python init_accounts.py`)

## 4. Automatic Backups 🤖

### Create Auto-Backup (stores in backups/ folder)

```bash
python auto_backup.py
```

This creates timestamped backups in the `backups/` folder and keeps the last 10.

**Recommended:** Run this before making major changes:
```bash
python auto_backup.py && git add . && git commit -m "your changes" && git push
```

## 5. Folder Backups 📁

Your entire project folder is backed up at:
```
/Users/coleyarmoshuk/Documents/budget-app-backup-20251004-123248
```

New timestamped backups are created whenever you ask for them.

## What Gets Backed Up? 📋

✅ User accounts (usernames only, not passwords - they're reset on restore)
✅ All expenses with dates, categories, amounts, descriptions
✅ All budget limits by category
✅ All savings entries
✅ All settings

## Best Practices 🎯

1. **On cona.me (production):**
   - Sign up ONCE with cole/yarmoshuk
   - Always use "Log in" after that
   - Your data persists forever

2. **For local development:**
   - Run `python init_accounts.py` if accounts get deleted
   - Or just sign up again with the exact credentials

3. **Before major changes:**
   - Run `python auto_backup.py` to create a backup
   - Or manually: `python backup.py export`

4. **Weekly backups (recommended):**
   - Every week, run: `python auto_backup.py`
   - Download the backup files and store them somewhere safe

## Emergency Data Recovery 🚨

If you ever lose data:

1. Find your most recent backup in `backups/` folder
2. Run: `python backup.py import backups/auto_backup_XXXXXXX.json`
3. Sign up with cole/yarmoshuk if needed
4. All your data will be restored!

## Summary 📝

**Your data is safe because:**
- ✅ Accounts automatically recreate on app startup
- ✅ Production database (cona.me) never gets wiped
- ✅ Easy manual backup/restore system
- ✅ Automatic backup system available
- ✅ Full project folder backups
- ✅ Multiple layers of protection

**You will never lose your data!** 🎉
