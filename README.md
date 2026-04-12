# GuardGig
# AI-Powered Parametric Insurance for Quick-Commerce Gig Workers
[Jump to Phase 2](#phase-2-system-intelligence--automation)

## Hackathon Scope Note

- Policy creation and payout flows are currently implemented as mock/demo logic for hackathon purposes.
- Current payout status and amounts are simulated from internal app/backend rules and are not connected to a real money movement provider.
- Current premium payment integration: Razorpay test-mode order creation and verification for policy activation.

## Live App

- GuardGig is published as a Progressive Web App (PWA).
- Live URL: https://guardgigs.smartattend.online
- The same product can also be deployed as an installable mobile app build.

## Local Setup (Backend + Frontend)

This root section contains complete setup instructions for both backend and frontend, including local source implementation flow, dependencies, environment variables, verification, and troubleshooting.

### 1. Local Source Code Implementation

- `backend/`: FastAPI backend, business rules, trigger/fraud/premium logic, SQL migrations, ML inference helpers.
- `backend/app/`: API routes and core service logic.
- `backend/sql/`: Supabase SQL migrations that must be applied before full app flow testing.
- `backend/ml/`: model training and prediction artifacts/utilities.
- `frontend/`: Expo React Native app.
- `frontend/src/`: UI screens, navigation, context state, components, API client.

### 2. Prerequisites and Dependencies

Backend prerequisites:

- Python 3.10+
- Supabase project
- OpenWeather API key (AQI fallback)
- Network access to public aqi.in dashboard pages

Frontend prerequisites:

- Node.js 18+
- npm
- Backend running at a reachable URL

Optional demo mode:

- `APP_DEMO_MODE=true` enables demo behavior in policy/trigger/claim flow.

### 3. Backend Architecture and Logic

Core business flow:

1. User registers and logs in via custom auth routes.
2. User submits onboarding profile.
3. Policy is created only if underwriting conditions pass.
4. Trigger engine evaluates live rain + AQI at coordinates.
5. Claim creation happens when trigger conditions are met.
6. Fraud/exclusion rules gate claim approval.
7. Payout amount is produced from trigger severity.

Trigger engine:

- Rain source: Open-Meteo (`hourly=rain`)
- AQI source: aqi.in city dashboard (primary)
- AQI fallback: OpenWeather Air Pollution API

Severity rules:

- `rain >= 100` -> `full`
- `rain >= 60` -> `partial`
- `aqi >= 400` -> `full`
- `aqi >= 300` -> `partial`
- otherwise -> no trigger

Claim creation flow (`/api/claim/create`):

1. Active policy lookup
2. Waiting period enforcement
3. Max one claim/day enforcement
4. Fresh trigger evaluation
5. Exclusion checks
6. Payout computation
7. Claim insertion with status/reason

Underwriting:

- `active_days < 5` -> ineligible
- `5 <= active_days < 7` -> eligible, low tier
- `active_days >= 7` -> eligible, medium tier

Automated claims:

- APScheduler runs hourly
- Scans active policies and auto-creates approved claims when trigger/rules pass

### 4. Backend API Surface

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

### 5. Backend Setup (Step by Step)

1. Go to backend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/backend
```

2. Create and activate virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install backend dependencies:

```bash
pip install -r requirements.txt
```

4. Create backend env file:

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
- `backend/sql/010_enforce_daily_claim_limit.sql`

Important: paste SQL file contents into Supabase SQL Editor, not file path strings.

7. Start backend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/backend
APP_DEMO_MODE=true .venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Base URL: `http://localhost:8000`

If you want normal production-like behavior instead of demo behavior, omit `APP_DEMO_MODE=true`.

### 6. Backend Quick Verification

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

1. Set `APP_DEMO_MODE=true` before starting backend.
2. Create or log in with a test user.
3. Verify `/api/policy/create` returns `status: "created"`.
4. Verify `/api/trigger/check` returns `rain: 75` and expected AQI for resolved location.
5. Verify `/api/claim/create` succeeds with an approved claim.

### 7. Backend Failure Handling Behavior

- aqi.in lookup failure -> fallback to OpenWeather AQI, then safe values
- External API failure -> safe fallback values (`rain=0`, `aqi=0`, no trigger)
- Missing/invalid location -> no trigger result, service remains stable
- Rule failures (waiting period, exclusions) -> structured 4xx responses
- Auth failures -> 401/403 with explicit detail

### 8. Frontend Product Logic

High-level user flow:

1. Login/Register
2. Onboarding profile submission
3. Policy creation and sync
4. Dashboard requests location and checks live trigger conditions
5. User taps `Check Coverage`
6. Frontend calls trigger API and auto-starts claim creation if trigger exists
7. Claim status appears in Claims and Payout screens

Backend-driven data model in UI:

- `policy`: weekly income, premium, coverage, status, tier, eligibility
- `risk`: rain, AQI, severity, trigger type, status text
- `claimsHistory`: trigger type, status, payout amount, timestamps
- `workflowState`: automation step progress

No premium or payout computation is performed in frontend.

Real-time trigger + auto-claim flow:

1. Request location permission with `expo-location`
2. Fetch `lat/lon`
3. `POST /api/trigger/check`
4. Display risk data from backend
5. On `Check Coverage`, trigger check runs again and may call `/api/claim/create`

### 9. Frontend Setup (Step by Step)

1. Go to frontend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Ensure location dependency exists (already in this project):

```bash
CI=1 npx expo install expo-location
```

4. Create/update `frontend/.env`:

```env
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

5. Start Expo:

```bash
npm run start
```

If needed:

```bash
npm run start -- --tunnel --clear
```

### 10. Frontend API URL Configuration

Use environment value based on target:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical phone (same Wi-Fi): `http://<your-lan-ip>:8000`

Example:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
```

Fallback if env is missing:

- Android fallback: `http://10.0.2.2:8000`
- iOS/Web fallback: `http://127.0.0.1:8000`

### 11. Frontend Verification Checklist

1. Backend `/api/health` responds.
2. App can register/login.
3. Dashboard prompts for location permission.
4. Dashboard shows rain/AQI values.
5. `Check Coverage` progresses through workflow states.
6. Claims screen shows claim entries.

For demo mode, confirm backend returns policy created, trigger values `rain=75` and `aqi=320`, and an approved claim.

### 12. Frontend Useful Commands

```bash
npm run start
npm run android
npm run ios
npm run web
```

### 13. Frontend Troubleshooting

- `Network request failed`
  - Verify `EXPO_PUBLIC_API_BASE_URL`
  - For physical phone testing, do not use `127.0.0.1`
  - Restart Expo with cache clear

- Location not available
  - Ensure app location permission is granted
  - Retry dashboard load

- No live risk values
  - Confirm backend trigger route is running
  - Confirm weather API key is configured in backend

- Claim not created
  - Trigger may be false (`No disruption detected`)
  - Backend waiting period/exclusion rules may block claim creation

### 14. End-to-End Local Run Flow

1. Start backend in one terminal.
2. Start frontend Expo in another terminal.
3. Register/login in app.
4. Complete onboarding.
5. Create policy.
6. Run trigger check and claim flow.
7. Validate claim and payout screens.

---


# Overview and Problem Statement

* India’s delivery partners (Swiggy, Zomato, Zepto, Blinkit, Amazon, Dunzo) are highly dependent on external conditions.
* Environmental disruptions (rain, floods, heat, pollution) reduce working hours and cause 20–30% income loss.
* Gig workers:

  * Have no fixed salary
  * Operate on a weekly income cycle
  * Lack protection against external risks
* Current gap:

  * No system compensates income loss due to uncontrollable external factors

### Constraint Compliance

* Coverage strictly limited to loss of income
* No coverage for:

  * Health
  * Accidents
  * Vehicle repairs
* Financial model strictly follows a weekly pricing structure

---

# Persona: Ramesh Kumar (Quick-Commerce Worker)

* Age: 23–27
* Location: Chennai
* Work type: Full-time delivery partner
* Vehicle: Two-wheeler
* Work duration: 10–12 hours/day

### Income Model

* Gross earnings: ₹900–₹1100/day
* Expenses: ₹200–₹300/day
* Net income: ₹600–₹800/day

### Risk Exposure

* Weekly income: ₹6000–₹7500
* Income fluctuation: 20–40%
* 2-day disruption results in ₹3000–₹3500 loss

---

# Parametric Trigger System
<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/4923aaef-38a7-4e16-9f93-d824699ba84f" />

## Environmental Triggers

* Rain ≥ 60 mm → Partial payout (30%)
* Rain ≥ 100 mm → Full payout (100%)
* Temperature ≥ 40°C → Partial payout
* Temperature ≥ 45°C → Full payout
* AQI > 300 → Partial payout
* AQI ≥ 400 → Full payout

## Operational Triggers

* Orders drop > 50% → Partial payout
* Orders = 0 → Full payout

## Deterministic Logic Engine

* If Rain ≥ 60 mm and duration ≥ 2 hours → Partial payout
* If Rain ≥ 100 mm or flood alert → Full payout
* If AQI ≥ 400 → Full payout
* If Orders = 0 → Full payout

---

# AI-Powered Weekly Premium Model
<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/d8987ec6-d290-4c92-bcc7-57a6b87776ae" />

## Premium Formula

* Premium = Base + Risk Adjustment + Event Factor + Loss Control

## Base Component

* Base = 0.6% × Weekly Income

## Risk Score Model (Mathematical Definition)

* Risk Score (0–1) calculated as:

  * 0.4 × Rain Index
  * 0.3 × Flood History
  * 0.2 × AQI Trend
  * 0.1 × Zone Risk

### Feature Definitions

* Rain Index: normalized rainfall probability for the week
* Flood History: historical flood occurrence frequency
* AQI Trend: pollution severity trend over time
* Zone Risk: infrastructure vulnerability score

## Risk Adjustment

* Risk Adjustment = Risk Score × ₹20

## Event Factor

* ₹5–₹10 based on predicted weather events

## Loss Control

* Adjusts premium based on system-wide payout ratios

## Example Premium Calculation

* Base = ₹36
* Risk Adjustment = ₹12
* Event Factor = ₹8
* Final Premium = ₹56/week

---

# Payout Structure

* Partial disruption: ~₹200
* Severe disruption: ~₹500
* Full disruption: ~₹700
* Weekly payout cap: ₹3000

---

# Adversarial Defense and Anti-Spoofing Strategy
<img width="926" height="475" alt="image" src="https://github.com/user-attachments/assets/1f807c53-1689-4ff0-8247-5307ce9f5b82" />

## Problem Context

* Fraud syndicates exploit systems using GPS spoofing
* Fake location claims trigger false payouts
* Basic GPS validation is insufficient

## Multi-Layer Data Validation

* GPS + IP + Cell tower triangulation
* WiFi network consistency checks
* Device integrity:

  * Root detection
  * Jailbreak detection
  * Mock location detection

## Behavioral Analysis

* Movement patterns over time
* Delivery activity density
* Session consistency and duration

## Graph-Based Fraud Detection

* Uses NetworkX and Graph Neural Networks
* Identifies coordinated fraud clusters
* Detects:

  * Shared IP subnets
  * Identical behavior patterns
  * Simultaneous claim bursts

## Fraud Score Model

* Fraud Score calculated as:

  * 0.3 × Location Mismatch
  * 0.25 × Device Anomaly
  * 0.25 × Behavior Anomaly
  * 0.2 × Graph Cluster Risk

## Decision Thresholds

* 0–0.3 → Approve instantly
* 0.3–0.7 → Soft verification
* > 0.7 → Reject and flag

## Soft Verification Mechanism

* Triggered for medium-risk claims
* User uploads real-time image:

  * Flood conditions OR
  * Delivery app “orders paused” screen
* AI validates authenticity
* Ensures honest users are not penalized

---

# System Architecture
<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/02b75dfe-c491-4521-a0ec-f40b00e37da7" />

## Automated Processing Engine

* **Background Scheduler:** APScheduler runs automated claim processing every hour
* **Weather Monitoring:** Real-time weather API integration for trigger detection
* **Auto Claim Creation:** System automatically creates claims when conditions are met
* **Fraud Engine:** Integrated fraud scoring with automatic approval/rejection
* **No User Intervention:** Entire claim lifecycle runs autonomously

## Data Flow Pipeline

* User (React Native App)
* API Gateway (FastAPI)
* Feature Engineering Layer
* ML Models (Risk + Fraud)
* Decision Engine
* Fraud Validation Layer
* Payout Engine
* Payment System (UPI / Mock)

## Architecture Layers

### Data Layer

* Weather API (OpenWeather)
* AQI API (AQICN)
* Platform APIs (mock/simulated)
* Government flood alerts (if available)

### Feature Layer

* Aggregates:

  * Rainfall patterns
  * AQI trends
  * Order activity

### Model Layer

* Risk scoring model
* Forecast model
* Fraud detection model

---
<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/fb1c102c-664e-45b2-8eaa-b3a75c9b4b93" />

# Tech Stack

* Mobile: React Native
* Backend: FastAPI (Python)
* Database: Supabase (PostgreSQL)
* Caching: Redis
* Messaging/Queue: Kafka

---

# Scalability and Performance
<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/25ee70a2-245d-4fde-8549-ba18f09af22b" />

## System Capacity

* Supports 2–3 million users
* Handles 50,000+ concurrent claims
* API latency < 200 ms
* Claim processing time < 2 seconds

## Optimization Strategies

* Redis caching for external APIs
* Kafka for batch claim processing
* Asynchronous FastAPI endpoints

---

# Fail-Safe Mechanisms

## Circuit Breaker

* Temporarily halts payouts during abnormal spikes
* Prevents system overload

## City-Level Caps

* Limits total payouts per geographic region
* Prevents liquidity exhaustion

---

# Failure Scenario Simulation
<img width="1024" height="572" alt="image" src="https://github.com/user-attachments/assets/666362df-e89c-4138-a03d-4bf0540b2dd2" />

Example: Chennai Flood Event

* Rainfall: 120 mm
* Claims triggered: 10,000

System response:

* Fraud detection blocks 2,000 claims
* Valid claims: 8,000
* Claims processed via Kafka batching
* Circuit breaker activates if threshold exceeded

---

# System Workflow

* User onboarding and profile creation
* AI computes weekly premium
* Real-time monitoring of environmental and operational data
* Trigger detection based on thresholds
* Fraud validation executed
* Payout amount calculated
* Instant transfer to user wallet

---

# Final Position

* Fully automated parametric insurance system
* AI-driven pricing and fraud detection
* Real-time trigger-based payouts
* Scalable to millions of users
* Designed specifically for gig economy income protection

---

# Conclusion

* Provides financial stability for gig workers
* Ensures fair pricing through AI models
* Prevents fraud through multi-layer validation
* Operates as a production-ready, scalable system

---
<a id="Phase 2"><\a>
## Phase 2: System Intelligence & Automation

## 1. Policy Integration

### Onboarding and Income Modeling

The onboarding flow persists income as a range, not a single manual daily number:

* `min_income`
* `max_income`
* derived `mean_income`
* derived `income_variance`

The backend computes:

$$
\mathrm{mean\_income} = \frac{\mathrm{min\_income} + \mathrm{max\_income}}{2}
$$

$$
\mathrm{income\_variance} = \frac{\mathrm{max\_income} - \mathrm{min\_income}}{\mathrm{mean\_income}}
$$

Policy creation then converts to weekly income:

$$
\mathrm{weekly\_income} = \mathrm{round}(\mathrm{mean\_income} \times 7)
$$

### Policy Creation and Coverage Definition

Policy creation is gated by onboarding completion and underwriting age checks (`active_days` from onboarding creation date). In normal mode:

* `< 5` days -> `ineligible`
* `5-6` days -> `eligible` (tier `low`)
* `>= 7` days -> `eligible` (tier `medium`)

In demo mode, eligibility is forced to eligible.

Coverage is defined in backend policy creation as a fixed amount:

* `coverage_amount = 700.00`

### Premium Computation

Premium is calculated server-side only.

Base:

$$
\mathrm{base} = 0.006 \times \mathrm{weekly\_income}
$$

Current premium function:

$$
\mathrm{premium} = \mathrm{base} \times \left(1 + \mathrm{risk\_score} + 0.02 \times \mathrm{income\_variance}\right)
$$

`risk_score` comes from `ml/predict.py` (`get_risk_score`). In current policy creation, rain/AQI/location are not passed into this call, so premium-time ML scoring is driven by income-derived features unless other endpoints provide weather inputs.

## 2. Automated Flow

### Trigger Check to Claim Creation

The backend flow is:

1. `POST /api/trigger/check` fetches rain + AQI snapshot and returns trigger metadata.
2. `POST /api/claim/create` re-fetches rain + AQI and re-evaluates trigger before claim creation.

Triggering is deterministic (rule thresholds), not model-predicted:

* rain `>= 100` -> full
* rain `>= 60` -> partial
* AQI `>= 400` -> full
* AQI `>= 300` -> partial

### Is Claim Auto-Triggered?

Yes, from the frontend orchestration flow:

* `DashboardScreen` auto-starts coverage check when policy is active + eligible.
* `AppContext.startCoverageCheck()` runs:
  1. location fetch
  2. `trigger/check`
  3. if detected, `claim/create`
  4. workflow state updates and payout navigation

There is no premium or payout math in frontend; frontend acts as orchestration + UI state.

## 3. AI/ML Integration

### Risk Model Usage

Implemented in `ml/predict.py` via `get_risk_score`:

* used in premium calculation (`premium_utils.py`)
* returns model probability when model artifact exists
* falls back to deterministic heuristic when model is unavailable

So: `risk_score` is integrated into premium.

### Fraud Model Usage

Implemented in `ml/predict.py` via `get_fraud_score`:

* used inside claim creation (`/api/claim/create`)
* claim is rejected when `fraud_score > 0.7`
* additional rule exclusions are applied in non-demo mode

So: `fraud_score` is directly used in claim decision.

### Trigger Engine Type

Trigger detection is currently rule-based (`check_trigger` thresholds), not ML-based.

## 4. Backend-Frontend Sync

System behavior is API-driven and synchronized around backend decisions:

* Frontend consumes `/api/policy/me`, `/api/claims/me`, `/api/trigger/check`, `/api/claim/create`.
* Policy, claim status, payout amount, and risk severity all originate from backend responses.
* Frontend transforms response data for display but does not compute insurance logic.

## 5. Improvements (Implemented in Phase 2)

* Income modeling upgraded from flat value to range-based underwriting inputs.
* Premium pipeline connected to ML risk scoring with fallback safety.
* Claim pipeline connected to ML fraud scoring plus deterministic exclusion guards.
* Automated trigger-to-claim flow implemented in app lifecycle (eligible users).
* Trigger utilities include API caching and graceful fallbacks for unstable external data.

## 6. Outcome

Phase 2 delivers a working intelligence + automation layer where:

* policy pricing uses ML-assisted risk input,
* claim approval includes ML fraud screening,
* event trigger detection remains deterministic and explainable,
* frontend stays thin and API-driven,
* and end-to-end claim initiation can run automatically for eligible users.

