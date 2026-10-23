# Continue Shali Collections on a new device

Updated **23 October 2026 (Asia/Calcutta)**. Read [HANDOFF.md](HANDOFF.md) for full context and [RAILWAY_DEPLOYMENT.md](RAILWAY_DEPLOYMENT.md) for live operations. This replaces the October 20 guide: code is pushed, the original store is migrated, and there is no WIP patch waiting to be rescued.

## What remains on the cloud

The site runs on Railway without the old computer/ngrok. Production accounts, catalogue and carts are in Postgres; uploaded images are on the app volume at /data/media. Code and notes are on GitHub **testing**. Admin: https://e-commerce-project-production-6748.up.railway.app/admin/ until the final www domain is ready.

Git does not contain customer data, uploaded media, private backups, passwords, OAuth secrets, local mail or CLI authentication. A clone starts with code and an empty LOCAL database, not a download of production. Local admin edits do not sync to cloud admin.

## Before erasing the old device

1. Confirm GitHub/Railway/Google account access, 2FA and recovery methods on the new device.
2. Privately copy D:/ShaliData and D:/ShaliBackups if you want the old local development store/recovery snapshots. They can be stale relative to later cloud changes.
3. Privately preserve needed D:/Backend/.local files in encrypted storage/password management. This includes secrets and customer exports: never GitHub/public attachments.
4. Recreate the Python environment; copying env is not a portable install.
5. The old Windows Shali Store Backup task does not move with Git and never backed up Railway. Automatic cloud/offsite backups still need configuration.
6. Do not delete Railway services/volumes/signing key because you are changing computers. Cloud services already hold the live store and its secrets.

## Clone and install

Install Git, a Python version compatible with the pinned requirements (old local 3.12, inspected Railway 3.13), and Node.js for Railway CLI. Choose any local workspace; D:/Backend is not required on the new device.

```powershell
git clone --branch testing https://github.com/Divo15/E-Commerce-Project.git
cd E-Commerce-Project
git status --short
git branch --show-current
py -3.12 -m venv env
.\env\Scripts\python.exe -m pip install -r requirements.txt
```

Select another supported installed Python if 3.12 is unavailable. Use testing; main is older. Authenticate GitHub if repository access requires it.

## Safe LOCAL development

Do not paste production DATABASE_URL into the environment for ordinary tests; ORM writes would target the real cloud DB. The app does not automatically source .env.

```powershell
$env:DJANGO_DEBUG='true'
$env:DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost'
$env:DJANGO_DATA_DIR=Join-Path (Get-Location) '.local/dev-data'
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
Remove-Item Env:ACCOUNT_PUBLIC_ORIGIN -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $env:DJANGO_DATA_DIR -Force | Out-Null
.\env\Scripts\python.exe -B manage.py migrate
.\env\Scripts\python.exe -B manage.py check
.\env\Scripts\python.exe -B manage.py test --noinput
.\env\Scripts\python.exe -B manage.py runserver 127.0.0.1:8001
```

This creates an empty local SQLite DB and a local key under .local/secret_key; tests use an isolated test database. Local email writes to .local/emails, not inboxes. Gunicorn runs on Linux/Railway; use runserver on Windows.

Local site: http://127.0.0.1:8001/ and local admin: http://127.0.0.1:8001/admin/.

An empty local DB has no cloud admin user. To get a development catalogue, follow PERSISTENT_STORAGE.md and inspect verify_store_backup / restore_store_backup --help, restoring an authorized private SQLite backup into a NEW empty directory. Or create a separate local superuser for an empty development store. Never reset a production password to fix local login or restore SQLite over Postgres. Do not re-import old fixtures into a populated DB.

## Connect to existing Railway project

```powershell
npx.cmd --yes @railway/cli@5.71.0 login
npx.cmd --yes @railway/cli@5.71.0 link --project 890fe855-842e-4f3c-8e53-1d7dcdabf8ac --environment production --service E-Commerce-Project
npx.cmd --yes @railway/cli@5.71.0 domain status www.shalicollections.com --service E-Commerce-Project --json
```

Login uses Railway's own browser authentication. Do not paste a password/token into chat. Link the existing project, do not create another one.

Variable list JSON/KV output exposes raw secrets: keep private and report only selected public settings/presence booleans. Do not use railway run with production variables for routine tests. Read HANDOFF.md before any data-write command.

Create/register a new SSH key for this device, without overwriting an existing key. Direct service-domain SSH worked on the old device; CLI auto-selected UUID SSH once stalled. No public Postgres proxy is necessary. CLI login sessions and private keys are not in Git.

## Start a new chat

Ask the assistant to read HANDOFF.md, this file and RAILWAY_DEPLOYMENT.md before editing. Current work: client DNS, bare-domain forwarding, Google callbacks/canonical origin, backups and launch tests. The source store is ALREADY transferred and verified. Preserve its design/data; do not repeat initial migration.

Use git status and log first; commit/push authorized changes to testing. GitHub pushes can trigger Railway deployments, including documentation pushes. Correctly configured Postgres and the /data volume survive these deployments.
