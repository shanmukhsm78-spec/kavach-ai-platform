/** Check URL screen -> POST /protect/url */
import { checkUrl } from "../src/api/client";
import CheckScreen from "../src/components/CheckScreen";

export default function CheckUrl() {
  return (
    <CheckScreen
      title="Is this link safe?"
      placeholder="https://example.com/login"
      onCheck={(v) => checkUrl(v)}
    />
  );
}
