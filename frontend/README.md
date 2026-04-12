# GuardGig Frontend

Expo React Native app for the GuardGig parametric insurance experience.

## Hackathon Scope Note

- Policy creation and payout behavior is currently mock/demo for hackathon delivery.
- The payout shown in app screens is a simulated value from backend decision logic, not a live transfer.
- Future production plan: integrate Stripe payouts and webhook-based payout status updates.

This frontend is backend-driven: risk, trigger, claim, policy, and payout values are sourced from API responses, not calculated in UI.

## 1. Product Logic (What the App Is Doing)

### 1.1 High-Level User Flow

1. Login/Register
2. Onboarding profile submission
3. Policy creation and sync
4. Dashboard requests location and checks live trigger conditions
5. User taps `Check Coverage`
6. Frontend calls trigger API and auto-starts claim creation if trigger exists
7. Claim status appears in Claims and Payout screens

### 1.2 Backend-Driven Data Model in UI

The app context stores normalized backend data for:

- `policy` (`weekly_income`, `premium`, `coverage_amount`, status, tier, eligibility)
- `risk` (`rain`, `aqi`, `severity`, `trigger type`, text status)
- `claimsHistory` (`trigger_type`, status, payout amount, timestamps)
- `workflowState` (automation step progress)

No premium or payout computation is performed in the frontend.

### 1.3 Real-Time Trigger + Auto Claim Flow

Dashboard logic:

1. Ask location permission via `expo-location`
2. Fetch `lat/lon`
3. `POST /api/trigger/check` with coordinates
4. Display rain, AQI, and risk status from backend response

When `Check Coverage` is tapped:

1. Trigger check runs again
2. If `trigger.trigger === true`, call `POST /api/claim/create`
3. Claim request includes trigger context (`trigger_type`, `severity`) and coordinates
4. UI workflow states progress through checking -> validating -> processing -> approved/failed

### 1.4 Screen Responsibilities

- Dashboard: live risk and automated workflow entry point
- Risk: current risk snapshot from backend values
- Policy: backend policy details (income, premium, coverage, status, tier)
- Claims: backend claim history and statuses
- Payout: backend-linked payout amount and reason from latest claim

## 2. Prerequisites

- Node.js 20.19.4+
- npm
- Backend running at a reachable URL

Recommended backend setup for local development:

- Start the backend from the `backend` directory with the project virtualenv
- Use `APP_DEMO_MODE=true` if you want the demo flow to always create a policy and claim

## 3. Setup (Step by Step)

1. Open terminal in frontend:

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

## 4. API URL Configuration

Use environment value based on runtime target:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical device (same Wi-Fi): `http://<your-lan-ip>:8000`

Example:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
```

For iOS simulator and Android emulator, keep the backend running locally and set the frontend API base URL to the matching host for your device type.

Fallback behavior if env is missing:

- Android fallback: `http://10.0.2.2:8000`
- iOS/Web fallback: `http://127.0.0.1:8000`

## 5. Setup Verification Checklist

1. Backend `/api/health` responds
2. App can register/login
3. Dashboard prompts for location permission
4. Dashboard shows rain/AQI values
5. `Check Coverage` progresses through workflow states
6. Claims screen shows real claim entries

For demo mode validation, confirm the backend returns a created policy, trigger values of rain 75 and aqi 320, and an approved claim.

## 6. Useful Commands

```bash
npm run start
npm run android
npm run ios
npm run web
```

## 7. Troubleshooting

- `Network request failed`
	- Verify `EXPO_PUBLIC_API_BASE_URL`
	- For phone testing, do not use `127.0.0.1`
	- Restart Expo with cache clear

- Location not available
	- Ensure app location permission is granted
	- Retry Dashboard load

- No live risk values
	- Confirm backend trigger route is running
	- Confirm backend has weather API key configured

- Claim not created
	- Trigger may be false (`No disruption detected`)
	- Backend waiting period/exclusion rules may block claim creation

## 8. Key Implementation Notes

- Frontend intentionally avoids financial/trigger calculations.
- UI status text is designed to communicate automation steps in real time.
- Data is synchronized through app context and API service modules.

## 9. Railway PWA Deployment

Deploy frontend as a separate Railway service from the same repository.

1. Create a new Railway service from this repo.
2. Set `Root Directory` to `frontend`.
3. Railway will use:
	- `frontend/railway.json`
	- `frontend/nixpacks.toml`
4. Build/start behavior for Railway:
	- Build: `npm run build:web` (Expo static web export to `dist`)
	- Start: `npm run start:railway` (serves `dist` as SPA on `$PORT`)
5. Set environment variables:
	- `EXPO_PUBLIC_API_BASE_URL=https://<backend-domain>.up.railway.app`
6. Redeploy and verify:
	- App loads on Railway URL
	- Install prompt appears in supported browsers (PWA)
	- Payment route opens Razorpay checkout screen

PWA assets are served from `frontend/public` (`manifest.json`, `sw.js`, icons) and service worker registration is done in `frontend/index.js`.
