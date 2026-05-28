param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    [string]$ApiKey,
    [string]$Model = "gemma4:31b",
    [string]$Url = "https://ollama.com",
    [string]$TimeoutSeconds = "300"
)

$ErrorActionPreference = "Stop"

if (-not $ApiKey) {
    $ApiKey = Read-Host "Enter $Environment Ollama API key"
}

if (-not $ApiKey) {
    throw "Ollama API key is required"
}

$namespace = "learntogrow-$Environment"
$enc = [Text.Encoding]::UTF8
$patchObject = @{
    data = @{
        "ollama-url"     = [Convert]::ToBase64String($enc.GetBytes($Url))
        "ollama-model"   = [Convert]::ToBase64String($enc.GetBytes($Model))
        "ollama-timeout" = [Convert]::ToBase64String($enc.GetBytes($TimeoutSeconds))
        "ollama-api-key" = [Convert]::ToBase64String($enc.GetBytes($ApiKey))
    }
}

$patchFile = Join-Path $env:TEMP "ollama-$Environment-secret-patch.json"
$patchObject | ConvertTo-Json -Depth 5 | Set-Content -Encoding utf8 $patchFile

try {
    kubectl patch secret learntogrow-secrets -n $namespace --type merge --patch-file $patchFile
}
finally {
    Remove-Item $patchFile -ErrorAction SilentlyContinue
}

Write-Host "`nSecret keys now present in ${namespace}:"
kubectl get secret learntogrow-secrets -n $namespace -o go-template='{{range $k,$v := .data}}{{println $k}}{{end}}'
