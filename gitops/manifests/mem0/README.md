# Mem0 Kubernetes Deployment

mem0 does not currently publish official Docker images, so we need to build them ourselves.

## Building Docker Images

```bash
cd ~/ghq/github.com/mem0ai/mem0


# Build API image
podman build --platform linux/amd64 -f server/Dockerfile \
  -t registry.local.timmybtech.com/mem0-api:latest server/

# Build Dashboard image
podman build --platform linux/amd64 -f server/dashboard/Dockerfile \
  -t registry.local.timmybtech.com/mem0-dashboard:latest server/dashboard/
```

## Pushing Images to Registry

```bash
# Push API image
podman push registry.local.timmybtech.com/mem0-api:latest

# Push Dashboard image
podman push registry.local.timmybtech.com/mem0-dashboard:latest
```
