# Explicit opt-in. Does not run during setup or UI startup.
$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'run-check.ps1'
$projectRoot = Split-Path -Parent $PSScriptRoot
$taskName = 'Immigration Source Monitor'
if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    throw 'Task already exists. Review it or run remove-scheduler.ps1 before installing again.'
}
if ($env:ISM_DATA_DIR) {
    Write-Host 'Custom ISM_DATA_DIR must be configured as a persistent user environment variable for the scheduled process.'
}
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -NonInteractive -File "{0}"' -f $runner) -WorkingDirectory $projectRoot
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 15)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description 'Checks due official sources and prepares opt-in digests. Requires a running connected host and logged-in user.' | Out-Null
Write-Host 'Installed. Runs every 15 minutes while this user is logged in. Source checks default to six hours. Sleeping/offline machines cannot perform ordinary checks.'
