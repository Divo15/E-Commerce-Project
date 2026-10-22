# Store data and backups

The database contains customer accounts, saved carts, sessions, products,
inventory, catalogue settings and any order drafts. Uploaded product, category
and campaign photos are stored separately under `media/`. Both must be preserved.

## Current local setup

The local storage configuration is in `.local/storage.json` (ignored by Git).
It points to directories outside the source checkout:

```text
D:\ShaliData\db.sqlite3
D:\ShaliData\media\
D:\ShaliBackups\shali-<UTC timestamp>-<unique ID>.zip
```

Restarting the website or updating its code does not remove these files. The
original `D:\Backend\db.sqlite3` and `D:\Backend\media` are left untouched as
the pre-move copies; the running store uses the new location after activation.
Do not switch back to the old database after customers have made newer changes.

Google credentials and the local Django signing key remain in `.local/` and are
not included in data backups. Keep credentials in the production host's secret
storage. Keep the production `DJANGO_SECRET_KEY` stable across releases so
existing browser sessions continue to work. Back up that key separately using
the host's private secret-management facilities.

## Take a backup

From the project directory:

```powershell
.\env\Scripts\python.exe -B manage.py backup_store
```

Backups use SQLite's online backup API, including committed WAL data, rather
than copying an open database file. Every uploaded file is included. SHA-256
checksums, database integrity, foreign keys and image references are verified
before a completed ZIP is published. Failed/incomplete snapshots are not
published as backups. If an upload changes or disappears during a snapshot,
the command fails; retry it. During a large catalogue import, finish the import
before backing up.

Archives contain private customer information. Store them in private storage,
never under `/media/`, `/static/` or a public download folder. No account data or
credentials are printed by these commands. Backups are not automatically deleted.
Choose and monitor a retention/storage policy when configuring live hosting.

## Automatic backups on this Windows computer

`scripts/install_backup_task.ps1` installs **Shali Store Backup** in Windows Task
Scheduler. It runs daily at 03:00 in the computer's local timezone and at user
sign-in. A new snapshot is skipped when a verified backup less than 20 hours
old already exists. The task catches missed schedules when possible, runs
without a visible console window, and does not require a stored password.

```powershell
powershell.exe -NoProfile -File .\scripts\install_backup_task.ps1
```

This is a local task: the computer must be on and its owner signed in. It does
not create an always-on hosting service. Check its Last Run Result in Task
Scheduler. The installer refuses to replace an existing task of the same name.
The first backup is made and verified during initial storage setup.

## Verify and recover

```powershell
.\env\Scripts\python.exe -B manage.py verify_store_backup D:\ShaliBackups\shali-<timestamp>-<id>.zip
.\env\Scripts\python.exe -B manage.py restore_store_backup D:\ShaliBackups\shali-<timestamp>-<id>.zip --destination D:\ShaliRecovered
```

The recovery destination must not exist. The command verifies the archive and
restored database, rejects unsafe ZIP paths, and never overwrites the current
store. Test the recovered store before switching to it. For a real recovery,
stop the server, set `DJANGO_DATA_DIR` to the recovered directory, run `migrate`
for the deployed code version if necessary, and restart. Keep the existing
signing key and Google credentials. Changes made after the snapshot are not
part of that snapshot.

## Deployment configuration

The live host has not been selected yet. It must provide a persistent mounted
disk for this SQLite setup. Do not put data on a disposable container filesystem.
Set these values in the host's environment, using its actual mount paths:

```text
DJANGO_DATA_DIR=/persistent/shali/data
DJANGO_BACKUP_DIR=/persistent/shali/backups
```

Production startup refuses to proceed without `DJANGO_DATA_DIR`. Data paths do
not depend on the code release directory. Copy the verified data and photos to
the mounted volume before the first launch; configure the web server to serve
`DJANGO_DATA_DIR/media` at `/media/` with debug disabled. Static frontend assets
are deployed separately with `collectstatic`.

This SQLite/disk implementation is for one application instance sharing that
disk. For multiple app instances, choose a managed database and shared object
storage; this backup command deliberately refuses non-SQLite databases.

Schedule `python manage.py backup_store --if-older-than-hours 20` daily on the
hosting server. Use the hosting provider's backup/scheduler service or cron:

```cron
0 3 * * * /path/to/venv/bin/python /path/to/app/manage.py backup_store --if-older-than-hours 20
```

The scheduler must receive the same environment/secrets as the website. Its
nonzero exit status must alert the operator through the host's monitoring.

A backup on the same disk cannot protect against losing that disk or computer.
Configure an independent, private backup destination before a real launch. An
optional `DJANGO_BACKUP_REPLICA_DIR` creates and verifies a second copy in a
mounted backup destination (for example a separately managed/synced backup
volume). A different folder on the same disk is still not an offsite copy.
Cloud storage, independent offsite copies, encryption at rest and the production
schedule must be configured with the selected provider; none are claimed to
exist just because the local scripts are installed.

## Moving an existing local store

The one-time migration takes a verified backup, restores into a new directory
and only then activates the local pointer. Stop the web server first so no new
cart/account changes can arrive during the cutover:

```powershell
.\env\Scripts\python.exe -B manage.py configure_store_storage --destination D:\ShaliData --backup-dir D:\ShaliBackups --activate-local
```

Existing destinations are never overwritten. On hosting, use environment
variables instead of `--activate-local`.
