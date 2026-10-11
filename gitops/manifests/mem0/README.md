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

## MCP server (`mem0-mcp.yaml`)

The official mem0 MCP server and Claude Code plugin only talk to the hosted Platform API
(`api.mem0.ai`), so `mem0-mcp` is a thin proxy that maps MCP tool calls onto this server's
REST API. Extraction and embeddings still run in the mem0 API pod via LiteLLM, so everything
lands in the same pgvector store and shows up in the dashboard.

- Tools: `add_memory`, `search_memories`, `list_memories`, `get_memory`, `update_memory`,
  `delete_memory`, `memory_history` (no bulk delete on purpose)
- Default scope: `user_id=timmyb` (`MEM0_DEFAULT_USER_ID` in the `mem0-mcp` ConfigMap)
- Transport: streamable HTTP (stateless, JSON responses) at `/mcp`
- Auth: `Authorization: Bearer <MEM0_MCP_AUTH_TOKEN>` required on every request except `/healthz`
- No image build: the script lives in the ConfigMap; `python:3.13-slim` pip-installs pinned deps at startup

### One-time setup

1. Create an API key in the dashboard (Settings → API Keys).
2. Add to Vault at `secret/argocd`:
   - `MEM0_MCP_API_KEY` = the dashboard key
   - `MEM0_MCP_AUTH_TOKEN` = `openssl rand -hex 32`
3. Commit and let ArgoCD sync.

Endpoints:
- Internal: `https://mem0-mcp.local.timmybtech.com/mcp`
- Public (Cloudflare tunnel, `/mcp` only): `https://mem0-mcp.timmybtech.com/mcp`

### Clients

Claude Code:

```bash
claude mcp add --scope user --transport http mem0 https://mem0-mcp.local.timmybtech.com/mcp \
  --header "Authorization: Bearer $MEM0_MCP_AUTH_TOKEN"
```

Claude app (web/desktop/mobile): Settings → Connectors → Add custom connector →
URL `https://mem0-mcp.timmybtech.com/mcp`, with request-header auth `Authorization: Bearer <token>`
(header auth for custom connectors is in beta). Anthropic's connector traffic comes from
`160.79.104.0/21`, which can be allowlisted in a Cloudflare WAF rule for the public hostname.

Smoke test:

```bash
curl -s https://mem0-mcp.local.timmybtech.com/mcp \
  -H "Authorization: Bearer $MEM0_MCP_AUTH_TOKEN" \
  -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```
