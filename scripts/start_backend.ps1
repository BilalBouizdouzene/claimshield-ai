$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
& '.\.venv-claimshield\Scripts\python.exe' -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

