/** Home: branding, backend status, and navigation to the three checks. */
import { useCallback, useEffect, useState } from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { Link } from "expo-router";
import { pingBackend } from "../src/api/client";
import { API_BASE_URL } from "../src/api/config";
import { colors } from "../src/theme/colors";

type Status = "checking" | "online" | "offline";

const CHECKS = [
  { href: "/check-url", icon: "🔗", title: "Check a URL", desc: "Is this link phishing?" },
  { href: "/check-sms", icon: "💬", title: "Check a Message", desc: "Digital arrest, KYC, UPI, OTP scams" },
  { href: "/check-audio", icon: "🎙️", title: "Check Audio", desc: "Voice-clone detection (coming soon)" },
] as const;

export default function Home() {
  const [status, setStatus] = useState<Status>("checking");

  const refresh = useCallback(async () => {
    setStatus("checking");
    setStatus((await pingBackend()) ? "online" : "offline");
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const dot = status === "online" ? colors.safe : status === "offline" ? colors.dangerous : colors.suspicious;

  return (
    <ScrollView style={styles.page} contentContainerStyle={{ padding: 16 }}>
      <Text style={styles.brand}>🛡️ Kavach Shield</Text>
      <Text style={styles.tagline}>AI that spots scams before they reach your wallet.</Text>

      <Pressable style={styles.status} onPress={refresh}>
        <View style={[styles.dot, { backgroundColor: dot }]} />
        <Text style={styles.statusText}>
          Backend {status} · {API_BASE_URL} (tap to retry)
        </Text>
      </Pressable>

      {CHECKS.map((c) => (
        <Link key={c.href} href={c.href} asChild>
          <Pressable style={styles.card}>
            <Text style={styles.cardTitle}>{c.icon} {c.title}</Text>
            <Text style={styles.cardDesc}>{c.desc}</Text>
          </Pressable>
        </Link>
      ))}

      <Text style={styles.footer}>Part of the Kavach AI Platform · Protect mode companion</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bg },
  brand: { color: colors.text, fontSize: 30, fontWeight: "800" },
  tagline: { color: colors.muted, marginTop: 4, marginBottom: 16 },
  status: { flexDirection: "row", alignItems: "center", marginBottom: 16 },
  dot: { width: 10, height: 10, borderRadius: 5, marginRight: 8 },
  statusText: { color: colors.muted, fontSize: 12, flexShrink: 1 },
  card: { backgroundColor: colors.card, borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: 16, marginBottom: 12 },
  cardTitle: { color: colors.text, fontSize: 17, fontWeight: "700" },
  cardDesc: { color: colors.muted, marginTop: 4 },
  footer: { color: colors.muted, fontSize: 12, textAlign: "center", marginTop: 24 },
});
