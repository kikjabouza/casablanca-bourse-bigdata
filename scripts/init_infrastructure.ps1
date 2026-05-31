# Initialise Cassandra + vérifie Trino après docker compose up
# Usage : .\scripts\init_infrastructure.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " INITIALISATION INFRASTRUCTURE — Bourse de Casablanca" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Démarrer Docker
Write-Host "`n[1/4] Demarrage des containers..." -ForegroundColor Yellow
Set-Location $Root
docker compose up -d

# 2. Attendre Cassandra
Write-Host "`n[2/4] Attente Cassandra (60s)..." -ForegroundColor Yellow
Start-Sleep -Seconds 60

$retries = 0
while ($retries -lt 10) {
    $result = docker exec cassandra cqlsh -e "DESCRIBE KEYSPACES" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Cassandra pret." -ForegroundColor Green
        break
    }
    $retries++
    Write-Host "  Retry $retries/10..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
}

if ($retries -ge 10) {
    Write-Host "  ERREUR : Cassandra non accessible." -ForegroundColor Red
    exit 1
}

# 3. Initialiser le schéma
Write-Host "`n[3/4] Application du schema Cassandra (init.cql)..." -ForegroundColor Yellow
docker exec cassandra cqlsh -f /cassandra/init.cql
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Schema bourse_data cree." -ForegroundColor Green
} else {
    Write-Host "  ERREUR lors de l'init CQL." -ForegroundColor Red
    exit 1
}

# 4. Vérifier Trino
Write-Host "`n[4/4] Verification Trino + Metabase..." -ForegroundColor Yellow
Start-Sleep -Seconds 15
py -3 "$Root\scripts\verify_stack.py"

Write-Host ""
Write-Host "Prochaines etapes :" -ForegroundColor Cyan
Write-Host "  1. Charger les donnees : py -3 flows/initial_load_flow.py"
Write-Host "  2. Requetes SQL       : sql/queries.sql via http://localhost:8080"
Write-Host "  3. Dashboards         : docs/ANALYSE_REPORTING.md"
Write-Host ""
