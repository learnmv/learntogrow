# LearnToGrow Codex Runbook

This runbook captures the operational facts and repeatable commands Codex should use for LearnToGrow work. Keep it short, current, and boringly reliable.

## Branches And Deployments

- `dev` deploys to the dev Kubernetes namespace: `learntogrow-dev`.
- `main` deploys to the prod Kubernetes namespace: `learntogrow-prod`.
- Pushing to either branch triggers the corresponding GitHub Actions workflow on the self-hosted runner.
- Prod promotion is usually: merge `dev` into `main`, run checks, then push `main`.

## Kubernetes Namespaces

```powershell
kubectl get pods -n learntogrow-dev
kubectl get pods -n learntogrow-prod
```

Backend logs:

```powershell
kubectl logs deployment/backend -n learntogrow-dev --tail=100
kubectl logs deployment/backend -n learntogrow-prod --tail=100
```

Follow live logs:

```powershell
kubectl logs -f deployment/backend -n learntogrow-dev
kubectl logs -f deployment/backend -n learntogrow-prod
```

## Databases

PostgreSQL runs in the `default` namespace.

```powershell
kubectl get pods -n default
kubectl exec postgres-69d98cd59d-hl42n -n default -- psql -U admin -d learntogrow_dev
kubectl exec postgres-69d98cd59d-hl42n -n default -- psql -U admin -d learntogrow_prod
```

Apply migrations carefully, one file at a time:

```powershell
.\scripts\apply-migration.ps1 -Database prod -Migration backend\app\migrations\016_add_generation_quality_pipeline.sql
```

Before applying a migration, inspect the target schema when possible:

```powershell
kubectl exec postgres-69d98cd59d-hl42n -n default -- psql -U admin -d learntogrow_prod -c "\d generation_jobs"
```

## Ollama Cloud

The app is configured to use direct Ollama Cloud API, not a local Ollama proxy.

Expected values:

```text
OLLAMA_URL=https://ollama.com
OLLAMA_MODEL=gemma4:31b
OLLAMA_GENERATION_WORKERS=3
OLLAMA_ENABLE_STRUCTURED_OUTPUTS=false
```

Why:

- The production server does not have a useful GPU.
- Ollama Pro cloud concurrency should be treated as 3 workers.
- Ollama Cloud currently should not be treated like local structured output mode; the backend extracts and validates JSON from model text.

Patch secrets with a file-based PowerShell script to avoid JSON quoting errors:

```powershell
.\scripts\patch-ollama-secret.ps1 -Environment dev
.\scripts\patch-ollama-secret.ps1 -Environment prod
```

Verify without printing secret values:

```powershell
kubectl get secret learntogrow-secrets -n learntogrow-dev -o go-template='{{range $k,$v := .data}}{{println $k}}{{end}}'
kubectl get secret learntogrow-secrets -n learntogrow-prod -o go-template='{{range $k,$v := .data}}{{println $k}}{{end}}'
```

Verify Ollama Cloud from inside a backend pod:

```powershell
.\scripts\verify-ollama-cloud.ps1 -Environment dev
.\scripts\verify-ollama-cloud.ps1 -Environment prod
```

## Question Generation

Current admin generation flow:

1. Admin selects subject, grade, standards, question count, type, review mode, timeout, and review score.
2. Backend creates a `generation_jobs` row and `generation_job_standards` rows.
3. Worker builds a prompt from database prompt templates.
4. Ollama generates a JSON candidate.
5. Backend validates the candidate structure.
6. Ollama reviewer scores the candidate.
7. Backend stores only approved questions.
8. Audit details are saved in `question_generation_audits`.

Required migration for this quality pipeline:

```text
backend/app/migrations/016_add_generation_quality_pipeline.sql
```

If logs show:

```text
column "quality_mode" of relation "generation_jobs" does not exist
```

apply migration `016` to that environment's database.

## Common Failure: Pod Cannot Reach Ollama Cloud

Symptoms:

```text
Temporary failure in name resolution
Could not connect to Ollama at https://ollama.com
```

Check from inside the backend pod:

```powershell
kubectl exec deployment/backend -n learntogrow-dev -- python -c "import socket; print(socket.getaddrinfo('ollama.com', 443)[0])"
kubectl exec deployment/backend -n learntogrow-dev -- python -c "import urllib.request; print(urllib.request.urlopen('https://ollama.com/api/tags', timeout=10).status)"
```

If host can reach the internet but pods cannot, check Calico:

```powershell
kubectl get pods -n calico-system
kubectl get deployment tigera-operator -n tigera-operator
```

Known fix from May 2026 incident:

```powershell
kubectl scale deployment tigera-operator -n tigera-operator --replicas=1
kubectl rollout status deployment/tigera-operator -n tigera-operator --timeout=120s
kubectl get pods -n calico-system
```

Expected Calico pods:

```text
calico-node              1/1 Running
calico-typha             1/1 Running
calico-kube-controllers  1/1 Running
```

## Safe Checks Before Push

Backend:

```powershell
python -m compileall backend/app
```

Frontend:

```powershell
Set-Location frontend
node .\node_modules\typescript\bin\tsc -b
node .\node_modules\vite\bin\vite.js build
```

Targeted lint when frontend files changed:

```powershell
node .\node_modules\eslint\bin\eslint.js src/components/admin/AdminChat.tsx src/components/admin/AdminDashboard.tsx src/services/admin.ts src/types/admin.ts
```

## Promotion To Prod

Use:

```powershell
.\scripts\promote-dev-to-main.ps1
```

Or manually:

```powershell
git fetch origin main dev
git switch main
git pull --ff-only origin main
git merge --no-ff dev -m "Merge dev into main"
python -m compileall backend/app
Set-Location frontend
node .\node_modules\vite\bin\vite.js build
Set-Location ..
git push origin main
```

After prod deploy:

```powershell
kubectl rollout status deployment/backend -n learntogrow-prod --timeout=300s
kubectl logs deployment/backend -n learntogrow-prod --tail=100
```

## Useful Helper Scripts

- `scripts/check-k8s-health.ps1`
- `scripts/patch-ollama-secret.ps1`
- `scripts/verify-ollama-cloud.ps1`
- `scripts/apply-migration.ps1`
- `scripts/promote-dev-to-main.ps1`
