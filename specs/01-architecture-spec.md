# WB-Profit-Engine — System Architecture Specification (Spec-Kit 01)

## 1. Architectural Vision & Clean Architecture Boundaries

`WB-Profit-Engine` is a high-availability, multi-container backend system engineered for **Wildberries (WB) Sellers** to compute exact unit-economics, marketplace deductions, net profit, and target selling prices required for **100% Return on Investment (ROI)** prior to listing SKUs.

The backend enforces strict **Clean / Onion Architecture** across four isolated concentric layers inside `app/`:

```text
+-------------------------------------------------------------------+
|                   Presentation Layer (FastAPI)                    |
|         app/presentation/{api_router.py, schemas.py}              |
+---------------------------------+---------------------------------+
                                  | Depends on
                                  v
+-------------------------------------------------------------------+
|                 Application Layer (Use Cases)                     |
|                  app/application/use_cases.py                     |
+---------------------------------+---------------------------------+
                                  | Orchestrates
                +-----------------+-----------------+
                |                                   |
                v                                   v
+-------------------------------+   +-------------------------------+
|    Domain Layer (Pure Math)   |   |     Infrastructure Layer      |
|  app/domain/{entities.py,     |   |  app/infrastructure/{models,  |
|        calculator.py}         |   |  database,repositories,redis, |
|  Zero external dependencies   |   |          wb_client}           |
+-------------------------------+   +-------------------------------+
```

### Layer Contracts
1. **Domain Layer (`app/domain/`)**:
   - Contains pure Python dataclasses (`entities.py`) and deterministic mathematical formulas (`calculator.py`).
   - Zero framework imports (no FastAPI, SQLAlchemy, Redis, or HTTPX).
   - 100% unit-testable in isolation.
2. **Application Layer (`app/application/use_cases.py`)**:
   - Orchestrates the business workflow: checks Redis cache (`wb:product:{nm_id}`), fetches live Wildberries card metadata via `WBClient` on cache miss, queries category commission and warehouse coefficient from PostgreSQL (`wb_tariffs`), executes the `UnitEconomicsCalculator`, persists calculation audit logs to `calculations`, and returns structured domain output.
3. **Infrastructure Layer (`app/infrastructure/`)**:
   - Implements persistence (`SQLAlchemy 2.0 AsyncEngine` + `asyncpg`), caching (`redis.asyncio`), and external HTTP resilience (`httpx.AsyncClient` querying Wildberries public card v2 endpoints with deterministic fallback when rate-limited).
4. **Presentation Layer (`app/presentation/`)**:
   - Exposes RESTful OpenAPI v1 routes (`/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/wb/calculate`, `/api/v1/wb/history`, `/api/v1/health`) with strict Pydantic v2 DTO validation and JWT Bearer authentication.

---

## 2. Mathematical Specification (Wildberries Unit-Economics Engine)

Given:
- Package dimensions $L, W, H$ (in cm)
- Selling Price $P$ (in RUB)
- Full Cost of Goods Sold $\text{COGS}$ (in RUB)
- Category Commission $K_{\text{wb}}$ (default $0.19$) and Acquiring $K_{\text{acq}} = 0.015$
- Warehouse Coefficient $C_{\text{wh}}$ (default $1.7$)
- Reverse Logistics per return $L_{\text{return}} = 50.0\text{ RUB}$

### Step-by-Step Formulas
1. **Volume in Liters ($V$)**:
   $$V = \frac{L \times W \times H}{1000}$$
   *(Fallback: $V = 2.0\text{ L}$ when dimensions are absent).*
2. **Commission & Acquiring ($K_{\text{total}}$)**:
   $$K_{\text{total}} = K_{\text{wb}} + K_{\text{acq}}$$
   $$\text{Commission Fee} = P \times K_{\text{total}}$$
3. **Forward Logistics ($L_{\text{forward}}$)**:
   $$L_{\text{base}} = \begin{cases} 46.0 & \text{if } V \le 1.0 \\ 46.0 + (V - 1.0) \times 14.0 & \text{if } V > 1.0 \end{cases}$$
   $$L_{\text{forward}} = L_{\text{base}} \times C_{\text{wh}}$$
4. **Effective Logistics Across 3 Buyout Rate ($B$) Scenarios**:
   For $B \in \{0.90\text{ (Optimistic)}, 0.75\text{ (Realistic)}, 0.50\text{ (Pessimistic)}\}$:
   $$L_{\text{effective}}(B) = \frac{L_{\text{forward}} + (1 - B) \times L_{\text{return}}}{B}$$
   $$\text{Return Logistics Burden}(B) = L_{\text{effective}}(B) - L_{\text{forward}}$$
5. **30-Day Storage ($S_{\text{storage}}$)**:
   $$S_{\text{storage}} = V \times 0.14 \times 30$$
6. **Total WB Deductions & Net Profit**:
   $$D_{\text{wb}}(B) = \text{Commission Fee} + L_{\text{effective}}(B) + S_{\text{storage}}$$
   $$\text{Payout to Seller}(B) = P - D_{\text{wb}}(B)$$
   $$\text{Net Profit}(B) = P - D_{\text{wb}}(B) - \text{COGS}$$
7. **Target Price for 100% ROI ($P_{\text{target}}$ where $\text{Net Profit} = \text{COGS}$)**:
   $$P_{\text{target}}(B) = \frac{2 \times \text{COGS} + L_{\text{effective}}(B) + S_{\text{storage}}}{1 - K_{\text{total}}}$$

---

## 3. Five-Container Zero-Trust Network Topology

```text
                        [ External Client / CLI ]
                                   |
                               Port 80:80
                                   v
+------------------------ frontend_net (bridge) ------------------------+
|                                                                       |
|                          +---------------+                            |
|                          |   nginx-lb    |                            |
|                          | (1.25-alpine) |                            |
|                          +-------+-------+                            |
|                                  | Round-Robin Upstream               |
|                    +-------------+-------------+                      |
|                    |                           |                      |
|                    v                           v                      |
|            +---------------+           +---------------+              |
|            |   wb-api-1    |           |   wb-api-2    |              |
|            | (non-root)    |           | (non-root)    |              |
|            +-------+-------+           +-------+-------+              |
|                    |                           |                      |
+--------------------+---------------------------+----------------------+
                     |                           |
+--------------------+---------------------------+----------------------+
|                    |                           |                      |
|                    +-------------+-------------+                      |
|                                  |                                    |
|                    +-------------+-------------+                      |
|                    |                           |                      |
|                    v                           v                      |
|            +---------------+           +---------------+              |
|            |  postgres-db  |           |  redis-cache  |              |
|            |  (16-alpine)  |           |  (7-alpine)   |              |
|            +---------------+           +---------------+              |
|                                                                       |
+------------------- backend_net (internal: true) ----------------------+
```
