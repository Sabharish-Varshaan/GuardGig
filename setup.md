
## Railway Deployment

Deploy backend and frontend as two separate Railway services from the same repository.

### Backend service

1. In Railway, create a new service from this repo.
2. Set Root Directory to `backend`.
3. Railway will use `backend/railway.json` automatically.
4. Add required backend environment variables (`SUPABASE_*`, `JWT_SECRET`, `OPENWEATHER_API_KEY`, etc.).
5. Deploy and verify health endpoint at `/api/health`.

### Frontend PWA service

1. Create another Railway service from the same repo.
2. Set Root Directory to `frontend`.
3. Railway will use `frontend/railway.json` and run:
	- Build: `npm ci && npm run build:web`
	- Start: `npm run start:railway`
4. Set `EXPO_PUBLIC_API_BASE_URL` to the deployed backend URL.
5. Redeploy frontend and test install/offline behavior in browser.

### Notes

- Frontend is served as a static SPA using `serve` with Railway-provided `$PORT`.
- Keep frontend and backend on separate Railway domains/services for easier scaling and logs.
# GuardGig Setup

This file is the single quick-start guide for running both services.

Detailed docs:

- Frontend: `frontend/README.md`
- Backend: `backend/README.md`

## Prerequisites

- Node.js 18+
- npm
- Python 3.10+
- Supabase project

## 1. Backend (Terminal 1)

1. Go to backend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/backend
```

2. Create and activate virtual env:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install backend dependencies:

```bash
pip install -r requirements.txt
```

**Note:** This installs all required libraries including APScheduler for automated claim processing.

4. Create env and fill values:

```bash
cp .env.example .env
```

Use these keys in `backend/.env`:

```env
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081

SUPABASE_URL=https://<your-project-ref>.supabase.co
SUPABASE_ANON_KEY=<your-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
SUPABASE_USERS_TABLE=app_users
SUPABASE_ONBOARDING_TABLE=onboarding_profiles

JWT_SECRET=<use-a-long-random-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXP_MINUTES=60
REFRESH_TOKEN_EXP_DAYS=7
```

5. Run SQL in Supabase SQL Editor (in order):

- `backend/sql/001_create_onboarding_profiles.sql`
- `backend/sql/002_create_app_users_and_link_onboarding.sql`
- `backend/sql/003_create_policies_and_claims.sql`
- `backend/sql/004_add_claim_rule_support.sql`
- `backend/sql/005_income_range_model.sql`
- `backend/sql/006_add_user_fks.sql`
- `backend/sql/007_relax_legacy_income_not_null.sql`
- `backend/sql/008_add_policy_onboarding_fk.sql`
- `backend/sql/009_normalize_fraud_score_scale.sql`

Important: paste SQL content, not file paths.

6. Start backend:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** The backend includes automated claim processing that runs every hour in the background. No additional configuration needed.

## 2. Frontend (Terminal 2)

1. Go to frontend:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/frontend
```

2. Install frontend dependencies:

```bash
npm install
```

3. Create `frontend/.env` and set backend URL:

```env
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

Use based on target:

- iOS simulator: `http://127.0.0.1:8000`
- Android emulator: `http://10.0.2.2:8000`
- Physical phone: `http://<your-mac-lan-ip>:8000`

How to find LAN IP for physical phone testing:

Mac:

```bash
ipconfig getifaddr en0
```

If needed:

```bash
ipconfig getifaddr en1
```

Windows (PowerShell):

```powershell
ipconfig
```

Use `IPv4 Address` from the active `Wi-Fi` or `Ethernet` adapter, then set:

```env
EXPO_PUBLIC_API_BASE_URL=http://<YOUR_COMPUTER_LAN_IP>:8000
```

4. Start Expo:

```bash
npm run start
```

If network is unstable in Expo Go:

```bash
npm run start -- --tunnel --clear
```

## 3. Quick Health Check

```bash
curl http://localhost:8000/api/health
```

## 4. Current Auth Mode

- Custom backend auth (`app_users` + JWT)
- Phone + password registration/login
- No Twilio required
