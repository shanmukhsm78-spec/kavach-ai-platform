/**
 * Generic "type something -> check it -> show ResultCard" screen.
 * The URL and SMS screens are just thin configs around this.
 */
import { useState } from "react";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet, Text, TextInput } from "react-native";
import type { CheckResult } from "../api/client";
import { colors } from "../theme/colors";
import ResultCard from "./ResultCard";

interface Props {
  title: string;
  placeholder: string;
  multiline?: boolean;
  onCheck: (value: string) => Promise<CheckResult>;
}

export default function CheckScreen({ title, placeholder, multiline, onCheck }: Props) {
  const [value, setValue] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CheckResult | null>(null);

  async function run() {
    if (!value.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await onCheck(value.trim()));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <ScrollView style={styles.page} contentContainerStyle={{ padding: 16 }} keyboardShouldPersistTaps="handled">
      <Text style={styles.title}>{title}</Text>
      <TextInput
        style={[styles.input, multiline && { minHeight: 120, textAlignVertical: "top" }]}
        value={value}
        onChangeText={setValue}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        autoCapitalize="none"
        autoCorrect={false}
        multiline={multiline}
      />
      <Pressable style={styles.button} onPress={run} disabled={loading}>
        {loading ? <ActivityIndicator color="#000" /> : <Text style={styles.buttonText}>Check</Text>}
      </Pressable>
      {error && <Text style={styles.error}>⚠ {error} — is the backend running and the API URL correct?</Text>}
      {result && <ResultCard result={result} />}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bg },
  title: { color: colors.text, fontSize: 20, fontWeight: "700", marginBottom: 12 },
  input: { backgroundColor: colors.card, color: colors.text, borderColor: colors.border, borderWidth: 1, borderRadius: 10, padding: 12, fontSize: 15 },
  button: { backgroundColor: colors.accent, borderRadius: 10, padding: 14, alignItems: "center", marginTop: 12 },
  buttonText: { color: "#000", fontWeight: "700", fontSize: 16 },
  error: { color: colors.dangerous, marginTop: 12 },
});
