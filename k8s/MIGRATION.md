# Kubernetes Namespace Migration Guide

## What Changed

The Kustomize structure has been updated to use **separate namespaces** for dev and prod instead of mixing them in the `default` namespace.

### Before (Broken)
- Both dev and prod in `default` namespace
- Same labels causing service cross-traffic
- Intermittent 404 errors when load balancing hit wrong pod

### After (Fixed)
- Dev in `learntogrow-dev` namespace
- Prod in `learntogrow-prod` namespace
- Complete isolation between environments

## Migration Steps

### 1. Create Namespaces

```bash
kubectl create namespace learntogrow-dev
kubectl create namespace learntogrow-prod
```

### 2. Backup Current State (Optional but Recommended)

```bash
kubectl get all -n default -o yaml > k8s-backup-default-$(date +%Y%m%d).yaml
```

### 3. Delete Old Resources

⚠️ **This will cause downtime. Plan for a maintenance window.**

```bash
# Delete old dev resources
kubectl delete deployment dev-learntogrow-backend -n default
kubectl delete deployment dev-learntogrow-frontend -n default
kubectl delete service dev-learntogrow-backend -n default
kubectl delete service dev-learntogrow-frontend -n default

# Delete old prod resources
kubectl delete deployment prod-learntogrow-backend -n default
kubectl delete deployment prod-learntogrow-frontend -n default
kubectl delete service prod-learntogrow-backend -n default
kubectl delete service prod-learntogrow-frontend -n default
```

### 4. Apply New Configuration

```bash
# Apply dev environment
cd k8s/overlays/dev
kubectl apply -k .
kubectl apply -f secrets.yaml

# Apply prod environment
cd ../prod
kubectl apply -k .
kubectl apply -f secrets.yaml
```

### 5. Verify Deployment

```bash
# Check dev namespace
kubectl get all -n learntogrow-dev

# Check prod namespace
kubectl get all -n learntogrow-prod

# Verify services have correct endpoints (should show only pods from same namespace)
kubectl describe service backend -n learntogrow-dev
kubectl describe service backend -n learntogrow-prod
```

### 6. Test the Fix

```bash
# Test dev backend (should only hit dev pods)
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code}\n" "http://10.0.0.131:30800/api/v1/health"
done

# Test prod backend (should only hit prod pods)
for i in {1..10}; do
  curl -s -o /dev/null -w "%{http_code}\n" "http://10.0.0.131:30801/api/v1/health"
done

# Test the previously failing endpoint
curl "http://10.0.0.131:30800/api/v1/questions/standard/10?limit=1"
```

All requests should return `200 OK` consistently.

## Access URLs After Migration

| Environment | Service | URL |
|------------|---------|-----|
| Dev | Backend API | http://10.0.0.131:30800/api/v1 |
| Dev | Frontend | http://10.0.0.131:30081 |
| Prod | Backend API | http://10.0.0.131:30801/api/v1 |
| Prod | Frontend | http://10.0.0.131:30082 |

## Database Access

The database remains in the `default` namespace and is accessible from both environments via NodePort:
- Host: `10.0.0.131`
- Port: `30432`

This works because we're using the node's external IP, which is routable from any namespace.

## Rollback (If Needed)

If you need to rollback:

```bash
# Delete new resources
kubectl delete namespace learntogrow-dev
kubectl delete namespace learntogrow-prod

# Restore from backup (if you created one)
kubectl apply -f k8s-backup-default-YYYYMMDD.yaml
```

## Troubleshooting

### Issue: Secrets not found

Secrets are not applied by Kustomize (they're excluded). Make sure to apply them manually:

```bash
kubectl apply -f k8s/overlays/dev/secrets.yaml -n learntogrow-dev
kubectl apply -f k8s/overlays/prod/secrets.yaml -n learntogrow-prod
```

### Issue: Image pull errors

Make sure the `ghcr-secret` exists in both namespaces:

```bash
kubectl get secret ghcr-secret -n learntogrow-dev
kubectl get secret ghcr-secret -n learntogrow-prod
```

If missing, create it:

```bash
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_USERNAME \
  --docker-password=YOUR_TOKEN \
  -n learntogrow-dev

# Repeat for prod namespace
```

### Issue: Frontend can't reach backend

Check the ConfigMap values:

```bash
kubectl get configmap frontend-config -n learntogrow-dev -o yaml
kubectl get configmap frontend-config -n learntogrow-prod -o yaml
```

Dev should have: `apiUrl: http://10.0.0.131:30800/api/v1`
Prod should have: `apiUrl: http://10.0.0.131:30801/api/v1`

## Summary of Changes

### Base Resources
- Removed hardcoded `namespace: default` from deployments
- Simplified resource names (removed `learntogrow-` prefix)
- Kustomize handles namespacing via `namespace:` field

### Dev Overlay
- Namespace: `learntogrow-dev`
- Removed `namePrefix: dev-`
- Backend NodePort: `30800`
- Frontend NodePort: `30081`
- Image tag: `dev`

### Prod Overlay
- Namespace: `learntogrow-prod`
- Removed `namePrefix: prod-`
- Backend NodePort: `30801`
- Frontend NodePort: `30082`
- Image tag: `stable`
- **Fixed**: Frontend config now points to correct backend port (30801)

### CI/CD Workflows Updated
- `.github/workflows/dev.yml`: Changed deployment names from `dev-learntogrow-backend` to `backend` in `learntogrow-dev` namespace
- `.github/workflows/prod.yml`: Changed deployment names from `prod-learntogrow-backend` to `backend` in `learntogrow-prod` namespace
- All verification commands now target correct namespaces
