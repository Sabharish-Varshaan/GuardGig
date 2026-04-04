# GuardGig
# AI-Powered Parametric Insurance for Quick-Commerce Gig Workers

---
[Jump to Phase 2](#phase-2-system-intelligence--automation)


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

