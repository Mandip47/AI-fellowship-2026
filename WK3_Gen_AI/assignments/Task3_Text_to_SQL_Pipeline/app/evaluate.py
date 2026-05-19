"""
evaluate.py
===========
Runs the benchmark dataset from Task 1 through the Text-to-SQL pipeline
and generates a structured evaluation report (CSV + console table).

Usage:
    python evaluate.py
"""

import csv
import json
import os
import time
from pathlib import Path

from executor import run_pipeline

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BENCHMARK_CSV = Path(__file__).parent.parent.parent / (
    "Task1_SQL_Benchmark_Dataset/"
    "sql_questions_and_answers - sql_questions_answers.csv"
)
REPORT_JSON = Path(__file__).parent.parent / "logs" / "eval_report.json"
REPORT_CSV = Path(__file__).parent.parent / "logs" / "eval_report.csv"

# Columns to write in the CSV report
CSV_COLUMNS = [
    "question",
    "expected_sql",
    "generated_sql",
    "fixed_sql",
    "executed_successfully",
    "retry_attempted",
    "retry_success",
    "final_status",
    "row_count",
    "latency_ms",
    "error",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_benchmark() -> list[dict]:
    """Load the benchmark CSV — handles \r\n line endings."""
    rows = []
    with open(BENCHMARK_CSV, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            q = row.get("questions", "").strip().strip("\r")
            a = row.get("answers", "").strip().strip("\r")
            if q:
                rows.append({"question": q, "expected_sql": a})
    return rows


def _eval_row(item: dict) -> dict:
    """Run one benchmark item through the pipeline and return a report row."""
    result = run_pipeline(item["question"])
    executed_ok = result["status"] == "success"
    return {
        "question": item["question"],
        "expected_sql": item["expected_sql"],
        "generated_sql": result.get("sql") or "",
        "fixed_sql": result.get("fixed_sql") or "",
        "executed_successfully": executed_ok,
        "retry_attempted": result["retry_attempted"],
        "retry_success": result["retry_success"],
        "final_status": result["status"],
        "row_count": (result.get("result") or {}).get("row_count", 0),
        "latency_ms": result["latency_ms"],
        "error": result.get("error") or "",
    }


def _print_summary(report: list[dict]) -> None:
    total = len(report)
    success = sum(1 for r in report if r["executed_successfully"])
    retried = sum(1 for r in report if r["retry_attempted"])
    fixed = sum(1 for r in report if r["retry_success"])
    failed = sum(1 for r in report if r["final_status"] == "failed")

    print("\n" + "=" * 70)
    print("  EVALUATION SUMMARY")
    print("=" * 70)
    print(f"  Total questions      : {total}")
    print(
        f"  Executed successfully: {success}  ({100*success//total if total else 0}%)"
    )
    print(f"  Retry attempted      : {retried}")
    print(f"  Fixed after retry    : {fixed}")
    print(f"  Failed               : {failed}")
    print("=" * 70)

    # Per-question table
    header = f"{'#':<4} {'Status':<10} {'Retry':<6} {'Rows':<6} {'ms':<8} Question"
    print(header)
    print("-" * 70)
    for i, r in enumerate(report, 1):
        retry_flag = "✓" if r["retry_attempted"] else "-"
        print(
            f"{i:<4} {r['final_status']:<10} {retry_flag:<6} "
            f"{r['row_count']:<6} {r['latency_ms']:<8.0f} "
            f"{r['question'][:45]}"
        )
    print("=" * 70)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("Loading benchmark dataset …")
    benchmark = _load_benchmark()
    print(f"Found {len(benchmark)} questions.\n")

    report = []
    for idx, item in enumerate(benchmark, 1):
        print(f"[{idx:>2}/{len(benchmark)}] {item['question'][:60]}")
        row = _eval_row(item)
        report.append(row)
        status_icon = "✓" if row["executed_successfully"] else "✗"
        print(
            f"       {status_icon} {row['final_status']}  ({row['latency_ms']:.0f} ms)"
        )
        # Small pause to avoid rate limiting on free-tier models
        time.sleep(1)

    # Save JSON report
    REPORT_JSON.parent.mkdir(parents=True, exist_ok=True)
    REPORT_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )

    # Save CSV report
    with open(REPORT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(report)

    _print_summary(report)
    print(f"\nJSON report → {REPORT_JSON}")
    print(f"CSV  report → {REPORT_CSV}")


if __name__ == "__main__":
    main()
