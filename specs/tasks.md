# WB-Profit-Engine — Spec-Kit Task Breakdown Mirror
See `specs/02-agent-task-plan.md` for the detailed agent task allocation.

- **Agent 0 (Principal Tech Lead)**: Architecture specification, mathematical verification, integration sign-off.
- **Agent 1 (Senior Backend Architect)**: FastAPI Clean Architecture in `app/`, SQLAlchemy/AsyncPG, Redis cache, WB API client, and Unit-Economics calculator.
- **Agent 2 (Senior DevOps Engineer)**: Multi-stage `Dockerfile`, `docker-compose.yml`, `.github/workflows/docker-publish.yml`, `scripts/cli_demo.sh`.
- **Agent 3 (Senior SysAdmin)**: `nginx/nginx.conf` Round-Robin Load Balancer, upstream failover, and rate limiting.
- **Agent 4 (Senior DevSecOps Auditor)**: Non-root `appuser`, internal `backend_net`, zero exposed DB/API ports, `.env.example`.
