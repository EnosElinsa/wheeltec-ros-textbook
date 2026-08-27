$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$venvRoot = Join-Path $projectRoot '.venv'
$pythonExe = Join-Path $venvRoot 'Scripts\python.exe'
$mkdocsExe = Join-Path $venvRoot 'Scripts\mkdocs.exe'

if (-not (Test-Path -LiteralPath $venvRoot -PathType Container)) {
    python -m venv $venvRoot
}

& $pythonExe -m pip install --disable-pip-version-check -r (Join-Path $projectRoot 'requirements.txt')
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $mkdocsExe build --strict -f (Join-Path $projectRoot 'mkdocs.yml')
exit $LASTEXITCODE
