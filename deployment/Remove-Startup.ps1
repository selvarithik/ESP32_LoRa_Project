$ErrorActionPreference='Stop'
$startupFolder=[Environment]::GetFolderPath('Startup')
$linkPath=[IO.Path]::GetFullPath((Join-Path $startupFolder 'Selvarithik Gateway.lnk'))
if((Split-Path -Parent $linkPath) -ne [IO.Path]::GetFullPath($startupFolder)){throw 'Unexpected startup path.'}
if(Test-Path -LiteralPath $linkPath){$shell=New-Object -ComObject WScript.Shell;$link=$shell.CreateShortcut($linkPath);if($link.Description -ne 'Selvarithik Gateway managed local startup'){throw 'Unrelated shortcut preserved.'};Remove-Item -LiteralPath $linkPath}
Write-Output 'Managed Gateway startup removed.'
