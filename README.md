# ServiceFlow

ServiceFlow is a multi-tenant, multi-branch café operations and shift intelligence platform engineered for high-volume Iranian hospitality environments. It coordinates table orders, real-time kitchen display systems (KDS), and shift operations across specialized preparation stations (Barista, Brew Bar, Cold Bar, Kitchen).

---

## Architecture & Technology Stack

- **Backend:** FastAPI (Python 3.14), SQLAlchemy 2 (ORM), Alembic (database migrations), Pydantic v2 (validation & schemas).
- **Database:** PostgreSQL 16 with composite foreign keys enforcing tenant and branch isolation at the database layer.
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide icons, Persian Vazirmatn typography with native RTL layouts.
- **Authentication:** Tenant-aware JWT authentication encoding `restaurant_id`, `branch_id`, `station_id`, and `role` (`manager`, `waiter`, `kitchen`).

---

## AI Operations Analyst

The platform includes a **read-only AI Operations Analyst** designed for restaurant shift managers. It explains operational performance and station bottlenecks using deterministic metrics calculated by PostgreSQL.

### Supported Analytical Intents
1. `SHIFT_SUMMARY`: High-level shift performance overview (order counts, active vs. served tickets, overall lead time).
2. `BOTTLENECK_STATION`: Workstation turnaround analysis, delay rates, and SLA adherence across KDS stations.
3. `DELAYED_ITEMS`: Identification of menu items consistently exceeding target preparation times.
4. `BRANCH_COMPARISON`: Comparative service lead times and delay percentages across branches.

### Grounded Facts vs. Narrative Analysis
- **Deterministic Metrics Engine:** All numbers, SLA turnaround times, and delay metrics are computed directly by PostgreSQL in `backend/app/services/metrics_service.py`. The LLM has no database access, cannot write queries, and cannot perform mutations.
- **Separation in UI:** The manager interface explicitly displays verified "Measured Facts" (with green verification indicators) separately from the generated narrative analysis.

### Implementation vs. Verification Status
- **Implemented in Codebase:** The Gemini provider integration is implemented in `backend/app/ai/analyst.py` using `google-genai` targeting `gemini-2.5-flash`.
- **Live Provider Execution Unverified:** **No live Gemini API key is configured or available for this assessment.** Consequently, live requests have not been executed or verified against Google's servers.
- **Provider Testing via Mocks:** Provider error handling, timeout recovery, and empty response handling are tested using unit test mocks (`unittest.mock.patch`), not live API requests.
- **Deterministic Fallback as Default:** If `GEMINI_API_KEY` is unset (the default for this assessment) or if the provider fails/times out, the system automatically routes to an offline deterministic rule engine. The application remains 100% functional without an API key. Core restaurant operations, waiter pads, kitchen queues, and manager KPI dashboards have zero dependency on external AI availability.

> **Note on Fallback vs. Live LLM:** The deterministic fallback generates structured, rule-based operational summaries based directly on database facts. It is not equivalent to live natural language synthesis from an LLM, but it provides guaranteed availability, zero operational cost, and zero hallucination risk.

---

## Configuration & Environment Variables

The application is designed to boot and run locally without requiring third-party AI credentials.

| Variable | Required | Default / Description |
|---|---|---|
| `DATABASE_URL` | Yes | `postgresql+psycopg2://serviceflow_user:serviceflow_password@localhost:5432/serviceflow_db` |
| `SECRET_KEY` | Yes (in prod) | JWT signing secret (minimum 32 characters enforced when `ENVIRONMENT=production`) |
| `ENVIRONMENT` | No | `development` (set to `production` for strict security checks) |
| `GEMINI_API_KEY` | **Optional** | **Not configured.** Optional for local development and demonstration. When omitted, the deterministic fallback engine is active. |
| `AI_REQUEST_TIMEOUT_SECONDS` | No | `6.0` (Provider call timeout budget) |

---

## Local Development & Setup

### 1. Database Infrastructure
Launch PostgreSQL 16 via Docker Compose:
```bash
docker compose up -d
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Testing & Verification Summary

### Verified Locally
- **Backend Test Suite:** 51 passing tests (`pytest -v tests`) executed against live PostgreSQL 16 on port 5432.
  - Multi-tenant boundary isolation and composite FK validation.
  - Role-based authorization (`waiter`, `kitchen`, `manager`).
  - Order-to-service state machine invariants and optimistic concurrency (`409 Conflict`).
  - Deterministic metrics calculations.
  - AI Analyst closed-intent validation, missing-key fallback, mocked timeout fallback, and mocked provider error recovery.
- **Frontend Build:** TypeScript compilation and Vite production build (`npm run build`) completed with 0 errors.
- **Offline Demonstration Path:** Complete waiter-to-kitchen-to-manager workflows demonstrated using the deterministic fallback engine.

### Not Verified (Assessment Scope Limitations)
- **Live Gemini API Execution:** No live Google Gemini API requests have been made or verified.
- **Real Provider Latency & Reliability:** Real-world network latency and provider uptime against Google APIs were not evaluated.
- **Token Costs & Quota Consumption:** Live API token usage and billing impact remain unmeasured.

