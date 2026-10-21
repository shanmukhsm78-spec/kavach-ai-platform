/**
 * Where the mobile app finds the Kavach FastAPI backend.
 *
 * IMPORTANT: on a real phone, "localhost" means the PHONE, not your laptop.
 * Use your laptop's LAN IP (same Wi-Fi as the phone), e.g. http://192.168.1.42:8000,
 * and start the backend with `--host 0.0.0.0` so it accepts LAN connections.
 *
 * Priority:
 *   1. EXPO_PUBLIC_API_URL env var (put it in mobile/.env, restart `npx expo start`)
 *   2. app.json -> expo.extra.apiBaseUrl
 *   3. placeholder below
 */
import Constants from "expo-constants";

const extra = (Constants.expoConfig?.extra ?? {}) as {
  apiBaseUrl?: string;
  enableSmsReader?: boolean;
};

export const API_BASE_URL: string = (
  process.env.EXPO_PUBLIC_API_URL ||
  extra.apiBaseUrl ||
  "http://192.168.1.100:8000" // <- placeholder LAN IP, change me
).replace(/\/+$/, "");

/** Feature flag for the (not yet built) Android SMS auto-reader. */
export const ENABLE_SMS_READER: boolean = extra.enableSmsReader === true;
