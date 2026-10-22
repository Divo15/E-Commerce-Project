$ErrorActionPreference = 'Stop'
$backupProjectRoot = Split-Path -Parent $PSScriptRoot
$backupPython = Join-Path $backupProjectRoot 'env/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $backupPython)) {
    throw 'The project Python environment was not found.'
}
& $backupPython -B (Join-Path $backupProjectRoot 'manage.py') backup_store --if-older-than-hours 20
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
