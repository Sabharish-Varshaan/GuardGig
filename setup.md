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
