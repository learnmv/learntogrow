param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev",
    [int]$LogTail = 80
)

$ErrorActionPreference = "Stop"

$namespace = "learntogrow-$Environment"

Write-Host "== $namespace pods =="
kubectl get pods -n $namespace -o wide

Write-Host "`n== backend rollout =="
kubectl rollout status deployment/backend -n $namespace --timeout=30s

Write-Host "`n== frontend rollout =="
kubectl rollout status deployment/frontend -n $namespace --timeout=30s

Write-Host "`n== backend Ollama env shape =="
kubectl exec deployment/backend -n $namespace -- python -c "import os; print('OLLAMA_URL=', os.getenv('OLLAMA_URL')); print('OLLAMA_MODEL=', os.getenv('OLLAMA_MODEL')); print('HAS_KEY=', bool(os.getenv('OLLAMA_API_KEY'))); print('WORKERS=', os.getenv('OLLAMA_GENERATION_WORKERS')); print('STRUCTURED=', os.getenv('OLLAMA_ENABLE_STRUCTURED_OUTPUTS'))"

Write-Host "`n== recent backend log tail =="
kubectl logs deployment/backend -n $namespace --tail=$LogTail

Write-Host "`n== calico pods =="
kubectl get pods -n calico-system
