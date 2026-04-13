# GuardGig Admin

Separate web dashboard for GuardGig administrators.

## Features
- Admin-only login with email and password
- Protected metrics dashboard
- 10-second auto refresh
- Logout and route protection

## Setup

```bash
cd guardgig-admin
npm install
npm run dev
```

## Environment

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Build

```bash
npm run build
npm run preview
```

## Railway Deployment

The admin app is Railway-ready with Nixpacks.

1. Create a new Railway service pointing to `guardgig-admin/`.
2. Set root directory to `guardgig-admin`.
3. Add environment variable:

```env
VITE_API_BASE_URL=https://<your-backend-domain>
```

Railway will build with `npm run build` and start with `npm run start`.
