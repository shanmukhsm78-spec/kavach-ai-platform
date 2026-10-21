"""Benchmark files + report generation (skips if `make protect-download` not run)."""
import csv
from pathlib import Path

import pytest

from modes.protect import evaluate

DS = Path(__file__).resolve().parents[1] / "datasets"


@pytest.mark.parametrize("rel,col", [("phishing/benchmark.csv", "url"), ("sms/benchmark.csv", "text")])
def test_benchmark_csv_has_split(rel, col):
    p = DS / rel
    if not p.exists():
        pytest.skip("benchmark not downloaded")
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    assert len(rows) > 1000 and {col, "label", "split"} <= set(rows[0])
    assert {r["split"] for r in rows} == {"train", "test"}


def test_report_written(tmp_path):
    out = evaluate.write_report(tmp_path / "bench.md")
    text = out.read_text(encoding="utf-8")
    assert "held-out" in text and "NOT a benchmark" in text
    if (DS / "sms" / "benchmark.csv").exists():
        assert "Rules + Naive Bayes" in text and "| 1116 |" in text
