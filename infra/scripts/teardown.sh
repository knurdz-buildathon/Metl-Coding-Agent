#!/usr/bin/env bash
set -euo pipefail

# Metl - Teardown
echo "=== Metl Teardown ==="

read -p "This will remove all Metl resources. Continue? (y/N) " confirm
if [ "$confirm" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

# Remove K8s resources
if command -v kubectl &>/dev/null; then
    echo "Removing K8s resources..."
    kubectl delete namespace metl 2>/dev/null || true
    kubectl delete namespace cert-manager 2>/dev/null || true
    kubectl delete namespace traefik 2>/dev/null || true
fi

# Remove Docker volumes
echo "Removing Docker volumes..."
docker volume rm metl_redis-data 2>/dev/null || true

# Remove workspace data
echo "Cleaning workspace data..."
rm -rf /data/metl-workspaces 2>/dev/null || true

echo "=== Teardown Complete ==="