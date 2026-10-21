// Kavach Shield popup: checks the active tab URL (and any selected text)
// against the local Kavach backend and renders the verdict.
const API = "http://localhost:8000/protect";

function render(box, title, data, lang) {
  const reasons = (data.reasons || [])
    .map((r) => `<li>${r[lang] || r.en}</li>`).join("");
  box.innerHTML =
    `<b>${title}</b> <span class="badge ${data.verdict}">${data.verdict}</span> ` +
    `risk ${data.risk_score}/100<ul>${reasons}</ul><small>${data.explanation[lang]}</small>`;
}

async function post(path, body) {
  const res = await fetch(`${API}/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

async function run() {
  const lang = document.getElementById("hindi").checked ? "hi" : "en";
  const urlBox = document.getElementById("url-box");
  const smsBox = document.getElementById("sms-box");
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  try {
    render(urlBox, "This page", await post("url", { url: tab?.url || "", language: lang }), lang);
  } catch (e) {
    urlBox.textContent = "Kavach backend not reachable on localhost:8000 (run `make backend`).";
    return;
  }

  // Grab the user's text selection from the page (needs activeTab + scripting).
  try {
    const [{ result: selected }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => window.getSelection().toString(),
    });
    if (selected && selected.trim()) {
      render(smsBox, "Selected text", await post("sms", { text: selected.slice(0, 2000), language: lang }), lang);
    }
  } catch (e) {
    // chrome:// pages etc. block scripting — just keep the hint text.
  }
}

document.getElementById("hindi").addEventListener("change", run);
run();
