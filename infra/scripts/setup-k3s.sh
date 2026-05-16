#!/usr/bin/env bash
set -euo pipefail

echo "=== Metl K3s Setup ==="
echo "Configuring K3s for Metl deployment..."

# Wait for K3s to be ready
echo "Waiting for K3s..."
while ! k3s kubectl get nodes 2>/dev/null; do
    sleep 2
done

# Label the node for agent workloads
k3s kubectl label nodes --all metl.io/role=agent 2>/dev/null || true

# Create namespace
k3s kubectl create namespace metl 2>/dev/null || true

# Apply core manifests
echo "Deploying Metl services..."
k3s kubectl apply -f /opt/metl/infra/k8s/

# Wait for deployments
echo "Waiting for deployments to be ready..."
k3s kubectl -n metl wait --for=condition=available --timeout=300s deployment/metl-redis 2>/dev/null || true
k3s kubectl -n metl wait --for=condition=available --timeout=300s deployment/metl-backend 2>/dev/null || true
k3s kubectl -n metl wait --for=condition=available --timeout=300s deployment/metl-frontend 2>/dev/null || true

echo ""
echo "=== K3s Setup Complete ==="
echo "Services:"
k3s kubectl -n metl get all