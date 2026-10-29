$ErrorActionPreference = 'Stop'
Unregister-ScheduledTask -TaskName 'Immigration Source Monitor' -Confirm:$true
Write-Host 'Removed scheduler registration. Evidence and settings were retained.'
