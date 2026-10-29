# Current user only; runs after sign-in under the same DPAPI identity.
$ErrorActionPreference='Stop'
$startupFolder=[Environment]::GetFolderPath('Startup')
$linkPath=Join-Path $startupFolder 'Selvarithik Gateway.lnk'
$shell=New-Object -ComObject WScript.Shell
$link=$shell.CreateShortcut($linkPath)
if((Test-Path -LiteralPath $linkPath) -and $link.Description -ne 'Selvarithik Gateway managed local startup'){throw 'Existing unrelated startup shortcut preserved.'}
$link.TargetPath=(Get-Command powershell.exe).Source
$link.Arguments='-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "'+(Join-Path $PSScriptRoot 'Start-Gateway.ps1')+'" -NoBrowser'
$link.WorkingDirectory=Split-Path -Parent $PSScriptRoot
$link.WindowStyle=7
$link.Description='Selvarithik Gateway managed local startup'
$link.Save()
Write-Output 'Current-user Gateway startup installed. It will run after your next Windows sign-in.'
