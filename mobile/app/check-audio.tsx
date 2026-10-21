/**
 * Check Audio screen - PLACEHOLDER.
 * The API call already exists (checkAudio in src/api/client.ts).
 * To finish: `npx expo install expo-document-picker`, pick a .wav,
 * call checkAudio(asset.uri, asset.name), render <ResultCard />.
 */
import { StyleSheet, Text, View } from "react-native";
import { colors } from "../src/theme/colors";

export default function CheckAudio() {
  return (
    <View style={styles.page}>
      <Text style={styles.icon}>🎙️</Text>
      <Text style={styles.title}>Upload a clip</Text>
      <Text style={styles.body}>
        Soon you will be able to upload a .wav voice clip and Kavach will tell you if it
        sounds AI-cloned (e.g. a fake call from a "relative" asking for money).
        {"\n\n"}For now, try voice-clone detection on the web dashboard's Protect page.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  page: { flex: 1, backgroundColor: colors.bg, padding: 24, alignItems: "center", justifyContent: "center" },
  icon: { fontSize: 48 },
  title: { color: colors.text, fontSize: 22, fontWeight: "700", marginVertical: 12 },
  body: { color: colors.muted, textAlign: "center", lineHeight: 22 },
});
