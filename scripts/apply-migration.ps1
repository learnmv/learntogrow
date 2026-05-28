param(
    [ValidateSet("dev", "prod")]
    [string]$Database = "dev",
    [Parameter(Mandatory = $true)]
    [string]$Migration,
    [string]$PostgresPod = "postgres-69d98cd59d-hl42n"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $Migration)) {
    throw "Migration file not found: $Migration"
}

$dbName = if ($Database -eq "prod") { "learntogrow_prod" } else { "learntogrow_dev" }

Write-Host "Applying $Migration to $dbName using pod $PostgresPod"
Get-Content $Migration | kubectl exec -i $PostgresPod -n default -- psql -U admin -d $dbName

Write-Host "`nDone. Recent schema tables:"
kubectl exec $PostgresPod -n default -- psql -U admin -d $dbName -c "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name LIMIT 20;"
