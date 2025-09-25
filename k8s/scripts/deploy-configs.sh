#!/bin/bash

# Deploy Kubernetes configurations for microservices
# Usage: ./deploy-configs.sh [environment]
# Environment can be: development, production (default: production)

ENVIRONMENT=${1:-production}
NAMESPACE="microservices-app"

echo "Deploying Kubernetes configurations for environment: $ENVIRONMENT"

# Create namespace if it doesn't exist
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

echo "Applying ConfigMaps..."

# Apply common ConfigMaps
kubectl apply -f ../configmaps/common-config.yaml -n $NAMESPACE
kubectl apply -f ../configmaps/service-urls-config.yaml -n $NAMESPACE
kubectl apply -f ../configmaps/service-ports-config.yaml -n $NAMESPACE

# Apply environment-specific configuration
if [ -f "../environments/$ENVIRONMENT/config.yaml" ]; then
    echo "Applying $ENVIRONMENT environment configuration..."
    kubectl apply -f ../environments/$ENVIRONMENT/config.yaml -n $NAMESPACE
else
    echo "Warning: No configuration found for environment '$ENVIRONMENT', using production defaults"
    kubectl apply -f ../environments/production/config.yaml -n $NAMESPACE
fi

echo "Applying Secrets..."
kubectl apply -f ../secrets/app-secrets.yaml -n $NAMESPACE

echo "Applying Deployments..."
kubectl apply -f ../auth-service-deployment.yaml -n $NAMESPACE
kubectl apply -f ../tasks-service-deployment.yaml -n $NAMESPACE
kubectl apply -f ../collaborator-service-deployment.yaml -n $NAMESPACE
kubectl apply -f ../logs-service-deployment.yaml -n $NAMESPACE

echo "Applying other resources..."
if [ -f "../namespace.yaml" ]; then
    kubectl apply -f ../namespace.yaml
fi

if [ -f "../ingress.yaml" ]; then
    kubectl apply -f ../ingress.yaml -n $NAMESPACE
fi

echo "Deployment completed!"
echo "To check status, run:"
echo "  kubectl get pods -n $NAMESPACE"
echo "  kubectl get services -n $NAMESPACE"
echo "  kubectl get configmaps -n $NAMESPACE"
echo "  kubectl get secrets -n $NAMESPACE"
