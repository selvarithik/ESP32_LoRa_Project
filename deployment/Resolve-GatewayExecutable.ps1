function Get-GatewayExecutable([string]$ProjectRoot) {
    $releasePointer = Join-Path $ProjectRoot 'deployment/active-release.json'
    if (!(Test-Path -LiteralPath $releasePointer)) { return (Join-Path $ProjectRoot 'dist/Gateway/Gateway.exe') }
    $release = Get-Content -LiteralPath $releasePointer -Raw | ConvertFrom-Json
    if ($release.executable -isnot [string]) { throw 'Invalid active release pointer' }
    $releaseRoot = [IO.Path]::GetFullPath($ProjectRoot)
    $releaseExecutable = [IO.Path]::GetFullPath((Join-Path $releaseRoot $release.executable))
    if (!$releaseExecutable.StartsWith($releaseRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or [IO.Path]::GetExtension($releaseExecutable) -ne '.exe') { throw 'Active executable must remain inside this project' }
    if (!(Test-Path -LiteralPath $releaseExecutable -PathType Leaf)) { return (Join-Path $ProjectRoot 'dist/Gateway/Gateway.exe') }
    return $releaseExecutable
}
