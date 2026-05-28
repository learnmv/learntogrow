param(
    [ValidateSet("dev", "prod")]
    [string]$Environment = "dev"
)

$ErrorActionPreference = "Stop"

$namespace = "learntogrow-$Environment"

Write-Host "== backend env shape in $namespace =="
kubectl exec deployment/backend -n $namespace -- python -c "import os; print('OLLAMA_URL=', os.getenv('OLLAMA_URL')); print('OLLAMA_MODEL=', os.getenv('OLLAMA_MODEL')); print('HAS_KEY=', bool(os.getenv('OLLAMA_API_KEY'))); print('WORKERS=', os.getenv('OLLAMA_GENERATION_WORKERS')); print('STRUCTURED=', os.getenv('OLLAMA_ENABLE_STRUCTURED_OUTPUTS'))"

Write-Host "`n== DNS resolution =="
kubectl exec deployment/backend -n $namespace -- python -c "import socket; print(socket.getaddrinfo('ollama.com', 443)[0])"

Write-Host "`n== unauthenticated tags endpoint =="
kubectl exec deployment/backend -n $namespace -- python -c "import urllib.request; r=urllib.request.urlopen('https://ollama.com/api/tags', timeout=10); print(r.status)"

Write-Host "`n== authenticated generate endpoint =="
kubectl exec deployment/backend -n $namespace -- python -c "import os, urllib.request, json; req=urllib.request.Request('https://ollama.com/api/generate', data=json.dumps({'model': os.environ.get('OLLAMA_MODEL'), 'prompt': 'Return the word ok only.', 'stream': False}).encode(), headers={'Content-Type':'application/json','Authorization':'Bearer '+os.environ.get('OLLAMA_API_KEY','')}); r=urllib.request.urlopen(req, timeout=60); print(r.status); print(json.loads(r.read()).get('response','')[:80])"
