#!/usr/bin/env bash
set -euo pipefail

# Metl - Deploy script for GitHub Actions self-hosted runner
# Builds and deploys to K3s on the VPS

echo "=== Metl Deploy ==="

REGISTRY="${REGISTRY:-ghcr.io}"
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Build backend
echo ">>> Building backend..."
docker build -t metl-backend:${IMAGE_TAG} ./backend
docker tag metl-backend:${IMAGE_TAG} ${REGISTRY}/metl-backend:${IMAGE_TAG}

# Build frontend
echo ">>> Building frontend..."
docker build -t metl-frontend:${IMAGE_TAG} ./frontend
docker tag metl-frontend:${IMAGE_TAG} ${REGISTRY}/metl-frontend:${IMAGE_TAG}

# Push images (requires docker login)
echo ">>> Pushing images..."
docker push ${REGISTRY}/metl-backend:${IMAGE_TAG}
docker push ${REGISTRY}/metl-frontend:${IMAGE_TAG}

# Update image references in K8s manifests
sed -i "s|image: metl-backend:.*|image: ${REGISTRY}/metl-backend:${IMAGE_TAG}|g" infra/k8s/backend-deployment.yaml
sed -i "s|image: metl-frontend:.*|image: ${REGISTRY}/metl-frontend:${IMAGE_TAG}|g" infra/k8s/frontend-deployment.yaml

# Apply to K3s
echo ">>> Deploying to K3s..."
kubectl apply -f infra/k8s/

# Rollout restart
echo ">>> Rolling restart..."
kubectl -n metl rollout restart deployment/metl-backend 2>/dev/null || true
kubectl -n metl rollout restart deployment/metl-frontend 2>/dev/null || true

echo ">>> Waiting for rollout..."
kubectl -n metl rollout status deployment/metl-backend --timeout=300s 2>/dev/null || true
kubectl -n metl rollout status deployment/metl-frontend --timeout=300s 2>/dev/null || true

echo "=== Deploy Complete ==="