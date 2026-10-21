# Kavach Shield — Browser Extension (MV3 demo)

Load unpacked in Chrome/Edge: `chrome://extensions` → Developer mode → **Load unpacked** → select this folder.
Start the backend first (`make backend`, default `http://localhost:8000`).

Open the popup on any page:
- the current page URL is sent to `POST /protect/url`;
- any text you selected on the page is sent to `POST /protect/sms`;
- tick **हिंदी** to see the warnings in Hindi.

Nothing is sent until you click the extension icon (privacy-friendly by design).
