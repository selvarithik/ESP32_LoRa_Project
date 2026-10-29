param([string]$DataDir,[string]$Config,[switch]$NoBrowser)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
if(!$DataDir){$DataDir=Join-Path $projectRoot 'data'}
if(!$Config){$Config=Join-Path $PSScriptRoot 'local.json';if(!(Test-Path -LiteralPath $Config)){$Config=Join-Path $PSScriptRoot 'local.example.json'}}
$executable=Join-Path $projectRoot 'dist/Gateway/Gateway.exe'
$arguments=@('serve','--data-dir',('"'+$DataDir+'"'),'--config',('"'+$Config+'"'))
if(!(Test-Path -LiteralPath $executable)){$executable=Join-Path $projectRoot '.venv/Scripts/python.exe';$arguments=@(('"'+(Join-Path $projectRoot 'tools/gateway.py')+'"'))+$arguments}
if($NoBrowser){$arguments+='--no-browser'}
for($attempt=0;$attempt -lt 4;$attempt++){
 $process=Start-Process -FilePath $executable -ArgumentList $arguments -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru
 $process.WaitForExit()
 if($process.ExitCode -eq 0){exit 0}
 if($attempt -lt 3){Start-Sleep -Seconds ([int[]](2,5,15)[$attempt])}
}
exit 1
