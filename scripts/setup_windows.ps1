$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw 'Python 3.11+ est requis.' }
if (-not (Get-Command node -ErrorAction SilentlyContinue)) { throw 'Node.js LTS est requis.' }

$VenvDirectory = Join-Path $Root '.venv-claimshield'
$VenvPython = Join-Path $VenvDirectory 'Scripts\python.exe'
if ((Test-Path $VenvDirectory) -and -not (Test-Path $VenvPython)) {
    throw 'Le dossier .venv-claimshield existe mais son Python est introuvable. Supprimez ou renommez-le, puis relancez ce script.'
}
if (-not (Test-Path $VenvDirectory)) { python -m venv $VenvDirectory }
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r backend\requirements.txt
& $VenvPython -m pip install -e '.\backend[asr]'
& $VenvPython -m pip install 'pytest>=8,<9' 'httpx>=0.27,<1'
if (-not (Test-Path 'frontend\node_modules')) { npm --prefix frontend install }
New-Item -ItemType Directory -Force -Path 'data\runtime' | Out-Null
& $VenvPython scripts\check_environment.py
Write-Host 'Installation du runtime réel terminée : faster-whisper est activé.' -ForegroundColor Green

