# GuardGig Frontend

Expo React Native app for GuardGig user auth, onboarding, dashboard, risk, policy, and claims flows.

## 1. Prerequisites

- Node.js 18+
- npm
- Backend running on port 8000

## 2. Install and Run (Step by Step)

1. Open terminal in frontend folder:

```bash
cd /Users/sabharishvarshaans/Documents/GuardGig/frontend
```

2. Install dependencies:

```bash
npm install
```

3. Create `frontend/.env`:

```bash
touch .env
```

4. Put this in `frontend/.env`:

```env
# Use your backend URL reachable from device/simulator
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

5. Start Expo:

```bash
npm run start
```

For device connection issues, use tunnel:

```bash
npm run start -- --tunnel --clear
```

## 3. API URL Guidance

Choose `EXPO_PUBLIC_API_BASE_URL` based on where the app runs:

- iOS Simulator (same machine): `http://127.0.0.1:8000`
- Android Emulator (same machine): `http://10.0.2.2:8000`
- Physical phone (same Wi-Fi): `http://<your-mac-lan-ip>:8000`

Example for physical device:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
```

If this variable is empty, app fallback logic tries:

- Android: `http://10.0.2.2:8000`
- iOS/Web: `http://127.0.0.1:8000`

## 4. How to Get IP for Physical Device (Mac and Windows)

When testing on a physical phone, your phone must call backend using your computer's LAN IP.

Mac (Wi-Fi):

```bash
ipconfig getifaddr en0
```

If no output, try:

```bash
ipconfig getifaddr en1
```

Windows (PowerShell):

```powershell
ipconfig
```

Then find `IPv4 Address` under your active adapter (`Wi-Fi` or `Ethernet`).

Set `frontend/.env` with that IP:

```env
EXPO_PUBLIC_API_BASE_URL=http://<YOUR_COMPUTER_LAN_IP>:8000
```

Example:

```env
EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
```

Important:

- Phone and computer must be on the same Wi-Fi.
- Backend must be running on port `8000`.
- After changing `.env`, restart Expo with cache clear:

```bash
npm run start -- --clear
```

## 5. Useful Commands

```bash
npm run start
npm run android
npm run ios
npm run web
```

## 6. Common Troubleshooting

- `Network request failed` on phone: use LAN IP in `.env` instead of `127.0.0.1`.
- App points to old API URL: stop Expo and restart with `--clear`.
- Auth fails: ensure backend is running and migrations were applied in Supabase.
