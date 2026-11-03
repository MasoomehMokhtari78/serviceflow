# AI Usage & Verification Log

## 1. Overview & Verification Methodology
During Phase 2 implementation and verification, AI coding assistance was utilized under an adversarial verification framework. No AI-generated code or test result was assumed correct without independent execution against a live PostgreSQL 16 database.

## 2. Tools & Models Used
- **Assistant:** Antigravity (Google DeepMind Advanced Agentic Coding)
- **Database Engine:** PostgreSQL 16 (running via Docker Compose on port 5432)
- **Python Runtime:** Python 3.14.7 / FastAPI 0.134.0 / SQLAlchemy 2.0.48 / Alembic 1.18.3 / Pytest 9.2.0

## 3. Findings Addressed from Adversarial Engineering Review
1. **C1 — Branch Authorization on Order Retrieval:**
   - *Review finding:* Waiters could retrieve orders across different branches if they guessed UUIDs; client-supplied branch headers were weakly verified.
   - *Verification & Fix:* Implemented `verify_branch_scope` with fail-closed semantics. Unassigned staff fail immediately with 403. Tested 6 branch boundary cases.
2. **C2 — Branch & Station Authorization on Item Mutations:**
   - *Review finding:* Waiters could trigger kitchen mutations; kitchen staff could update items outside their assigned station or branch.
   - *Verification & Fix:* Implemented `verify_kitchen_station_scope`. Waiters are strictly rejected from updating item status. Kitchen staff are scoped to their branch and assigned station. Tested 7 permission matrix scenarios.
3. **C3 — Tenant-Aware Login:**
   - *Review finding:* Global email uniqueness violated multi-tenant requirements; duplicate emails in different restaurants could collide.
   - *Verification & Fix:* Required `restaurant_slug` in `LoginRequest`. Queries user scoped to `restaurant_id`. Verified duplicate email `duplicate@cafegroup.ir` in two distinct restaurants authenticating independently with different credentials.
4. **H1 — Parent Order Status Race Condition:**
   - *Review finding:* Concurrent item status transitions could regress a `SERVED` or `CANCELLED` parent order.
   - *Verification & Fix:* Added conditional SQL update `WHERE status NOT IN ('SERVED', 'CANCELLED')`. Documented locking order (`orders` -> `order_items` -> `order_status_history`). Verified via concurrent race test.
5. **H2 — Daily Order Number Generation:**
   - *Review finding:* Simple count-based order numbering generated race conditions and collisions under concurrency.
   - *Verification & Fix:* Implemented PostgreSQL atomic upsert in `branch_daily_counters` with database uniqueness constraint `uq_orders_branch_daily_number`. Verified with 10 concurrent threads generating sequential numbers without collision.
6. **H3 — AI Analyst Hardening:**
   - *Review finding:* Direct user prompt concatenation invited prompt injection and LLM hallucination.
   - *Verification & Fix:* Constrained input to `AnalyticalIntentEnum`, pre-aggregated deterministic operational metrics, sanitized multi-lingual injection attempts (Persian and English), and implemented deterministic fallback for timeouts/errors.
7. **H4 & M5 — Production Security & CORS:**
   - *Review finding:* Insecure secret fallback and wildcard CORS permitted credential leakage.
   - *Verification & Fix:* Enforced production startup validator requiring strong secrets (>=32 chars); replaced CORS wildcard with explicit origin list; added `X-Request-ID` tracing middleware.

## 4. Verification & Test Execution

### 4.1 Verified Locally
- **Unit & Integration Tests:** 51 passed in 16.18s against live PostgreSQL 16 (including E2E full workflow test `test_e2e_frontend_flow.py` and 9 dedicated AI analyst tests in `test_h3_ai_analyst.py`).
- **Missing-Key Behavior:** Verified that when `GEMINI_API_KEY` is absent or unset, the system immediately routes to the deterministic fallback engine without making network calls or throwing unhandled exceptions.
- **Deterministic Fallback Engine:** Verified that structured operational summaries and indisputable measured facts are computed directly from PostgreSQL metrics across all four analytical intents.
- **Mocked Provider Execution & Failures:** Verified that simulated provider timeouts (`TimeoutError`), HTTP/service errors (`RuntimeError`), and malformed/empty provider outputs safely trigger the deterministic fallback.
- **Migration Verification:** Downgraded to `base` and upgraded to `head` cleanly. Repeatable synthetic seed verified with exit code 0.
- **Frontend Build:** `npm run build` completed cleanly (0 errors, 2057 modules transformed).
- **Core Workflow Verification:** Complete order-to-service lifecycle verified:
  - Waiter login with `kariz-cafe` slug -> Table selection & order creation -> Order item queued to station.
  - Barista login -> KDS queue retrieval -> Item status transitions: PENDING -> PREPARING -> READY.
  - Waiter order review -> `is_ready_for_service` alert triggered -> Serving mutation executed -> Status: SERVED.
  - Manager login -> Operational metrics calculation & intent-driven AI operational analysis (executed via deterministic fallback).

### 4.2 Not Verified (Deliberate Assessment Scope Limitation)
- **Live Gemini API Execution:** The application has **not** executed requests against live Google Gemini endpoints because no `GEMINI_API_KEY` is configured or provided for this assessment.
- **Real Provider Latency & Reliability:** Network latency, connection timeouts, and provider uptime against live Google APIs remain unverified.
- **Token Consumption & Financial Cost:** Real token usage figures and billing impacts were not measured against live endpoints.

---

## 5. Gemini Integration Scope & Assessment Trade-Offs
- **Implementation Status:** The Gemini provider client is implemented in `app/ai/analyst.py` using the official `google-genai` SDK targeting model `gemini-2.5-flash`.
- **Deliberate Assessment Trade-Off:** In accordance with assessment instructions, no live API key was requested, obtained, or configured. The application was intentionally designed to run fully and reliably without external AI provider dependencies.
- **Testing Approach:** Provider interaction was verified exclusively through unit test mocks (`unittest.mock.patch`) simulating provider success, empty responses, timeouts, and network errors.
- **Operational Independence:** Core restaurant operations (ordering, kitchen KDS queues, table status, serving invariants) and manager KPI dashboard metrics run 100% on PostgreSQL. They do not depend on the AI provider. Fallback analysis provides structured operational reporting directly from database facts, though it does not provide live LLM natural language synthesis.

---

## 6. Reflective Evaluation (Part E Rubric Alignment)

### 6.1 Which tools and what for?
- **AI Coding Assistant:** Antigravity (Google DeepMind Advanced Agentic Coding with Gemini 3.8 Flash).
- **Primary Applications:** Rapid generation of repetitive boilerplate (Pydantic v2 schemas, SQLAlchemy relationship definitions, Alembic migration scaffolds), extensive synthetic Persian seed datasets, expanding the Pytest boundary condition matrix, and scaffolding touch-friendly Tailwind CSS layout components.

### 6.2 Where did AI save real time?
1. **Domain-Specific Synthetic Seed Generation:** Generating ~860 lines of authentic Iranian café data in `backend/seed.py` (realistic Persian beverage/food items, prices in integer Toman, culinary modifiers like "کم‌شیرین" and "با یخ اضافه", authentic staff names, and multi-branch table layouts across 4 Tehran locations) in minutes rather than hours.
2. **Exhaustive Permission Test Matrix Expansion:** Rapidly expanding authorization boundary test cases in `test_c1_c2_authorization.py` across 7 distinct permission scenarios (waiter cross-branch, kitchen cross-station, unassigned staff fail-closed).
3. **Initial Schema & Migration Scaffolding:** Scaffolding the initial SQLAlchemy entity models and Alembic migration scripts from domain specifications.

### 6.3 Where did AI produce something bad or incorrect?
1. **Broken Multi-Tenant Account Model:** The AI initially generated a conventional single-tenant `User` model with a global unique constraint on `email`. In the Iranian hospitality industry, floor staff frequently work across different cafés or move between establishments across seasons. A global unique email prevented legitimate multi-restaurant employment and introduced cross-tenant account enumeration vulnerabilities. We had to replace this with a composite tenant-scoped lookup requiring `restaurant_slug` + `email`.
2. **Race Condition in Parent Order Derivation:** The AI suggested naive logic where any item status change would automatically re-derive the parent order status based on all child items. Under concurrent conditions, if a kitchen worker marked an item ready *after* a waiter had already marked the parent order `SERVED`, the parent order would regress back to `READY_FOR_SERVICE`. We had to enforce an explicit conditional SQL invariant: `WHERE status NOT IN ('SERVED', 'CANCELLED')`.
3. **False Security Boundary via Delimiters:** The AI initially claimed that XML delimiter tags (`<operational_evidence>`) combined with 8 simple regex patterns constituted "complete prompt injection defense". Adversarial testing proved that subtle paraphrasing in English and Persian easily bypassed the regex filters.

### 6.4 One recommendation you rejected and why?
- **The AI's Recommendation:** The assistant suggested implementing a dynamic "Text-to-SQL" tool-calling agent where the LLM would translate manager inquiries into dynamic SQL queries executed against the PostgreSQL database.
- **Why We Decisively Rejected It:** Granting an external probabilistic LLM direct SQL generation capabilities against a multi-tenant database introduces catastrophic security and operational risks:
  1. *Cross-Tenant Leakage:* A prompt injection or subtle query bug could leak data across restaurant organizations.
  2. *Performance Destruction:* An unoptimized generated query (e.g. table scans across millions of historical items) could lock database tables during a busy dinner shift.
  3. *Unpredictability:* Restaurant managers need deterministic, auditable accounting facts, not probabilistic guesses.
  Instead, we insisted on **pre-aggregating deterministic metrics in PostgreSQL** via typed queries in `MetricsService` and passing only sanitized, bounded JSON evidence to a read-only explainer.

### 6.5 How was generated code verified?
- **Zero-Trust Verification Loop:** No AI-generated code or test result was trusted without execution against live PostgreSQL 16 running on port 5432.
- **Concurrency & Race Testing:** We verified high-concurrency operations using multithreaded test suites (`test_h1_h2_concurrency.py`), validating that 10 concurrent threads creating orders never produce duplicate order numbers and that concurrent item mutations trigger explicit `409 Conflict`.
- **Migration Verification:** Tested database migrations bi-directionally (`alembic downgrade base` followed by `alembic upgrade head`) and verified synthetic seeding with exit code 0.
- **End-to-End Workflow Validation:** Executed `test_e2e_frontend_flow.py`, proving the entire multi-role lifecycle (Waiter login $\rightarrow$ order creation $\rightarrow$ KDS queue $\rightarrow$ item preparation $\rightarrow$ waiter serving $\rightarrow$ manager analytics).

### 6.6 Which parts of the architecture were your own thinking?
1. **Composite Foreign Key Multi-Tenant Enforcement:** Enforcing `(restaurant_id, branch_id, id)` composite primary and foreign keys at the PostgreSQL schema layer. This makes cross-tenant data corruption physically impossible at the database engine level, independent of application code bugs.
2. **Decoupled Hierarchical Versioning:** Decoupling `Order.version` from `OrderItem.version` so that kitchen staff updating ticket statuses on busy stations never conflict with waiters adding new drinks or appetizers to the table order.
3. **Transactional Daily Counter Table:** Designing `branch_daily_counters` with PostgreSQL atomic upsert (`INSERT ... ON CONFLICT DO UPDATE`) to guarantee gapless, human-readable `#1, #2, #104` daily order numbers per branch without race conditions.
4. **Offline Deterministic Fallback Engine:** Decoupling operational intelligence from external third-party cloud APIs so that Iranian cafés—operating under frequent national internet disruptions or sanctions—retain 100% operational functionality and manager analytics offline.
