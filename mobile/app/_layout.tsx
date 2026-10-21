/** Root navigation (expo-router stack). Each file in app/ is a screen. */
import { useEffect } from "react";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { colors } from "../src/theme/colors";
import { startSmsReader } from "../src/features/sms-reader";

export default function RootLayout() {
  // Future-work hook: no-op unless enableSmsReader is true AND on Android.
  useEffect(() => startSmsReader(), []);

  return (
    <>
      <StatusBar style="light" />
      <Stack
        screenOptions={{
          headerStyle: { backgroundColor: colors.card },
          headerTintColor: colors.text,
          contentStyle: { backgroundColor: colors.bg },
        }}
      >
        <Stack.Screen name="index" options={{ title: "Kavach Shield" }} />
        <Stack.Screen name="check-url" options={{ title: "Check URL" }} />
        <Stack.Screen name="check-sms" options={{ title: "Check Message" }} />
        <Stack.Screen name="check-audio" options={{ title: "Check Audio" }} />
      </Stack>
    </>
  );
}
