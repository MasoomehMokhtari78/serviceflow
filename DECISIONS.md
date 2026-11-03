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
- **Status:** Implemented (Deterministic Fallback & Mocks Verified; Live Provider Unverified)
- **Context:** The AI operations analyst summarizes queue bottlenecks and delayed items. Feeding unvalidated free-form user input or granting direct SQL access invites prompt injection, system prompt leakage, and unauthorized data exfiltration.
- **Decision:**
  1. **Closed Analytical Intents:** The API accepts an enumerated intent (`AnalyticalIntentEnum`: `BOTTLENECK_STATION`, `DELAYED_ITEMS`, `BRANCH_COMPARISON`, `SHIFT_SUMMARY`).
  2. **Deterministic Evidence Aggregation:** Operational metrics (average preparation delays, active ticket counts, backlog per station) are computed deterministically via PostgreSQL queries in `MetricsService` before any LLM interaction. No SQL access or tool execution is provided to the LLM.
  3. **PII Elimination & Sanitization:** Customer notes, names, and phone numbers are stripped. Delimiters (`<system>`, `</user>`, etc.) are escaped. Multi-lingual injection patterns (English and Persian jailbreaks) are sanitized.
  4. **Fail-Safe Deterministic Fallback:** If the external LLM provider times out, returns an error, or the API key is not configured, the service generates a structured deterministic operational summary directly from the calculated metrics. Core restaurant operations never depend on LLM availability.

---

## ADR 06: Production Operational Security & CORS (H4 & M5)
- **Status:** Implemented & Verified
- **Context:** Hardcoded fallback JWT secrets in production or wildcard CORS (`*`) with credentials create severe security risks.
- **Decision:**
  1. Pydantic model validator `validate_production_security` halts application startup if `ENVIRONMENT=production` and `SECRET_KEY` is missing, default, or under 32 characters.
  2. CORS origins are explicitly whitelisted (e.g., `http://localhost:5173`, `http://127.0.0.1:5173`). Wildcards are prohibited with credentials.
  3. Request ID middleware generates and propagates `X-Request-ID` across all HTTP logs and responses.

## ADR 07: Persian-First RTL Frontend Architecture & Resilient Polling
- **Status:** Implemented & Verified
- **Context:** Café floor staff (waiters and baristas) operate under noisy, high-pressure shift conditions on mobile/tablet devices. WebSockets or SSE would introduce connection lifecycle complexities and server state overhead.
- **Decision:**
  1. Built a touch-friendly, Persian-first RTL UI using React, TypeScript, Tailwind CSS, Lucide icons, and the Vazirmatn font.
  2. Implemented lightweight, resilient polling (5s for waiter active orders, 4s for kitchen KDS queues) with immediate refresh upon mutation.
  3. Integrated optimistic concurrency conflict handling: when a `409 Conflict` occurs (e.g. concurrent kitchen item status mutation or waiter serving), the UI surfaces a localized notification ("سفارش همزمان به‌روزرسانی شده بود؛ اطلاعات تجدید گردید") and transparently refetches state.
  4. Role-tailored experience: Waiters manage table orders and serving; Kitchen staff operate large touch action buttons on station tickets; Managers access operational KPI tables and deterministic AI analyst workflows.

---

## ADR 08: Optional Gemini Provider Integration with Deterministic Fallback as Assessment Default
- **Status:** Implemented (Local Mocks & Fallback Verified; Live Provider Unverified)
- **Context:** The technical assessment does not provide an external Gemini API key. Acquiring or configuring a personal/commercial third-party credential solely for a time-boxed technical assessment is neither requested nor required. The platform requires a verified demonstration path that remains fully operational offline without external API dependencies.
- **Decision:**
  1. **Provider Implemented but Optional:** The Gemini provider client is implemented in `app/ai/analyst.py` via `google-genai` (`gemini-2.5-flash`), with `Settings.GEMINI_API_KEY: str | None = None` marked optional. The application boots and functions normally without an API key.
  2. **Deterministic Fallback as Default:** When `GEMINI_API_KEY` is not configured, `AIAnalystService.analyze` routes immediately to `generate_deterministic_fallback`. This generates a structured, grounded Markdown operational report based on exact database facts computed in PostgreSQL.
  3. **Mocked Provider Test Strategy:** Unit tests (`test_h3_ai_analyst.py`) use `unittest.mock.patch` to verify provider invocation, exception handling, timeout fallbacks, and empty output handling without executing real network calls.
  4. **Strict Separation of Concerns:** Core restaurant workflows (waiter order-taking, kitchen KDS queue management, table status tracking, and manager KPI dashboards) run entirely on PostgreSQL with zero dependency on external AI services.
- **Alternatives Considered:**
  - *Obtain/configure a live Gemini API key:* Rejected because no key is provided for this assessment, and introducing external credential dependencies makes local assessment verification fragile.
  - *Remove Gemini integration entirely:* Rejected because demonstrating full-stack LLM provider architecture, structured evidence passing, and defensive prompt fencing is an explicit requirement.
  - *Make provider mandatory (fail on startup if key missing):* Rejected because restaurant operations must never halt due to external AI provider outages or missing credentials.
- **Trade-offs & Known Limitations:**
  - Live Gemini API requests have not been executed or verified against Google's servers.
  - Real provider latency, network timeouts, live rate limiting, and real token costs are unverified.
  - The deterministic fallback produces structured rule-based reports rather than natural-language synthesis, but ensures 100% availability, zero cost, and zero hallucination.
- **Revisit When:** A valid production API key, billing account, and secure secret manager are provisioned in a dedicated production deployment environment.

---

## Architectural Decisions We Now Think Were Wrong or Would Revisit

Per the assessment brief requirement (*"Include at least two you now think were wrong or would revisit"*), the following architectural choices were made during the initial implementation that we now evaluate critically:

### 1. Revisit Decision #1: Permitting Optional Freeform `question` Input in AI Analyst (ADR 05)
- **The Original Choice:** We permitted an optional freeform `question: Optional[str]` field (capped at 200 characters) in `AIAnalystQuery` alongside the four closed analytical intents, attempting to sanitize it with character stripping and 8 regex jailbreak patterns before passing it as `Manager Context`.
- **Why We Now Think It Was Wrong:**
  1. *Sanitization Fragility:* As demonstrated during our adversarial security audit, regex-based sanitization and character stripping are inherently porous. Subtle variations in phrasing (both English and Persian) bypass the 8 regex patterns completely and enter the prompt as instructions, violating the prompt fencing principle.
  2. *Architectural Contradiction:* For a safety-critical restaurant operations platform, the four closed analytical intents (`SHIFT_SUMMARY`, `BOTTLENECK_STATION`, `DELAYED_ITEMS`, `BRANCH_COMPARISON`) are fully expressive and deterministic. Adding freeform text introduced an unneeded prompt-injection vector without adding commensurate operational value.
- **How We Would Revisit It:** Completely remove `question` from `AIAnalystQuery` and the frontend UI. The manager selects an intent, and the backend generates a strictly bounded prompt consisting *only* of system safety rules, pre-aggregated database JSON, and the fixed intent definition.

### 2. Revisit Decision #2: High-Frequency Client HTTP Polling vs. Server-Sent Events (ADR 07)
- **The Original Choice:** We chose client-side interval polling (4 seconds for kitchen KDS queues, 5 seconds for waiter active orders) with immediate refetch on mutations.
- **Why We Now Think It Was Wrong:**
  1. *Database & Network Overload:* While polling avoided WebSocket connection lifecycle complexities during the 6-hour time box, in a 4-branch café group with 4 stations per branch and 8 waiter tablets (48 active devices), 4-second polling generates ~720 HTTP requests per minute even when no orders are being placed. This places needless query load on PostgreSQL.
  2. *Latency Lag:* Kitchen staff must wait up to 4 seconds to see an incoming order chit appear on their station screen, which is noticeable during peak breakfast/rush hours.
- **How We Would Revisit It:** Implement lightweight **Server-Sent Events (SSE)** via FastAPI and a Redis Pub/Sub channel (or PostgreSQL `LISTEN`/`NOTIFY`). Active devices hold an open read-only HTTP stream and receive ticket updates instantaneously with zero database polling, falling back to 15-second polling only if the SSE stream drops.

### 3. Revisit Decision #3: Coupling Single-Branch Scoping to Multi-Branch Metric Aggregation
- **The Original Choice:** In `MetricsService.get_operational_metrics`, we scoped the base `orders` query by `branch_id` if provided in the query parameters, and then reused that same `orders` list to calculate `branch_comparison`.
- **Why We Now Think It Was Wrong:** When a manager selects a branch (e.g. Enghelab), `orders` is filtered down to only Enghelab. When `branch_comparison` subsequently loops over all branches of the café group, it evaluates `b_orders = [o for o in orders if o.branch_id == b.id]`, resulting in 0 orders and 0% delay for Sanaee, Tajrish, and Shahrak Gharb.
- **How We Would Revisit It:** Decouple branch comparison from single-branch station metrics: station queues and delayed dishes should filter by `branch_id`, while branch comparison queries the entire tenant scope (`Order.restaurant_id == restaurant_id`).
