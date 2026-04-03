# Sealed Secrets Setup Guide

This document describes how to set up Sealed Secrets for the LearnToGrow project to securely manage Kubernetes secrets in Git.

## Overview

Sealed Secrets allows you to encrypt Kubernetes secrets into `SealedSecret` CRDs that can be safely committed to Git. The sealed-secrets controller running in the cluster automatically decrypts them into native Kubernetes secrets.

## Why Sealed Secrets

- **K8s-native**: Works seamlessly with Kubernetes via CRDs and controllers
- **Git-safe**: Encrypted secrets can be committed to version control
- **Simple workflow**: One CLI command (`kubeseal`) to encrypt
- **No external dependencies**: Controller runs in-cluster

## Installation

### 1. Install Controller in Kubernetes

```bash
# Install the sealed-secrets controller
kubectl apply -f https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.3/controller.yaml

# Verify controller is running
kubectl get pods -n kube-system -l name=sealed-secrets-controller
```

### 2. Install kubeseal CLI

**Local machine:**

```bash
# Linux (amd64)
wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.3/kubeseal-0.27.3-linux-amd64.tar.gz
tar -xzf kubeseal-0.27.3-linux-amd64.tar.gz
sudo mv kubeseal /usr/local/bin/

# macOS
brew install kubeseal
```

**GitHub Actions runner (self-hosted):**

Add to your workflow or runner setup script:

```bash
curl -sL https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.3/kubeseal-0.27.3-linux-amd64.tar.gz | tar xz
sudo mv kubeseal /usr/local/bin/
```

## Usage

### Seal an Existing Secret

```bash
# Fetch the public certificate from the cluster (one time)
kubeseal --fetch-cert > sealed-secrets-cert.pem

# Seal your secret file
kubeseal --cert sealed-secrets-cert.pem --format yaml < k8s/secrets.yaml > k8s/secrets-sealed.yaml

# The sealed secret is safe to commit
git add k8s/secrets-sealed.yaml
git commit -m "Add sealed secrets"
git push
```

### Create a New Secret and Seal It

```bash
# Create a secret imperatively and seal it
kubectl create secret generic learntogrow-secrets \
  --from-literal=db-user=admin \
  --from-literal=db-password=secretpassword \
  --dry-run=client -o yaml | \
  kubeseal --format yaml > k8s/secrets-sealed.yaml
```

## GitHub Actions Integration

Add this step to your deployment workflow to automatically seal and apply secrets:

```yaml
# .github/workflows/deploy-with-sealed-secrets.yml
name: Deploy with Sealed Secrets

on:
  push:
    branches: [main, dev]

jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Install kubeseal
        run: |
          curl -sL https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.27.3/kubeseal-0.27.3-linux-amd64.tar.gz | tar xz
          sudo mv kubeseal /usr/local/bin/

      - name: Verify controller is running
        run: |
          kubectl get pods -n kube-system -l name=sealed-secrets-controller

      - name: Apply sealed secrets
        run: |
          kubectl apply -f k8s/secrets-sealed.yaml

      - name: Verify secret was created
        run: |
          kubectl get secret learntogrow-secrets -n default
```

## Project Structure Update

```
k8s/
├── secrets.yaml              # Original secrets (gitignored - never commit)
├── secrets-sealed.yaml       # Sealed secrets (safe to commit)
├── secrets.example.yaml      # Template for new developers
├── backend-deployment.yaml
├── backend-service.yaml
├── ...
```

Update `.gitignore`:

```gitignore
# Kubernetes secrets (unsealed)
k8s/secrets.yaml
k8s/*-secret.yaml
!k8s/*-sealed.yaml

# Certificates
sealed-secrets-cert.pem
```

## Migration from Plain Secrets

1. **Backup existing secrets**:
   ```bash
   kubectl get secret learntogrow-secrets -o yaml > k8s/secrets-backup.yaml
   ```

2. **Seal the secret**:
   ```bash
   kubeseal --format yaml < k8s/secrets-backup.yaml > k8s/secrets-sealed.yaml
   ```

3. **Update kustomization**:
   ```yaml
   # k8s/kustomization.yaml
   resources:
     - secrets-sealed.yaml  # Replace secrets.yaml with this
     - backend-deployment.yaml
     - backend-service.yaml
     - frontend-deployment.yaml
     - frontend-service.yaml
     - ingress.yaml
   ```

4. **Apply and verify**:
   ```bash
   kubectl apply -f k8s/secrets-sealed.yaml
   kubectl get secret learntogrow-secrets  # Should show the unsealed secret
   ```

5. **Commit sealed secrets**:
   ```bash
   git add k8s/secrets-sealed.yaml
   git rm k8s/secrets.yaml  # Remove unencrypted version from repo
   git commit -m "Migrate to Sealed Secrets"
   ```

## Verification Commands

```bash
# Check sealed secret exists
kubectl get sealedsecrets

# Verify unsealed secret was created
kubectl get secret learntogrow-secrets -o yaml

# View controller logs if issues arise
kubectl logs -n kube-system -l name=sealed-secrets-controller
```

## Important Notes

- **Backup the controller's private key**: The controller generates a private key on first run. If you lose this key, you cannot unseal secrets.
  ```bash
  kubectl get secret -n kube-system sealed-secrets-key -o yaml > sealed-secrets-key-backup.yaml
  ```

- **Scope**: By default, sealed secrets are namespace-scoped. Use `--scope cluster-wide` for cluster-wide scope.

- **Rotation**: To rotate secrets, re-seal with new values and apply. The controller will update the native secret automatically.

## References

- [Sealed Secrets GitHub](https://github.com/bitnami-labs/sealed-secrets)
- [Installation Guide](https://github.com/bitnami-labs/sealed-secrets#installation)
