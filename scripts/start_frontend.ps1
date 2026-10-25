$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
npm --prefix frontend run dev -- --host 127.0.0.1

