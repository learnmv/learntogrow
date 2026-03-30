# CI/CD Setup Guide

## What Was Created

### 1. Containerization
- `backend/Dockerfile` - Python 3.11 slim with uvicorn
- `frontend/Dockerfile` - Multi-stage Node.js + nginx
- `frontend/nginx.conf` - Reverse proxy to backend

### 2. GitHub Actions
- `.github/workflows/dev.yml` - Builds and deploys on push to `dev` branch
- `.github/workflows/prod.yml` - Builds and deploys on push to `main` branch

### 3. Kubernetes Manifests
- `k8s/secrets.yaml` - Database credentials (gitignored)
- `k8s/backend-deployment.yaml` - FastAPI deployment (2 replicas)
- `k8s/backend-service.yaml` - ClusterIP service
- `k8s/frontend-deployment.yaml` - Nginx deployment (2 replicas)
- `k8s/frontend-service.yaml` - ClusterIP service
- `k8s/ingress.yaml` - Ingress rules (learntogrow.local)
- `k8s/kustomization.yaml` - Kustomize base configuration

### 4. Branches
- `main` - Production branch
- `dev` - Development branch

## Setup Instructions

### Step 1: Configure GitHub Secrets

Go to **GitHub Repo → Settings → Secrets and variables → Actions**

Add these secrets:

1. **KUBE_CONFIG** - Base64 encoded kubectl config:
   ```bash
   cat ~/.kube/config | base64 -w0
   ```
   Copy the output and paste as KUBE_CONFIG secret.

2. **GITHUB_TOKEN** - Auto-generated, no need to set manually

### Step 2: Set Up Local Runner

On your server:

```bash
# Create runner directory
mkdir -p ~/actions-runner && cd ~/actions-runner

# Download runner (check for latest version)
curl -o actions-runner-linux-x64-2.311.0.tar.gz \
  -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# Extract
tar xzf ./actions-runner-linux-x64-2.311.0.tar.gz

# Configure (get token from GitHub repo settings)
./config.sh --url https://github.com/learnmv/learntogrow --token YOUR_TOKEN

# Install as service
sudo ./svc.sh install
sudo ./svc.sh start

# Verify runner is active in GitHub (Settings → Actions → Runners)
```

### Step 3: Create Kubernetes Secrets

On your server:

```bash
cd /home/sysadmin/learntogrow

# Copy secrets template
cp k8s/secrets.example.yaml k8s/secrets.yaml

# Edit with actual values (this file is gitignored)
nano k8s/secrets.yaml

# Apply secrets manually (only once)
kubectl apply -f k8s/secrets.yaml
```

### Step 4: Configure Ingress (if not already set up)

If you don't have nginx-ingress controller:

```bash
# Install nginx ingress controller
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/baremetal/deploy.yaml

# Wait for controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```

### Step 5: Add Host Entry (for local access)

```bash
# Add to /etc/hosts
echo "127.0.0.1 learntogrow.local" | sudo tee -a /etc/hosts
```

## Workflow

### Development Flow

1. **Push to dev branch**:
   ```bash
   git checkout dev
   git add .
   git commit -m "Your changes"
   git push origin dev
   ```

2. **GitHub Actions will**:
   - Build dev images with `dev` tag
   - Push to GHCR
   - Deploy to Kubernetes

3. **Access dev deployment**:
   ```
   http://learntogrow.local
   ```

### Production Flow

1. **Create PR from dev to main**:
   - Go to GitHub → Pull Requests → New PR
   - Base: `main`, Compare: `dev`
   - Review and merge

2. **GitHub Actions will**:
   - Build prod images with `latest`, `stable`, and version tags
   - Push to GHCR
   - Deploy to Kubernetes
   - Create GitHub release

3. **Access production**:
   ```
   http://learntogrow.local
   ```

## Monitoring Commands

```bash
# Check pods
kubectl get pods -n default

# Check services
kubectl get svc -n default

# Check ingress
kubectl get ingress -n default

# View logs
kubectl logs -f deployment/learntogrow-backend -n default
kubectl logs -f deployment/learntogrow-frontend -n default

# Describe deployment
kubectl describe deployment learntogrow-backend -n default

# Rollout status
kubectl rollout status deployment/learntogrow-backend -n default
```

## Troubleshooting

### Runner not picking up jobs
- Check runner status: `sudo ./svc.sh status`
- Restart runner: `sudo ./svc.sh stop && sudo ./svc.sh start`
- Check logs: `cat ~/actions-runner/_diag/Worker_*.log`

### Images not pushing to GHCR
- Verify GITHUB_TOKEN has `write:packages` permission
- Check if runner can access GitHub API

### Pods not starting
- Check events: `kubectl get events -n default --sort-by=.lastTimestamp`
- Check image pull: `kubectl describe pod <pod-name> -n default`
- Verify secrets exist: `kubectl get secrets -n default`

### Ingress not working
- Verify ingress controller: `kubectl get pods -n ingress-nginx`
- Check ingress: `kubectl describe ingress learntogrow-ingress -n default`
- Test locally: `curl -H "Host: learntogrow.local" http://localhost/`

## Security Notes

- `k8s/secrets.yaml` is gitignored - never commit real credentials
- Use GitHub Secrets for sensitive data
- Runner runs on your server - ensure it's secure
- Database is external - ensure network connectivity
