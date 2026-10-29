$ErrorActionPreference = 'Stop'
$monitorData = if ($env:ISM_DATA_DIR) { $env:ISM_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'ImmigrationSourceMonitor' }
New-Item -ItemType Directory -Force -Path $monitorData | Out-Null
$password = Read-Host 'SMTP password or app password (stored with Windows user DPAPI; never logged)' -AsSecureString
$password | ConvertFrom-SecureString | Set-Content -LiteralPath (Join-Path $monitorData 'smtp-password.dpapi')
Write-Host 'Saved for this Windows user and machine. Configure SMTP and enable email in the application. Backups do not include this credential.'
