# CI/CD Setup Guide

## What Was Created

### 1. Containerization
- `backend/Dockerfile` - Python 3.11 slim with uvicorn
- `frontend/Dockerfile` - Multi-stage Node.js + nginx
- `frontend/nginx.conf` - Reverse proxy to backend

### 2. GitHub Actions (Local Image Storage)
- `.github/workflows/dev.yml` - Builds and saves images to `/home/sysadmin/dev-builds/`
- `.github/workflows/prod.yml` - Builds and saves images to `/home/sysadmin/prod-builds/`

Images are stored locally as tar files using `docker save` and loaded with `docker load` during deployment.

### 3. Kubernetes Manifests
- `k8s/secrets.yaml` - Database credentials (gitignored)
- `k8s/backend-deployment.yaml` - FastAPI deployment (2 replicas)
- `k8s/backend-service.yaml` - NodePort service (port 30800)
- `k8s/frontend-deployment.yaml` - Nginx deployment (2 replicas)
- `k8s/frontend-service.yaml` - NodePort service (port 30080)
- `k8s/kustomization.yaml` - Kustomize base configuration

### 4. Branches
- `main` - Production branch
- `dev` - Development branch

## Image Storage Locations

**Dev builds:** `/home/sysadmin/dev-builds/`
- `learntogrow-backend-dev.tar`
- `learntogrow-frontend-dev.tar`

**Prod builds:** `/home/sysadmin/prod-builds/`
- `learntogrow-backend-stable.tar`
- `learntogrow-frontend-stable.tar`
- `learntogrow-backend-v{VERSION}.tar` (versioned)
- `learntogrow-frontend-v{VERSION}.tar` (versioned)

## Setup Instructions

### Step 1: Configure GitHub Secrets

Go to **GitHub Repo → Settings → Secrets and variables → Actions**

Add this secret:

**KUBE_CONFIG** - Base64 encoded kubectl config:
```bash
cat ~/.kube/config | base64 -w0
```
Copy the output and paste as KUBE_CONFIG secret.

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

### Step 4: Get Node IP for Access

```bash
# Get your node's IP address
kubectl get nodes -o wide

# Example output shows EXTERNAL-IP or INTERNAL-IP column
# Use that IP with the NodePort to access services
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
   - Build dev images locally
   - Save to `/home/sysadmin/dev-builds/`
   - Load images into Docker
   - Deploy to Kubernetes using local images

3. **Access dev deployment**:
   ```
   Frontend: http://<node-ip>:30080
   Backend:  http://<node-ip>:30800
   ```

### Production Flow

1. **Create PR from dev to main**:
   - Go to GitHub → Pull Requests → New PR
   - Base: `main`, Compare: `dev`
   - Review and merge

2. **GitHub Actions will**:
   - Build prod images locally
   - Save to `/home/sysadmin/prod-builds/` (with stable and versioned tags)
   - Load images into Docker
   - Deploy to Kubernetes using local images
   - Create GitHub release

3. **Access production**:
   ```
   Frontend: http://<node-ip>:30080
   Backend:  http://<node-ip>:30800
   ```

## Managing Local Images

### View stored images

```bash
# Dev builds
ls -lh /home/sysadmin/dev-builds/

# Prod builds
ls -lh /home/sysadmin/prod-builds/
```

### Load an image manually

```bash
# Load dev backend
docker load < /home/sysadmin/dev-builds/learntogrow-backend-dev.tar

# Load stable frontend
docker load < /home/sysadmin/prod-builds/learntogrow-frontend-stable.tar

# Check loaded images
docker images | grep learntogrow
```

### Rollback to previous version

```bash
# List available versions
ls -lt /home/sysadmin/prod-builds/

# Load specific version
docker load < /home/sysadmin/prod-builds/learntogrow-backend-v2024.01.15-a1b2c3d.tar

# Update deployment to use specific image
kubectl set image deployment/learntogrow-backend \
  backend=learntogrow-backend:v2024.01.15-a1b2c3d -n default
```

### Clean up old images

```bash
# Keep only last 5 versions in prod
ls -t /home/sysadmin/prod-builds/*.tar | tail -n +6 | xargs rm -f

# Keep only last 3 dev builds
ls -t /home/sysadmin/dev-builds/*.tar | tail -n +4 | xargs rm -f
```

## Monitoring Commands

```bash
# Check pods
kubectl get pods -n default

# Check services
kubectl get svc -n default

# View logs
kubectl logs -f deployment/learntogrow-backend -n default
kubectl logs -f deployment/learntogrow-frontend -n default

# Describe deployment
kubectl describe deployment learntogrow-backend -n default

# Rollout status
kubectl rollout status deployment/learntogrow-backend -n default

# Check disk space used by images
du -sh /home/sysadmin/dev-builds/
du -sh /home/sysadmin/prod-builds/
```

## Troubleshooting

### Runner not picking up jobs
- Check runner status: `sudo ./svc.sh status`
- Restart runner: `sudo ./svc.sh stop && sudo ./svc.sh start`
- Check logs: `cat ~/actions-runner/_diag/Worker_*.log`

### Image not found during deploy
- Check if tar file exists: `ls -la /home/sysadmin/dev-builds/`
- Load manually: `docker load < /path/to/image.tar`
- Check loaded images: `docker images | grep learntogrow`

### Pods not starting (ImagePullBackOff)
- Verify image exists locally: `docker images`
- Check imagePullPolicy is set to Never: `kubectl get deployment learntogrow-backend -o yaml | grep imagePullPolicy`
- Load image manually: `docker load < /home/sysadmin/dev-builds/learntogrow-backend-dev.tar`

### Out of disk space
- Clean old builds: `rm /home/sysadmin/dev-builds/*.tar`
- Clean old versions: Keep only last 5 prod versions
- Prune Docker: `docker system prune -f`

### Cannot access services
- Check services are NodePort: `kubectl get svc`
- Verify node IP: `kubectl get nodes -o wide`
- Test locally: `curl http://<node-ip>:30080` and `curl http://<node-ip>:30800`
- Check firewall allows ports 30080 and 30800

## Security Notes

- `k8s/secrets.yaml` is gitignored - never commit real credentials
- Images are stored locally on your server - ensure adequate disk space
- Runner runs on your server - ensure it's secure
- Database is external - ensure network connectivity
- Local images are not pushed to any external registry
