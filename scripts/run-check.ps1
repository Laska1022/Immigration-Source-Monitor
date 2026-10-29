$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw 'Run Setup.cmd first.' }
$monitorData = if ($env:ISM_DATA_DIR) { $env:ISM_DATA_DIR } else { Join-Path $env:LOCALAPPDATA 'ImmigrationSourceMonitor' }
$credentialFile = Join-Path $monitorData 'smtp-password.dpapi'
if (Test-Path -LiteralPath $credentialFile) {
    $secure = Get-Content -LiteralPath $credentialFile -Raw | ConvertTo-SecureString
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { $env:ISM_SMTP_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}
try {
    & $python -m immigration_monitor check
    $checkExit = $LASTEXITCODE
} finally { Remove-Item Env:\ISM_SMTP_PASSWORD -ErrorAction SilentlyContinue }
exit $checkExit
