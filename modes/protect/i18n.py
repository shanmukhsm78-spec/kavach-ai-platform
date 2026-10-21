"""English + Hindi warning templates for Protect mode (no paid translation API).

Every reason a detector can emit has a stable *code*. We keep the human text
in this table so explanations are always available in both languages and the
student can add more languages (e.g. Telugu) by adding one more column.
"""
from __future__ import annotations

# code -> {lang: text}
REASONS: dict[str, dict[str, str]] = {
    # ---- URL ----
    "ip_host": {"en": "The link uses a raw IP address instead of a website name.",
                "hi": "लिंक में वेबसाइट नाम की जगह सीधा IP पता है।"},
    "at_symbol": {"en": "The link contains '@', which can hide the real destination.",
                  "hi": "लिंक में '@' है, जो असली पते को छिपा सकता है।"},
    "punycode": {"en": "The domain uses punycode (xn--), often used for look-alike letters.",
                 "hi": "डोमेन में punycode (xn--) है, जो नकली मिलते-जुलते अक्षरों के लिए इस्तेमाल होता है।"},
    "no_https": {"en": "The site does not use a secure HTTPS connection.",
                 "hi": "साइट सुरक्षित HTTPS कनेक्शन का उपयोग नहीं करती।"},
    "suspicious_tld": {"en": "The domain ends in a cheap TLD commonly abused by scammers.",
                       "hi": "डोमेन का अंत ऐसे सस्ते TLD से होता है जिसका स्कैमर अक्सर दुरुपयोग करते हैं।"},
    "shortener": {"en": "The link is shortened, so the real destination is hidden.",
                  "hi": "लिंक छोटा (short) किया गया है, असली पता छिपा है।"},
    "many_subdomains": {"en": "The address has an unusually large number of subdomains.",
                        "hi": "पते में असामान्य रूप से बहुत सारे सबडोमेन हैं।"},
    "typosquat": {"en": "The domain looks like a misspelling of a well-known brand.",
                  "hi": "डोमेन किसी प्रसिद्ध ब्रांड की गलत वर्तनी जैसा दिखता है।"},
    "brand_not_owner": {"en": "A famous brand name appears in the link but the site is not owned by that brand.",
                        "hi": "लिंक में प्रसिद्ध ब्रांड का नाम है, लेकिन साइट उस ब्रांड की नहीं है।"},
    "long_url": {"en": "The link is unusually long.", "hi": "लिंक असामान्य रूप से लंबा है।"},
    "many_hyphens": {"en": "The domain has many hyphens, common in fake sites.",
                     "hi": "डोमेन में कई हाइफ़न हैं, जो नकली साइटों में आम है।"},
    "sensitive_words": {"en": "The link contains words like 'login', 'verify' or 'kyc' used to steal credentials.",
                        "hi": "लिंक में 'login', 'verify' या 'kyc' जैसे शब्द हैं जो जानकारी चुराने के लिए इस्तेमाल होते हैं।"},
    "non_std_port": {"en": "The link uses a non-standard port.", "hi": "लिंक एक असामान्य पोर्ट का उपयोग करता है।"},
    "trusted_domain": {"en": "The domain belongs to a well-known trusted organisation.",
                       "hi": "यह डोमेन एक जाने-माने विश्वसनीय संगठन का है।"},
    # ---- SMS ----
    "digital_arrest": {"en": "Mentions police/CBI/'digital arrest'. Real police never arrest or demand money over a call.",
                       "hi": "पुलिस/CBI/'डिजिटल अरेस्ट' का ज़िक्र है। असली पुलिस कभी फ़ोन पर गिरफ़्तारी या पैसे की मांग नहीं करती।"},
    "kyc": {"en": "Asks you to update KYC or says your account will be blocked.",
            "hi": "KYC अपडेट करने या खाता बंद होने की बात कही गई है।"},
    "otp": {"en": "Asks you to share an OTP/PIN. Never share an OTP with anyone.",
            "hi": "OTP/PIN मांगा गया है। OTP कभी किसी के साथ साझा न करें।"},
    "lottery": {"en": "Claims you won a lottery/prize/cashback you never entered.",
                "hi": "ऐसी लॉटरी/इनाम/कैशबैक जीतने का दावा जिसमें आपने भाग नहीं लिया।"},
    "upi_collect": {"en": "Asks you to approve a UPI request or scan a QR to 'receive' money.",
                    "hi": "पैसे 'पाने' के लिए UPI अनुरोध स्वीकार करने या QR स्कैन करने को कहा गया है।"},
    "job_scam": {"en": "Offers easy work-from-home money or asks for a registration fee.",
                 "hi": "घर बैठे आसान कमाई या रजिस्ट्रेशन फ़ीस की मांग।"},
    "loan_scam": {"en": "Offers an instant pre-approved loan with no documents.",
                  "hi": "बिना दस्तावेज़ तुरंत प्री-अप्रूव्ड लोन का ऑफ़र।"},
    "utility_cutoff": {"en": "Threatens to cut electricity/gas tonight - utilities never do this by SMS from a mobile number.",
                       "hi": "आज रात बिजली/गैस काटने की धमकी - असली विभाग मोबाइल नंबर से ऐसा SMS नहीं भेजते।"},
    "family_impersonation": {"en": "Pretends to be a family member on a 'new number' asking for money. Call them on their old number first.",
                             "hi": "'नए नंबर' से परिवार का सदस्य बनकर पैसे मांग रहा है। पहले उनके पुराने नंबर पर कॉल करें।"},
    "urgency": {"en": "Creates urgency ('immediately', 'within 24 hours') to rush you.",
                "hi": "जल्दबाज़ी पैदा करता है ('तुरंत', '24 घंटे में')।"},
    "contains_link": {"en": "Contains a link; do not open links from unknown senders.",
                      "hi": "इसमें लिंक है; अनजान भेजने वालों के लिंक न खोलें।"},
    "phishing_link": {"en": "The link inside the message itself looks like phishing.",
                      "hi": "संदेश में दिया गया लिंक खुद फ़िशिंग जैसा लगता है।"},
    "ml_scam": {"en": "The language model trained on scam samples rates this as scam-like.",
                "hi": "स्कैम नमूनों पर प्रशिक्षित मॉडल इसे स्कैम जैसा मानता है।"},
    # ---- VOICE ----
    "too_steady_volume": {"en": "Volume is unnaturally steady (real speech rises and falls).",
                          "hi": "आवाज़ का स्तर अस्वाभाविक रूप से एक जैसा है (असली बोली ऊपर-नीचे होती है)।"},
    "no_pauses": {"en": "Almost no natural pauses/breaths were found.",
                  "hi": "लगभग कोई स्वाभाविक ठहराव/साँस नहीं मिली।"},
    "too_clean": {"en": "No background noise at all, typical of synthetic audio.",
                  "hi": "बिल्कुल भी पृष्ठभूमि शोर नहीं, जो कृत्रिम ऑडियो में आम है।"},
    "flat_pitch": {"en": "Pitch/tone barely changes, which sounds robotic.",
                   "hi": "स्वर (पिच) लगभग नहीं बदलता, जो रोबोटिक लगता है।"},
    "natural_audio": {"en": "Audio shows natural variation in volume, pauses and noise.",
                      "hi": "ऑडियो में आवाज़, ठहराव और शोर में स्वाभाविक बदलाव है।"},
}

VERDICT_TEXT = {
    "safe": {"en": "Looks safe.", "hi": "सुरक्षित लगता है।"},
    "suspicious": {"en": "Be careful - this looks suspicious.", "hi": "सावधान रहें - यह संदिग्ध लगता है।"},
    "dangerous": {"en": "Danger! This is very likely a scam. Do not click, pay or share anything.",
                  "hi": "ख़तरा! यह लगभग निश्चित रूप से स्कैम है। कुछ भी क्लिक, भुगतान या साझा न करें।"},
}

HELPLINE = {"en": "Report cyber fraud: call 1930 or visit cybercrime.gov.in.",
            "hi": "साइबर धोखाधड़ी की शिकायत: 1930 पर कॉल करें या cybercrime.gov.in पर जाएँ।"}


def reason_text(code: str, lang: str = "en") -> str:
    return REASONS.get(code, {}).get(lang) or REASONS.get(code, {}).get("en", code)


def build_explanation(verdict: str, codes: list[str]) -> dict[str, str]:
    """Plain-language explanation in every supported language."""
    out = {}
    for lang in ("en", "hi"):
        parts = [VERDICT_TEXT[verdict][lang]]
        parts += [reason_text(c, lang) for c in codes]
        if verdict != "safe":
            parts.append(HELPLINE[lang])
        out[lang] = " ".join(parts)
    return out
