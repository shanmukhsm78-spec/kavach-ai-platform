# Kavach Shield — Mobile App

Companion app for **Protect mode** of the Kavach AI Platform. Paste a suspicious
link or SMS on your phone and get an instant risk score, verdict
(safe / suspicious / dangerous), reasons, and an English/हिंदी explanation —
powered by the same FastAPI backend as the web dashboard.

Built with **Expo (React Native + TypeScript)** and **expo-router**; runs on Android and iPhone.

## Features
| Screen | Backend call | Status |
|---|---|---|
| Home — branding, backend status dot (pings `/health`) | `GET /health` | ✅ |
| Check URL | `POST /protect/url` | ✅ |
| Check Message (SMS) | `POST /protect/sms` | ✅ |
| Check Audio (voice clone) | `POST /protect/audio` | 🚧 placeholder (client fn ready) |
| Android SMS auto-reader | — | 🔮 future work |

Shared `ResultCard` component: score bar + verdict badge + reasons + EN/HI toggle + 1930 helpline hint.

## Run it on your phone
1. **Start the backend so the phone can reach it** (from repo root):
   ```bash
   uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```
2. **Find your laptop's LAN IP** (`ipconfig` on Windows, `ip addr`/`ifconfig` on Linux/macOS), e.g. `192.168.1.42`.
   Phone and laptop must be on the **same Wi-Fi**. `localhost` will NOT work on a phone.
3. **Point the app at it** — either:
   - `cp .env.example .env` and set `EXPO_PUBLIC_API_URL=http://192.168.1.42:8000`, or
   - edit `expo.extra.apiBaseUrl` in `app.json`.
4. **Install & start:**
   ```bash
   cd mobile
   npm install
   npx expo start
   ```
5. Install **Expo Go** (Play Store / App Store) and scan the QR code. The home screen dot turns green when the backend is reachable.

Tip: `npx expo start --web` runs it in a browser too; `npm run typecheck` runs `tsc`.

## Layout
```
app/                 screens (expo-router: file = route)
  _layout.tsx        stack navigator + SMS-reader hook
  index.tsx          home / dashboard
  check-url.tsx      URL check
  check-sms.tsx      message check
  check-audio.tsx    placeholder
src/api/config.ts    backend URL resolution + feature flags
src/api/client.ts    typed API client (fetch + timeout)
src/components/      CheckScreen (input+button), ResultCard
src/features/sms-reader/  future Android SMS auto-reader stub
src/theme/colors.ts  palette
```

## Future work: Android SMS auto-reading
Plug-in point: `src/features/sms-reader/index.ts` (`startSmsReader()`), already
called from `app/_layout.tsx` and gated by `expo.extra.enableSmsReader` in `app.json`.
- **Android only** — iOS doesn't allow apps to read SMS.
- Needs `READ_SMS`/`RECEIVE_SMS` permissions and a native module, so it needs a
  **development build** (`npx expo run:android` / EAS), **not Expo Go**.
- Play Store restricts SMS permissions; fine for a sideloaded demo APK.
