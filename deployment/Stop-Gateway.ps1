param([string]$DataDir)
$projectRoot=Split-Path -Parent $PSScriptRoot
if(!$DataDir){$DataDir=Join-Path $projectRoot 'data'}
. (Join-Path $PSScriptRoot 'Resolve-GatewayExecutable.ps1')
$executable=Get-GatewayExecutable $projectRoot
if(Test-Path -LiteralPath $executable){& $executable stop --data-dir $DataDir}else{& (Join-Path $projectRoot '.venv/Scripts/python.exe') (Join-Path $projectRoot 'tools/gateway.py') stop --data-dir $DataDir}
exit $LASTEXITCODE
