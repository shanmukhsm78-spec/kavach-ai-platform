/** Check Message screen -> POST /protect/sms */
import { checkSms } from "../src/api/client";
import CheckScreen from "../src/components/CheckScreen";

export default function CheckSmsScreen() {
  return (
    <CheckScreen
      title="Paste a suspicious message"
      placeholder="e.g. Your KYC has expired, click here within 24 hours..."
      multiline
      onCheck={(v) => checkSms(v)}
    />
  );
}
