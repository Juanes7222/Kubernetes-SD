# Kubernetes Environment Variables Management

This document describes the improved environment variable management system for the microservices project using Kubernetes ConfigMaps and Secrets.

## 📁 Structure

```
k8s/
├── configmaps/
│   ├── common-config.yaml          # Common settings shared across all services
│   ├── service-urls-config.yaml    # Inter-service communication URLs
│   └── service-ports-config.yaml   # Service port configurations
├── secrets/
│   └── app-secrets.yaml            # Sensitive data (JWT secrets, etc.)
├── environments/
│   ├── development/
│   │   └── config.yaml             # Development-specific settings
│   └── production/
│       └── config.yaml             # Production-specific settings
├── scripts/
│   ├── deploy-configs.sh           # Bash deployment script
│   └── deploy-configs.ps1          # PowerShell deployment script
└── [service-deployments].yaml     # Updated deployment files
```

## 🔧 Configuration Categories

### 1. Common Configuration (`configmaps/common-config.yaml`)
Contains settings used by all services:
- `ENVIRONMENT`: Current environment (production/development)
- `DEBUG`: Debug mode flag
- `HOST`: Server host binding
- `LOG_LEVEL`: Logging level
- `LOG_FORMAT`: Log message format
- `CORS_ORIGINS`: CORS allowed origins
- `FIREBASE_CRED_PATH`: Path to Firebase credentials

### 2. Service URLs (`configmaps/service-urls-config.yaml`)
Inter-service communication URLs:
- `AUTH_SERVICE_URL`: Authentication service endpoint
- `TASKS_SERVICE_URL`: Tasks service endpoint
- `COLLABORATOR_SERVICE_URL`: Collaborator service endpoint  
- `LOGS_SERVICE_URL`: Logs service endpoint
- `REACT_APP_*`: Frontend build-time environment variables

### 3. Service Ports (`configmaps/service-ports-config.yaml`)
Port configurations for each service:
- `AUTH_SERVICE_PORT`: Auth service port (8000)
- `TASKS_SERVICE_PORT`: Tasks service port (8001)
- `COLLABORATOR_SERVICE_PORT`: Collaborator service port (8002)
- `LOGS_SERVICE_PORT`: Logs service port (8003)

### 4. Application Secrets (`secrets/app-secrets.yaml`)
Sensitive configuration data:
- `SECRET_KEY`: JWT signing key (base64 encoded)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token expiration time (base64 encoded)
- Firebase credentials are in a separate secret

### 5. Environment-Specific Configuration
Override common settings per environment:
- **Development**: Debug enabled, localhost URLs, verbose logging
- **Production**: Debug disabled, internal service URLs, restricted CORS

## 🚀 Deployment

### Using PowerShell (Windows)
```powershell
cd k8s/scripts
./deploy-configs.ps1 production    # Deploy production environment
./deploy-configs.ps1 development   # Deploy development environment
```

### Using Bash (Linux/MacOS)
```bash
cd k8s/scripts
chmod +x deploy-configs.sh
./deploy-configs.sh production      # Deploy production environment  
./deploy-configs.sh development     # Deploy development environment
```

### Manual Deployment
```bash
# Apply configurations in order
kubectl apply -f k8s/configmaps/ -n microservices-app
kubectl apply -f k8s/secrets/ -n microservices-app
kubectl apply -f k8s/environments/production/ -n microservices-app  # or development
kubectl apply -f k8s/ -n microservices-app  # Apply deployments
```

## 🔍 Verification

Check that all resources are created:
```bash
kubectl get configmaps -n microservices-app
kubectl get secrets -n microservices-app
kubectl get pods -n microservices-app
```

View environment variables in a running pod:
```bash
kubectl exec -it <pod-name> -n microservices-app -- env | grep -E "(LOG_LEVEL|AUTH_SERVICE_URL|DEBUG)"
```

## 📝 How Services Use Environment Variables

Each service deployment now loads environment variables from multiple sources:

1. **Individual PORT env var**: Set directly in deployment
2. **Common ConfigMap**: Shared settings like logging, CORS
3. **Service URLs ConfigMap**: Inter-service communication
4. **Service Ports ConfigMap**: Port definitions
5. **Environment ConfigMap**: Environment-specific overrides
6. **App Secrets**: Sensitive JWT and authentication data
7. **Firebase Volume Mount**: Firebase credentials as files

### Order of Precedence
Later sources override earlier ones:
1. Common config
2. Service URLs config  
3. Service ports config
4. Environment-specific config (highest priority for non-secrets)
5. App secrets

## 🔐 Security Considerations

### Secrets Management
- **JWT Secret Key**: Stored as Kubernetes Secret, base64 encoded
- **Firebase Credentials**: Mounted as volume from Secret
- **Sensitive URLs**: Keep in Secrets if they contain credentials

### Base64 Encoding for Secrets
```bash
# Encode a value for use in secrets
echo -n "your-secret-value" | base64

# Decode to verify
echo "eW91ci1zZWNyZXQtdmFsdWU=" | base64 -d
```

## 🔄 Environment Management

### Switching Environments
To deploy different environments, use the appropriate config:
```bash
# Deploy development environment
kubectl apply -f k8s/environments/development/config.yaml -n microservices-app
kubectl rollout restart deployment -n microservices-app

# Deploy production environment  
kubectl apply -f k8s/environments/production/config.yaml -n microservices-app
kubectl rollout restart deployment -n microservices-app
```

### Adding New Environments
1. Create `k8s/environments/{env-name}/config.yaml`
2. Update deployment scripts to recognize the new environment
3. Deploy using scripts with the new environment name

## 🐛 Troubleshooting

### Common Issues

1. **ConfigMap not found**: Ensure all ConfigMaps are applied before deployments
2. **Secret decoding errors**: Verify base64 encoding of secret values  
3. **Missing environment variables**: Check that the ConfigMap exists and is correctly referenced
4. **Service communication failures**: Verify service URLs in `service-urls-config.yaml`

### Debug Commands
```bash
# Check ConfigMap contents
kubectl describe configmap common-config -n microservices-app

# Check Secret contents (encoded)
kubectl describe secret app-secrets -n microservices-app

# Check pod environment variables
kubectl exec -it <pod-name> -n microservices-app -- printenv

# Check pod logs for configuration issues
kubectl logs <pod-name> -n microservices-app
```

## 📚 Best Practices

1. **Separate Concerns**: Keep different types of configuration in separate ConfigMaps
2. **Environment Isolation**: Use different ConfigMaps for different environments
3. **Secret Security**: Always use Secrets for sensitive data, never ConfigMaps
4. **Documentation**: Keep this README updated when adding new environment variables
5. **Validation**: Test configuration changes in development before production
6. **Backup**: Keep secure backups of production secrets

## 🔄 Migration from Old System

The old single `configmap.yaml` has been replaced with this structured approach. Key changes:

- **Before**: Single ConfigMap with all variables mixed together
- **After**: Multiple ConfigMaps organized by purpose + proper Secrets
- **Before**: Hard-coded environment settings  
- **After**: Environment-specific overrides
- **Before**: Inconsistent secret handling
- **After**: Proper Secret resources with volume mounts

All services have been updated to use the new configuration structure while maintaining backward compatibility.
