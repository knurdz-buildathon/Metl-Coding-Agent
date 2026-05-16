#!/usr/bin/env bash
set -euo pipefail

# Metl - VPS Provisioning Script
# Tested on Ubuntu 24.04 LTS with Docker and K3s

echo "=== Metl VPS Setup ==="
echo "This script will install Docker, K3s, and configure the Metl agent stack."
echo ""

# Check prerequisites
if [ "$(id -u)" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

DOMAIN="${DOMAIN:-metl.yourdomain.com}"
EMAIL="${EMAIL:-admin@yourdomain.com}"

# 1. System updates
echo ">>> Updating system packages..."
apt-get update && apt-get upgrade -y

# 2. Install Docker
echo ">>> Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | bash
    systemctl enable --now docker
fi

# 3. Install K3s (lightweight Kubernetes)
echo ">>> Installing K3s..."
if ! command -v k3s &>/dev/null; then
    curl -sfL https://get.k3s.io | sh -s - \
        --disable traefik \
        --write-kubeconfig-mode 644
    export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
fi

# 4. Install Helm (for cert-manager, etc.)
echo ">>> Installing Helm..."
if ! command -v helm &>/dev/null; then
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
fi

# 5. Install cert-manager
echo ">>> Installing cert-manager..."
kubectl create namespace cert-manager 2>/dev/null || true
helm repo add jetstack https://charts.jetstack.io 2>/dev/null || true
helm upgrade --install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --set installCRDs=true \
    --wait

# 6. Create Let's Encrypt ClusterIssuer
echo ">>> Creating Let's Encrypt ClusterIssuer..."
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ${EMAIL}
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: traefik
EOF

# 7. Create Metl namespace and resources
echo ">>> Deploying Metl..."
kubectl create namespace metl 2>/dev/null || true

# 8. Create persistent volume for workspaces
echo ">>> Creating workspace volume..."
mkdir -p /data/metl-workspaces
chmod 777 /data/metl-workspaces

cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: metl-workspaces-pv
  namespace: metl
spec:
  capacity:
    storage: 100Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/metl-workspaces
  persistentVolumeReclaimPolicy: Retain
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: metl-workspaces-pvc
  namespace: metl
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
EOF

# 9. Install Traefik ingress controller
echo ">>> Installing Traefik ingress controller..."
kubectl create namespace traefik 2>/dev/null || true
helm repo add traefik https://traefik.github.io/charts 2>/dev/null || true
helm upgrade --install traefik traefik/traefik \
    --namespace traefik \
    --set ports.web.port=80 \
    --set ports.websecure.port=443 \
    --set service.type=LoadBalancer \
    --wait

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Update infra/k8s/ingress.yaml with your actual domain"
echo "  2. Update infra/k8s/config.yaml with your LLM provider settings"
echo "  3. Create metl-secrets with your API keys:"
echo "     kubectl -n metl create secret generic metl-secrets \\"
echo "       --from-literal=openai_api_key=... \\"
echo "       --from-literal=anthropic_api_key=... \\"
echo "       --from-literal=github_pat=..."
echo "  4. Apply all K8s manifests:"
echo "     kubectl apply -f infra/k8s/"
echo "  5. Configure DNS: ${DOMAIN} -> VPS IP"
echo ""
echo "To check status: kubectl -n metl get pods"