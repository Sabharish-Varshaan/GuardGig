# GuardGig Backend

FastAPI backend for GuardGig's parametric insurance workflow.

This service handles:

- custom auth (phone/password + JWT)
- onboarding profile persistence
- policy creation with underwriting
- real-time trigger checks using weather and AQI APIs
- automated and manual claim creation
- fraud-rule based exclusions

## 1. Architecture and Logic (What It Does)

### 1.1 Core Business Flow

1. User registers and logs in via custom auth routes.
2. User submits onboarding profile.
3. Policy is created only if underwriting conditions pass.
4. Trigger engine evaluates live rain + AQI at coordinates.
5. Claim creation happens when trigger conditions are met.
6. Fraud/exclusion rules gate claim approval.
7. Payout amount is produced from trigger severity.

### 1.2 Trigger Engine Logic

Trigger checks use two external APIs:

- Open-Meteo for rain (`hourly=rain`)
- OpenWeather Air Pollution API for AQI (mapped to a numeric scale)

Severity rules:

- rain >= 100 -> full
- rain >= 60 -> partial
- aqi >= 400 -> full
- aqi >= 300 -> partial
- else -> no trigger

Returned trigger response shape from `/api/trigger/check`:

```json
{
   "rain": 0,
   "aqi": 0,
   "trigger": {
      "trigger": false,
      "type": null,
      "severity": null
   }
}
```

### 1.3 Claim Logic

`/api/claim/create` performs:

1. Active policy lookup
2. Waiting period enforcement
3. Max one claim/day enforcement
4. Fresh trigger evaluation (backend-side)
5. Exclusion checks (activity/location/fraud threshold)
6. Payout computation:
    - full -> 100% coverage amount
    - partial -> 30% coverage amount
7. Claim insertion with status and rule reason

Important: trigger type and severity are determined by backend trigger evaluation, not trusted from frontend input.

### 1.4 Underwriting Logic

At policy creation, `active_days` is derived from onboarding `created_at`:

- `active_days < 5` -> ineligible
- `5 <= active_days < 7` -> worker_tier = low
- `active_days >= 7` -> worker_tier = medium

Policy row stores:

- `eligibility_status`
- `worker_tier`
- `active_days`

### 1.5 Automated Claims

APScheduler runs hourly.

- Scans active policies
- Evaluates trigger conditions
- Applies exclusions/rules
- Creates approved claims when conditions pass

## 2. API Surface (High Level)

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/onboarding/me`
- `POST /api/onboarding`
- `POST /api/policy/create`
- `GET /api/policy/me`
- `POST /api/trigger/check`
- `POST /api/claim/create`
- `GET /api/claims/me`
- `POST /api/fraud/check`
- `GET /api/health`

## 3. Prerequisites

- Python 3.10+
- Supabase project
- OpenWeather API key

Optional for demo validation:

- `APP_DEMO_MODE=true` to enable demo behavior for policy, trigger, and claim flow

## 4. Setup (Step by Step)

1. Open terminal in backend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/backend
```

2. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create env file:

```bash
cp .env.example .env
```

5. Update `backend/.env`:

```env
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEMO_MODE=false
CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081

SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
SUPABASE_USERS_TABLE=app_users
SUPABASE_ONBOARDING_TABLE=onboarding_profiles
SUPABASE_POLICIES_TABLE=policies
SUPABASE_CLAIMS_TABLE=claims

OPENWEATHER_API_KEY=your_api_key_here

JWT_SECRET=<use-a-long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXP_MINUTES=60
REFRESH_TOKEN_EXP_DAYS=7
CLAIM_FRAUD_THRESHOLD=0.7
```

6. Run SQL migrations in Supabase SQL Editor in this order:

- `backend/sql/001_create_onboarding_profiles.sql`
- `backend/sql/002_create_app_users_and_link_onboarding.sql`
- `backend/sql/003_create_policies_and_claims.sql`
- `backend/sql/004_add_claim_rule_support.sql`
- `backend/sql/005_income_range_model.sql`
- `backend/sql/006_add_user_fks.sql`
- `backend/sql/007_relax_legacy_income_not_null.sql`
- `backend/sql/008_add_policy_onboarding_fk.sql`
- `backend/sql/009_normalize_fraud_score_scale.sql`

Important: paste SQL file contents into Supabase SQL Editor, not file path strings.

7. Start backend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/backend
APP_DEMO_MODE=true .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Base URL: `http://localhost:8000`

If you want normal production-like behavior instead of the demo flow, omit `APP_DEMO_MODE=true`.

## 5. Quick Verification

Health:

```bash
curl http://localhost:8000/api/health
```

Register:

```bash
curl -X POST http://localhost:8000/api/auth/register \
   -H "Content-Type: application/json" \
   -d '{
      "full_name": "Ramesh Kumar",
      "phone": "9876543210",
      "password": "pass1234"
   }'
```

Login:

```bash
curl -X POST http://localhost:8000/api/auth/login \
   -H "Content-Type: application/json" \
   -d '{
      "phone": "9876543210",
      "password": "pass1234"
   }'
```

Trigger check by coordinates:

```bash
curl -X POST http://localhost:8000/api/trigger/check \
   -H "Content-Type: application/json" \
   -d '{
      "lat": 13.0827,
      "lon": 80.2707
   }'
```

Demo flow check:

1. Set `APP_DEMO_MODE=true` before starting the backend.
2. Create or log in with a test user.
3. Verify `/api/policy/create` returns `status: "created"`.
4. Verify `/api/trigger/check` returns `rain: 75` and `aqi: 320`.
5. Verify `/api/claim/create` succeeds with an approved claim.

## 6. Failure Handling Behavior

- External API failure -> safe fallback values (`rain=0`, `aqi=0`, no trigger)
- Missing/invalid location -> no trigger result, server stays stable
- Rule failures (waiting period, exclusions) -> structured 4xx messages
- Auth failures -> 401/403 with explicit detail

## 7. Notes

- Auth is custom backend JWT auth, no Twilio.
- Keep frontend `EXPO_PUBLIC_API_BASE_URL` aligned with this backend host.
- Restart server after changing env variables.
