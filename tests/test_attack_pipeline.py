"""End-to-end offline test for Attack mode.

Spins up the bundled deliberately-vulnerable mock target (no Docker / Juice
Shop needed), runs the full Recon → Scanner → Exploit → Reporter pipeline, and
asserts findings + a Markdown and PDF report are produced. The generated
report is copied to docs/sample_report/ as a checked-in sample.
"""
import shutil
from pathlib import Path

import pytest

from modes.attack import pipeline
from modes.attack.mocktarget import run_in_thread
from modes.attack.safety import ScopeError

_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def mock_target():
    base_url, server = run_in_thread()
    yield base_url
    server.should_exit = True


def test_scope_guard_refuses_public_target():
    # Safety: a clearly public host must be refused before any traffic.
    with pytest.raises(ScopeError):
        pipeline.run("http://example.com")


def test_full_pipeline_against_mock_target(mock_target, tmp_path, monkeypatch):
    # Keep the real run output under the repo data dir so paths are realistic,
    # but the sample we publish is copied explicitly below.
    result = pipeline.run(mock_target, scope="web")

    assert result["status"] == "completed"
    assert result["summary_engine"] == "rule-based"  # LLM forced off

    found_ids = {f["check_id"] for f in result["findings"]}
    # The mock target is built to trigger at least these classic issues.
    for expected in {
        "missing_security_headers",
        "reflected_xss",
        "sqli_error_based",
        "exposed_sensitive_endpoint",
        "default_weak_config",
        "directory_listing",
    }:
        assert expected in found_ids, f"Scanner missed {expected}: {found_ids}"

    # Every finding must carry a MITRE technique id.
    for f in result["findings"]:
        assert f["mitre"]["id"].startswith("T")
        assert f["exploit_proof"]  # safe PoC attached

    md = Path(result["report"]["markdown"])
    pdf = Path(result["report"]["pdf"])
    assert md.exists() and md.stat().st_size > 0
    assert pdf.exists() and pdf.read_bytes()[:4] == b"%PDF"

    # Publish a checked-in sample report for the repo / viva.
    sample_dir = _ROOT / "docs" / "sample_report"
    sample_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(md, sample_dir / "attack_report_sample.md")
    shutil.copy(pdf, sample_dir / "attack_report_sample.pdf")
    (sample_dir / "result_sample.json").write_text(
        (Path(result["report"]["dir"]) / "result.json").read_text())
