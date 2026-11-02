# ServiceFlow — Architectural Decisions & Trade-Offs (ADR)

## ADR 01: Multi-Tenant Identity & Authentication Architecture (C3)
- **Status:** Implemented & Verified
- **Context:** In Iranian hospitality operations, staff (e.g. baristas, waiters) frequently work at different cafés or move between establishments across seasons. Enforcing a globally unique email across distinct restaurant organizations breaks real-world tenant isolation and prevents legitimate users from registering under different venues.
- **Decision:** Require `restaurant_slug` alongside normalized email and password during login (`POST /api/v1/auth/login`).
  1. The backend resolves the tenant `Restaurant` by slug.
  2. Queries `User` filtered by `restaurant_id == restaurant.id` and lowercase email.
  3. Validates password and active status.
  4. Encodes `sub` (user_id), `tenant_id` (restaurant_id), `role`, `branch_id`, and `station_id` into the JWT.
- **Trade-offs & Alternatives:**
  - *Alternative:* Globally unique email. Rejected because it creates cross-tenant account enumeration vulnerabilities and prevents multi-restaurant employment.
  - *Consequence:* Frontend and API clients must provide the restaurant slug upon login.

---

## ADR 02: Transactional Branch-Scoped Daily Order Numbering (H2)
- **Status:** Implemented & Verified
- **Context:** Iranian café staff rely on simple, human-readable daily order numbers (e.g., #1, #2, #104) called out to baristas or customers. A simple `COUNT(*)` suffers from race conditions under concurrent submissions, and PostgreSQL sequences do not automatically reset per-day per-branch without complex external cron jobs.
- **Decision:** Implement a transactional counter table `branch_daily_counters` with composite primary key `(restaurant_id, branch_id, counter_date)`.
  1. Atomic increment uses PostgreSQL `INSERT ... ON CONFLICT (restaurant_id, branch_id, counter_date) DO UPDATE SET last_number = branch_daily_counters.last_number + 1, updated_at = NOW() RETURNING last_number`.
  2. The database enforces uniqueness via `CONSTRAINT uq_orders_branch_daily_number UNIQUE (restaurant_id, branch_id, order_date, order_number)`.
- **Trade-offs & Alternatives:**
  - *Alternative:* In-memory atomic integer or redis lock. Rejected because multi-worker uvicorn processes or container restarts cause sequence collisions.
  - *Alternative:* Global UUID or sequence. Rejected because kitchen tickets need branch-local 1-to-N numbering each day.
  - *Consequence:* The counter row is locked for the duration of the order creation transaction (~10-20ms), which provides guaranteed uniqueness with zero gaps and minimal contention overhead.

---

## ADR 03: Parent Order Status Invariants & Hierarchical Row Locking (H1)
- **Status:** Implemented & Verified
- **Context:** An order contains multiple items prepared by different stations (e.g., Barista, Brew Bar, Cold Bar, Hot Kitchen). If kitchen staff complete an item after a waiter has already marked the parent order `SERVED` or `CANCELLED`, naive parent derivation logic could regress the parent order back to `READY_FOR_SERVICE` or `IN_PROGRESS`. Furthermore, concurrent transactions modifying different items or serving the order could cause deadlocks or race conditions.
- **Decision:**
  1. **Serving Invariant:** `SERVED` and `CANCELLED` are terminal parent states. A conditional SQL update enforces:
     `UPDATE orders SET status = :new_status, updated_at = NOW() WHERE id = :order_id AND status NOT IN ('SERVED', 'CANCELLED')`
  2. **Decoupled Item Versioning:** Modifying an item increment's that item's `version` independently. Parent order status recalculation is atomic and does not conflict with items being added or changed at other stations.
  3. **Strict Locking Hierarchy:** To avoid deadlocks:
     - Resource order: `orders` -> `order_items` -> `order_status_history`.
     - In item state updates: Lock single target item row (`SELECT ... FOR UPDATE OF order_items`), apply transition, derive parent order status, and execute conditional update on `orders`.
     - In order service: Lock parent order first (`SELECT ... FOR UPDATE OF orders`), then verify item states (`FOR UPDATE OF order_items`).

---

## ADR 04: Authorization Fail-Closed Enforcement (C1 & C2)
- **Status:** Implemented & Verified
- **Context:** Role-based access control must prevent horizontal privilege escalation across branches or stations. A waiter at Branch A must not view or mutate orders at Branch B. Waiters must not mutate kitchen statuses. Kitchen staff must only update items assigned to their specific station and branch.
- **Decision:**
  1. Centralized dependency helpers `verify_branch_scope` and `verify_kitchen_station_scope` execute in the service/dependency layer.
  2. **Fail-Closed Rule:** If a user has `RoleEnum.WAITER` or `RoleEnum.KITCHEN` without a valid `branch_id`, access is immediately denied (`403 Forbidden`). If kitchen staff lack a valid `station_id`, item mutation is immediately denied.
  3. **Station Scoping:** Kitchen staff can only update items matching their authorized `station_id` and `branch_id`.
  4. **Manager Scope:** Managers have tenant-wide branch access within their tenant, but cannot access branches of another tenant (`404 Not Found` without information leakage).
- **Trade-offs:** Client-supplied branch headers are strictly ignored; authorization relies solely on the validated JWT claims and database checks.

---

## ADR 05: AI Analyst Architecture & Multi-Layered Prompt Hardening (H3)
- **Status:** Implemented & Verified
- **Context:** The AI operations analyst summarizes queue bottlenecks and delayed items. Feeding unvalidated free-form user input or granting direct SQL access invites prompt injection, system prompt leakage, and unauthorized data exfiltration.
- **Decision:**
  1. **Closed Analytical Intents:** The API accepts an enumerated intent (`AnalyticalIntentEnum`: `BOTTLENECK_STATION`, `DELAYED_ITEMS`, `BRANCH_COMPARISON`, `SHIFT_SUMMARY`).
  2. **Deterministic Evidence Aggregation:** Operational metrics (average preparation delays, active ticket counts, backlog per station) are computed deterministically via PostgreSQL queries in `OrderService` before any LLM interaction. No SQL access or tool execution is provided to the LLM.
  3. **PII Elimination & Sanitization:** Customer notes, names, and phone numbers are stripped. Delimiters (`<system>`, `</user>`, etc.) are escaped. Multi-lingual injection patterns (English and Persian jailbreaks) are sanitized.
  4. **Fail-Safe Deterministic Fallback:** If the external LLM provider times out, returns malformed JSON, or the API key is not configured, the service generates a structured deterministic operational summary directly from the calculated metrics. Core restaurant operations never depend on LLM availability.

---

## ADR 06: Production Operational Security & CORS (H4 & M5)
- **Status:** Implemented & Verified
- **Context:** Hardcoded fallback JWT secrets in production or wildcard CORS (`*`) with credentials create severe security risks.
- **Decision:**
  1. Pydantic model validator `validate_production_security` halts application startup if `ENVIRONMENT=production` and `SECRET_KEY` is missing, default, or under 32 characters.
  2. CORS origins are explicitly whitelisted (e.g., `http://localhost:5173`, `http://127.0.0.1:5173`). Wildcards are prohibited with credentials.
  3. Request ID middleware generates and propagates `X-Request-ID` across all HTTP logs and responses.
