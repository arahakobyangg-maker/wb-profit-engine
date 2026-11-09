# WB-Profit-Engine — Spec-Kit Multi-Agent Task Plan (Spec-Kit 02)

## Orchestration Protocol
Owned and reviewed by **Agent 0 (Principal Tech Lead & Spec-Kit Orchestrator)**. Every task below has explicit input dependencies, isolated file ownership, and deterministic acceptance criteria.

---

## Agent 0: Principal Tech Lead & Spec-Kit Orchestrator
- **Owned Artifacts**:
  - `specs/01-architecture-spec.md` (`specs/architecture.md`)
  - `specs/02-agent-task-plan.md` (`specs/tasks.md`)
- **Sub-Tasks**:
  - `[TASK-001]` Define Clean Architecture layer boundaries (`domain`, `application`, `infrastructure`, `presentation`, `core`).
  - `[TASK-002]` Audit mathematical formulas for Wildberries forward/reverse logistics, storage, net margin, and 100% ROI target pricing.
  - `[TASK-003]` Verify zero-trust network isolation (`frontend_net` vs `backend_net`) and container hostname propagation (`served_by_container`).

---

## Agent 1: Senior Backend Architect (Python / FastAPI / Clean Architecture)
- **Owned Artifacts**:
  - `requirements.txt`
  - `app/core/config.py`, `app/core/security.py`
  - `app/domain/entities.py`, `app/domain/calculator.py`
  - `app/application/use_cases.py`
  - `app/infrastructure/database.py`, `app/infrastructure/models.py`, `app/infrastructure/repositories.py`, `app/infrastructure/redis_cache.py`, `app/infrastructure/wb_client.py`
  - `app/presentation/schemas.py`, `app/presentation/api_router.py`
  - `app/main.py`
- **Sub-Tasks**:
  - `[TASK-101]` **Core Config & Security**: Implement Pydantic `BaseSettings` reading `.env` variables and `passlib[bcrypt]` + `PyJWT` token generation/verification.
  - `[TASK-102]` **Pure Domain Engine**: Implement `ProductMetadata`, `ScenarioBreakdown`, and `UnitEconomicsCalculator` in `app/domain/` with 3 buyout scenarios ($B \in \{0.90, 0.75, 0.50\}$).
  - `[TASK-103]` **Async Persistence & Seeding**: Configure `SQLAlchemy` async engine with `asyncpg`, define ORM models (`UserModel`, `WBTariffModel`, `CalculationModel`), and seed default category commissions on startup.
  - `[TASK-104]` **Redis Cache & Resilient WB Client**: Implement `RedisCache` (`TTL = 3600s` on `wb:product:{nm_id}`) and `WBClient` querying `card.wb.ru/cards/v2/detail` with automatic basket/fallback resolution.
  - `[TASK-105]` **Application Use Cases & FastAPI Presentation**: Wire `CalculateUnitEconomicsUseCase`, Auth endpoints, History endpoint, Healthcheck endpoint, and `os.getenv("HOSTNAME")` replica telemetry.

---

## Agent 2: Senior DevOps & CI/CD Engineer (Docker / Git / GitHub Actions / GHCR)
- **Owned Artifacts**:
  - `Dockerfile`
  - `docker-compose.yml`
  - `.github/workflows/docker-publish.yml`
  - `scripts/cli_demo.sh`
  - `.gitignore`
- **Sub-Tasks**:
  - `[TASK-201]` **Multi-Stage Dockerfile**: Build slim Python 3.12 production image with virtual environment isolation and non-root execution (`appuser`, UID 10001).
  - `[TASK-202]` **5-Container Docker Compose**: Orchestrate `nginx-lb`, `wb-api-1`, `wb-api-2`, `postgres-db`, and `redis-cache` with healthcheck-gated startup (`service_healthy`).
  - `[TASK-203]` **GHCR Continuous Delivery Pipeline**: Configure GitHub Actions workflow using `docker/login-action@v3`, `docker/metadata-action@v5`, and `docker/build-push-action@v5` to publish `ghcr.io/${{ github.repository }}:latest` on every push to `main`.
  - `[TASK-204]` **Automated CLI Verification Script**: Write `scripts/cli_demo.sh` demonstrating end-to-end user registration, JWT login, unit-economics calculation, and round-robin load balancer proof across `wb-api-1` and `wb-api-2`.

---

## Agent 3: Senior System & Network Administrator (Nginx / Linux / High Availability)
- **Owned Artifacts**:
  - `nginx/nginx.conf`
- **Sub-Tasks**:
  - `[TASK-301]` **Round-Robin Upstream Pool**: Configure `upstream wb_backend` pointing to `wb-api-1:8000` and `wb-api-2:8000` with `max_fails=3` and `fail_timeout=15s`.
  - `[TASK-302]` **Rate Limiting & Proxy Hardening**: Configure `limit_req_zone` (`10r/s` with `burst=20 nodelay`), security headers, and upstream failure failover (`proxy_next_upstream`).

---

## Agent 4: Senior DevSecOps / Security Auditor
- **Owned Artifacts**:
  - `.env.example`
  - Security constraints across `Dockerfile`, `docker-compose.yml`, and `nginx/nginx.conf`
- **Sub-Tasks**:
  - `[TASK-401]` **Network Segmentation**: Enforce `frontend_net` (bridge) for Nginx-to-API traffic and `backend_net` (`internal: true`) isolating PostgreSQL and Redis from the host and public internet.
  - `[TASK-402]` **Container Hardening**: Enforce `USER appuser`, `no-new-privileges:true`, zero host ports on `wb-api-1`, `wb-api-2`, `postgres-db`, and `redis-cache`, plus CPU/Memory limits.
  - `[TASK-403]` **Secret Hygiene**: Ensure zero hardcoded credentials in source files and document required runtime secrets in `.env.example`.
