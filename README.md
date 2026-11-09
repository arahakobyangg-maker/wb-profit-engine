# WB-Profit-Engine 🚀

[![Docker Image CI/CD](https://github.com/arahakobyangg-maker/wb-profit-engine/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/arahakobyangg-maker/wb-profit-engine/actions/workflows/docker-publish.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Clean_Architecture-009688.svg)
![Docker](https://img.shields.io/badge/Docker-5--Container_Cluster-2496ED.svg)
![Nginx](https://img.shields.io/badge/Nginx-Load_Balancer-009639.svg)

Production-grade, containerized backend engine for **Wildberries (WB) Sellers** to calculate unit-economics, marketplace deductions, net profit margins, and target selling prices for **100% ROI** across multiple buyout rate scenarios (`90%`, `75%`, `50%`).

---

## 🏗 System Architecture & Network Topology

The system is deployed as a **5-container cluster** orchestrated via Docker Compose across two isolated virtual bridge networks (`frontend_net` and internal-only `backend_net`):

~~text
                    [ Client / CLI (curl / Swagger) ]
                                    │
                               (Port 80)
                                    ▼
┌───────────────────── PUBLIC NETWORK (frontend_net) ─────────────────────┐
│                                                                         │
│                        [ 1. wb-nginx-lb (Nginx) ]                       │
│                   Reverse Proxy, Rate Limiter & Round-Robin LB          │
│                               /           \                             │
│                              ▼             ▼                            │
│               [ 2. wb-api-1 ]               [ 3. wb-api-2 ]             │
│             (FastAPI Replica #1)          (FastAPI Replica #2)          │
│                                                                         │
└───────────────────────┬───────────────────────────┬─────────────────────┘
                        │                           │
┌───────────────────────▼───────────────────────────▼─────────────────────┐
│                  INTERNAL NETWORK (backend_net: internal)               │
│                  (Zero external internet or host port access)           │
│                                                                         │
│         [ 4. wb-postgres-db ]               [ 5. wb-redis-cache ]       │
│       PostgreSQL 16 + pg_data Vol          Redis 7 (TTL: 3600s Cache)   │
└─────────────────────────────────────────────────────────────────────────┘
~~

### Clean Architecture Layers (`app/`)
- **`domain/`** — Pure mathematical unit-economics calculator & domain entities (zero framework dependencies).
- **`application/`** — Use-case orchestration (`CalculateUnitEconomicsUseCase`).
- **`infrastructure/`** — Async SQLAlchemy + `asyncpg` repositories, Redis cache wrapper, and resilient WB Card v2 HTTPX client.
- **`presentation/`** — FastAPI routers, JWT dependency injection, and Pydantic v2 schemas.

---

## 🔒 DevSecOps & Zero-Trust Security Controls

1. **Strict Network Isolation:** `postgres-db` (`5432`) and `redis-cache` (`6379`) reside exclusively on an `internal: true` Docker network with **zero host ports exposed**. Backend replicas (`8000`) are accessible only via the Nginx reverse proxy.
2. **Non-Root Execution:** Multi-stage `Dockerfile` runs the application under an unprivileged system account (`USER 10001:10001` / `appuser`).
3. **Immutable & Hardened Runtime:** API containers enforce `read_only: true` root filesystems, CPU/RAM resource limits, and automated container `HEALTHCHECK` probes.
4. **Zero Hardcoded Secrets:** Credentials and cryptographic JWT keys are injected strictly via `.env` (excluded via `.gitignore`).
5. **Authentication & Rate Limiting:** Passwords hashed via `bcrypt`; protected endpoints require `HS256` Bearer JWT tokens; Nginx enforces `10 req/s` rate limiting per IP.

---

## 📊 Business Logic & Wildberries Formulas

Given package dimensions ($L, W, H$ in cm), Selling Price ($P$), and Seller's full cost ($\text{COGS}$):

- **Volume ($V$):** $V = \frac{L \times W \times H}{1000}$ liters
- **Total Commission ($K_{\text{total}}$):** $K_{\text{wb}} + K_{\text{acq}}$ (Category tariff + `1.5%` acquiring)
- **Forward Logistics ($L_{\text{forward}}$):**
  - $V \le 1.0\text{L} \implies 46 \times C_{\text{wh}}$ RUB
  - $V > 1.0\text{L} \implies (46 + (V - 1) \times 14) \times C_{\text{wh}}$ RUB
- **Effective Logistics with Returns ($L_{\text{effective}}$ across Buyout Rate $B \in \{0.90, 0.75, 0.50\}$):**
  $$L_{\text{effective}}(B) = \frac{L_{\text{forward}} + (1 - B) \times 50}{B}$$
- **30-Day Storage ($S_{\text{storage}}$):** $V \times 0.14 \times 30$ RUB
- **Target Selling Price for 100% ROI ($\text{Net Profit} = \text{COGS}$):**
  $$P_{\text{target}} = \frac{2 \times \text{COGS} + L_{\text{effective}}(B) + S_{\text{storage}}}{1 - K_{\text{total}}}$$

---

## 🚀 Quick Start & Deployment

### 1. Clone & Configure Environment
~~bash
git clone https://github.com/arahakobyangg-maker/wb-profit-engine.git
cd wb-profit-engine

cp .env.example .env
sed -i "s/REPLACE_WITH_64_HEX_CHARACTER_CRYPTOGRAPHIC_SECRET/$(openssl rand -hex 32)/" .env
~~

### 2. Build & Launch the 5-Container Cluster
~~bash
docker compose build wb-api-1
docker compose up -d
docker compose ps
~~

### 3. Pull Pre-Built Image from GitHub Container Registry (GHCR)
Every push to `main` automatically builds and publishes the production image via GitHub Actions:
~~bash
docker pull ghcr.io/arahakobyangg-maker/wb-profit-engine:latest
~~

---

## 🧪 Verification & Load Balancing Demo

Run the automated CLI verification script to test Seller Registration, JWT Login, Unit-Economics Calculation, and **Round-Robin Load Balancing** across `wb-api-1` and `wb-api-2`:

~~bash
chmod +x scripts/cli_demo.sh
BASE_URL=http://localhost:80 ./scripts/cli_demo.sh
~~

### API Endpoints
| Method | Endpoint | Auth | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Public | Healthcheck & active container replica ID (`served_by_container`) |
| `POST` | `/api/v1/auth/register` | Public | Register a new WB Seller account |
| `POST` | `/api/v1/auth/login` | Public | Authenticate and obtain JWT Bearer token |
| `POST` | `/api/v1/wb/calculate` | Bearer JWT | Compute WB fees, net profit & 100% ROI price across 3 buyout scenarios |
| `GET` | `/api/v1/wb/history` | Bearer JWT | Retrieve seller's persisted calculation history from PostgreSQL |
| `GET` | `/docs` | Public | Interactive OpenAPI / Swagger UI documentation |
