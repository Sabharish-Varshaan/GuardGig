# GuardGig Backend

FastAPI service for custom phone/password auth (JWT) and onboarding profile storage in Supabase Postgres.

## 1. Prerequisites

- Python 3.10+
- A Supabase project

## 2. Install and Run (Step by Step)

1. Open terminal in backend folder:

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

**Note:** This installs all required libraries including APScheduler for automated claim processing.

4. Create env file:

```bash
cp .env.example .env
```

5. Update `backend/.env` values:

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

6. Run SQL migrations in Supabase SQL Editor:

- First run SQL from `backend/sql/001_create_onboarding_profiles.sql`
- Then run SQL from `backend/sql/002_create_app_users_and_link_onboarding.sql`

Important: paste SQL content into Supabase SQL Editor. Do not paste file path names as SQL.

7. Start backend server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API base: `http://localhost:8000`

## 4. Automated Claim Processing

The system includes automated claim processing that runs in the background:

- **APScheduler Integration:** Automatically checks weather conditions every hour for all active policies
- **Trigger Detection:** Creates claims when rain triggers are met (≥60mm partial, ≥100mm full)
- **Fraud Prevention:** Automatically runs fraud checks on new claims
- **Status Updates:** Claims are approved or rejected based on fraud scores

The automation starts automatically when the server runs. No additional setup required.

## 5. Verify Backend Quickly

Health check:

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

## 4. Notes

- Auth is custom and free (no Twilio required).
- If frontend cannot call backend, check `CORS_ORIGINS` and restart server.
