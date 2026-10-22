$ErrorActionPreference = 'Stop'
$backupScript = Join-Path $PSScriptRoot 'backup_store.ps1'
$backupAccount = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$backupAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -WindowStyle Hidden -File "{0}"' -f $backupScript)
$backupTriggers = @(
    (New-ScheduledTaskTrigger -Daily -At '03:00'),
    (New-ScheduledTaskTrigger -AtLogOn -User $backupAccount)
)
$backupPrincipal = New-ScheduledTaskPrincipal -UserId $backupAccount -LogonType Interactive -RunLevel Limited
$backupSettings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$backupTask = New-ScheduledTask -Action $backupAction -Trigger $backupTriggers -Principal $backupPrincipal -Settings $backupSettings -Description 'Verified Shali database and uploaded-photo backups. Runs locally while the owner is signed in; production scheduling belongs on the hosting server.'
$existingBackupTask = Get-ScheduledTask -TaskName 'Shali Store Backup' -ErrorAction SilentlyContinue
if ($existingBackupTask) { throw 'Shali Store Backup already exists; it was left unchanged.' }
Register-ScheduledTask -TaskName 'Shali Store Backup' -InputObject $backupTask | Select-Object TaskName, State
