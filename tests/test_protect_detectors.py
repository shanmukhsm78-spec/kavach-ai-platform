"""Protect mode tests - fully offline and deterministic (KAVACH_LLM=off)."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from modes.protect import check
from modes.protect.evaluate import eval_sms, eval_url, eval_voice

VOICE = Path(__file__).resolve().parents[1] / "datasets" / "voice"


@pytest.mark.parametrize("url", [
    "http://192.168.45.10/sbi/login.php", "http://sbi-kyc-update.xyz/verify",
    "https://paypa1.com/signin", "http://www.google.com@evil-site.tk/login",
    "https://xn--pple-43d.com/id", "http://hdfcbank.secure-login.top/account"])
def test_phishing_urls_dangerous(url):
    r = check("url", url)
    assert r["verdict"] == "dangerous" and r["risk_score"] >= 65 and r["reasons"]


@pytest.mark.parametrize("url", [
    "https://www.onlinesbi.sbi/", "https://www.hdfcbank.com/personal",
    "https://github.com/OWASP/juice-shop", "https://cybercrime.gov.in/"])
def test_legit_urls_safe(url):
    assert check("url", url)["verdict"] == "safe"


@pytest.mark.parametrize("text", [
    "This is Mumbai Cyber Cell. You are under digital arrest, transfer money to verify.",
    "Dear customer your SBI account will be blocked today. Update KYC immediately at http://sbi-kyc-update.xyz/verify",
    "Bank executive here, please share the OTP sent to your phone.",
    "Scan the QR code and enter your UPI PIN to receive your refund."])
def test_scam_sms_flagged(text):
    assert check("sms", text)["verdict"] in ("suspicious", "dangerous")


@pytest.mark.parametrize("text", [
    "Your OTP for login is 482913. Do not share it with anyone. -SBI",
    "Hey, are we still meeting at the library at 4 for the project review?",
    "Mom: dinner is ready, come home soon."])
def test_ham_sms_allowed(text):
    assert check("sms", text)["verdict"] == "safe"


def test_bilingual_explanation():
    r = check("sms", "Your KYC expired, account will be blocked")
    assert r["explanation"]["en"] and r["explanation"]["hi"]
    assert any("\u0900" <= ch <= "\u097f" for ch in r["explanation"]["hi"])
    assert "llm" not in r["explanation"]          # offline: no LLM layer


def test_audio_returns_score():
    real = check("audio", str(VOICE / "real" / "real_1.wav"))
    fake = check("audio", str(VOICE / "fake" / "fake_1.wav"))
    assert 0 <= real["risk_score"] <= 100 and real["verdict"] == "safe"
    assert fake["verdict"] == "dangerous" and fake["risk_score"] > real["risk_score"]


def test_sample_accuracy(capsys):
    url, sms, voice = eval_url(), eval_sms(), eval_voice()
    with capsys.disabled():
        print(f"\n[protect] URL acc={url['accuracy']}  SMS(rules+NB, LOO) acc={sms['rules+nb_loo']['accuracy']}"
              f"  SMS(rules) acc={sms['rules_only']['accuracy']}  voice acc={voice['accuracy']}")
    assert url["accuracy"] >= 0.9
    assert sms["rules+nb_loo"]["accuracy"] >= 0.8
    assert voice["accuracy"] >= 0.75


def test_api_routes(tmp_path, monkeypatch):
    monkeypatch.setenv("KAVACH_PROTECT_DIR", str(tmp_path))
    from app.main import app
    c = TestClient(app)
    assert c.post("/protect/url", json={"url": "http://bit.ly/3kycUpdate"}).json()["verdict"] != "safe"
    assert c.post("/protect/sms", json={"text": "You have won a lottery prize!"}).status_code == 200
    with open(VOICE / "fake" / "fake_2.wav", "rb") as fh:
        r = c.post("/protect/audio", files={"file": ("x.wav", fh, "audio/wav")})
    assert r.status_code == 200 and "risk_score" in r.json()
    assert c.post("/protect/audio", data={"path": "datasets/voice/real/real_2.wav"}).status_code == 200
    assert c.post("/protect/audio", data={"path": "/etc/passwd"}).status_code == 400
    s = c.get("/protect/stats").json()
    assert s["total"] == 4 and len(s["recent"]) == 4
