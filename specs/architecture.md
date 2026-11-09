# WB-Profit-Engine — Spec-Kit Architecture Mirror
See `specs/01-architecture-spec.md` for the full system specification.

- **Pattern**: Clean / Layered Architecture (`domain`, `application`, `infrastructure`, `presentation`, `core`)
- **Topology**: 5-Container Zero-Trust Cluster (`nginx-lb`, `wb-api-1`, `wb-api-2`, `postgres-db`, `redis-cache`)
- **Networks**: `frontend_net` (bridge) and `backend_net` (`internal: true`)
- **Registry**: `ghcr.io/<github_username>/wb-profit-engine:latest`
