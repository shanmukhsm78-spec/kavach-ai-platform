/**
 * ===================== FUTURE WORK: Android SMS auto-reader =====================
 *
 * NOT IMPLEMENTED. This is the single plug-in point for scanning incoming SMS
 * automatically and warning the user.
 *
 * Constraints (mention these in the viva):
 *  - ANDROID ONLY. iOS does not let third-party apps read SMS at all.
 *  - Needs RECEIVE_SMS / READ_SMS runtime permissions (add to app.json
 *    "android.permissions"). Google Play restricts these to default-SMS apps,
 *    so this is for a demo / sideloaded APK.
 *  - Needs a native module (e.g. a config plugin around a BroadcastReceiver),
 *    so it will NOT run in Expo Go - you must make a development build:
 *    `npx expo prebuild` + `npx expo run:android` (or EAS Build).
 *
 * How to enable later:
 *  1. Set expo.extra.enableSmsReader = true in app.json.
 *  2. Implement startSmsReader() below: request permission, subscribe to
 *     incoming messages, and for each one call checkSms(body) from api/client.
 *  3. If verdict !== "safe", show a local notification (expo-notifications).
 *  It is already called from app/_layout.tsx, guarded by the flag.
 * ==============================================================================
 */
import { Platform } from "react-native";
import { ENABLE_SMS_READER } from "../../api/config";

export function startSmsReader(): () => void {
  if (!ENABLE_SMS_READER || Platform.OS !== "android") return () => {};
  // TODO(sms-reader): request READ_SMS/RECEIVE_SMS, subscribe, call checkSms().
  console.warn("[Kavach] SMS reader flag is on, but the feature is not implemented yet.");
  return () => {};
}
