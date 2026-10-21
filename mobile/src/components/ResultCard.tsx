/**
 * Reusable result view: score bar + verdict badge + reasons + EN/HI explanation.
 * Used by both the URL and SMS screens (and later the Audio screen).
 */
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import type { CheckResult, Lang } from "../api/client";
import { colors, verdictColor } from "../theme/colors";

export default function ResultCard({ result }: { result: CheckResult }) {
  const [lang, setLang] = useState<Lang>("en");
  const color = verdictColor(result.verdict);

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.score}>{result.risk_score}/100</Text>
        <View style={[styles.badge, { backgroundColor: color }]}>
          <Text style={styles.badgeText}>{result.verdict.toUpperCase()}</Text>
        </View>
      </View>

      {/* Risk score bar */}
      <View style={styles.barTrack}>
        <View style={[styles.barFill, { width: `${result.risk_score}%`, backgroundColor: color }]} />
      </View>

      {/* Language toggle */}
      <View style={styles.toggle}>
        {(["en", "hi"] as Lang[]).map((l) => (
          <Pressable
            key={l}
            onPress={() => setLang(l)}
            style={[styles.toggleBtn, lang === l && styles.toggleActive]}
          >
            <Text style={styles.toggleText}>{l === "en" ? "English" : "हिंदी"}</Text>
          </Pressable>
        ))}
      </View>

      <Text style={styles.explanation}>{result.explanation[lang]}</Text>

      {result.reasons.length > 0 && (
        <>
          <Text style={styles.heading}>{lang === "en" ? "Why?" : "क्यों?"}</Text>
          {result.reasons.map((r) => (
            <Text key={r.code} style={styles.reason}>• {r[lang]}</Text>
          ))}
        </>
      )}

      {result.verdict !== "safe" && (
        <Text style={styles.helpline}>
          {lang === "en"
            ? "Lost money? Call the cybercrime helpline 1930 or visit cybercrime.gov.in"
            : "पैसे गए? साइबर क्राइम हेल्पलाइन 1930 पर कॉल करें या cybercrime.gov.in देखें"}
        </Text>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.card, borderColor: colors.border, borderWidth: 1, borderRadius: 12, padding: 16, marginTop: 16 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  score: { color: colors.text, fontSize: 28, fontWeight: "700" },
  badge: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 999 },
  badgeText: { color: "#000", fontWeight: "700" },
  barTrack: { height: 10, backgroundColor: colors.border, borderRadius: 5, marginVertical: 12, overflow: "hidden" },
  barFill: { height: "100%" },
  toggle: { flexDirection: "row", gap: 8, marginBottom: 8 },
  toggleBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: colors.border },
  toggleActive: { backgroundColor: colors.accent },
  toggleText: { color: colors.text },
  explanation: { color: colors.text, fontSize: 15, lineHeight: 22 },
  heading: { color: colors.muted, marginTop: 12, marginBottom: 4, fontWeight: "600" },
  reason: { color: colors.text, marginBottom: 4 },
  helpline: { color: colors.suspicious, marginTop: 12, fontSize: 13 },
});
