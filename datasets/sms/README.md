# Scam SMS sample set

`sms_samples.csv` - 42 messages (22 scam, 20 ham), English + Hindi, **written
by hand in the style of real Indian scams** (digital arrest, KYC/UPI, OTP theft,
lottery, job, loan, "hi mom"). Phone numbers/links are fake.

Expand with:
- UCI SMS Spam Collection (https://archive.ics.uci.edu/dataset/228/sms+spam+collection)
- Kaggle "Indian SMS spam" style datasets
- Government advisories: cybercrime.gov.in, Sanchar Saathi "Chakshu" reports

## Real benchmark (`benchmark.csv`)
Built by `make protect-download` on 2026-10-21.
- **Source:** SMS Spam Collection v.1, T. A. Almeida & J. M. Gómez Hidalgo (2011), UCI id 228,
  https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip — **CC BY 4.0**.
- **Rows:** all 5,574 messages (747 spam → `scam`, 4,827 `ham`); `split` = stratified 80/20, seed 42.
- Not Indian-context (UK/Singapore, ~2010). `sms_samples.csv` stays separate and is **synthetic**; it is never mixed into the benchmark.
