"""Run the suite, rerun failures to tell flaky from consistent, and write a triage report.

Usage:  .venv\\Scripts\\python.exe scripts\\triage.py [extra pytest args, e.g. -m api]
Output: reports/triage.json (for the triage-suite skill) and reports/triage.md (for humans).
Exit:   0 if the suite is green (no failures/errors), 1 otherwise.

The script only collects facts. Judgment (PR check, quarantine, fix, delete) is in
.claude/skills/triage-suite/SKILL.md.
"""
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORTS = ROOT / "reports"
RERUN_ATTEMPTS = 2  # small on purpose: the API budget is a few hundred calls in total
CATEGORIES = {"tests/api/": "api", "tests/ui/": "ui (e2e)"}


def run_pytest(args: list[str], junit_path: Path) -> None:
    # xunit1 keeps the "file" attribute on each testcase, which we need to rebuild node ids.
    cmd = [sys.executable, "-m", "pytest", *args, f"--junitxml={junit_path}", "-o", "junit_family=xunit1", "-q", "-p", "no:warnings"]
    subprocess.run(cmd, cwd=ROOT)


def category_of(node_id: str) -> str:
    return next((name for prefix, name in CATEGORIES.items() if node_id.startswith(prefix)), "other")


def parse_junit(junit_path: Path) -> list[dict]:
    results = []
    for case in ET.parse(junit_path).getroot().iter("testcase"):
        file = case.get("file", "").replace("\\", "/")
        class_name = case.get("classname", "").split(".")[-1]
        parts = [file] + ([class_name] if class_name.startswith("Test") else []) + [case.get("name")]
        node_id = "::".join(parts)

        outcome, message = "passed", ""
        for tag in ("failure", "error", "skipped"):
            element = case.find(tag)
            if element is not None:
                message = (element.get("message") or "").strip()
                outcome = {"failure": "failed", "error": "error"}.get(tag, "skipped")
                if tag == "skipped" and element.get("type") == "pytest.xfail":
                    outcome = "quarantined" if "QUARANTINED" in message else "xfailed"
                break
        results.append({
            "node_id": node_id,
            "category": category_of(node_id),
            "outcome": outcome,
            "duration_s": round(float(case.get("time", 0)), 2),
            "message": message[:300],
        })
    return results


def rerun_failures(failures: list[dict]) -> None:
    """Rerun only the failed tests; mark each flaky (passed at least once) or consistent."""
    node_ids = [f["node_id"] for f in failures]
    passes = {node_id: 0 for node_id in node_ids}
    for attempt in range(1, RERUN_ATTEMPTS + 1):
        junit = REPORTS / f"rerun-{attempt}.xml"
        run_pytest(node_ids, junit)
        for result in parse_junit(junit):
            if result["node_id"] in passes and result["outcome"] == "passed":
                passes[result["node_id"]] += 1
    for failure in failures:
        failure["reruns_passed"] = f"{passes[failure['node_id']]}/{RERUN_ATTEMPTS}"
        failure["classification"] = "flaky" if passes[failure["node_id"]] else "consistent"


def one_line(text: str, limit: int = 120) -> str:
    """First line only, pipes escaped, so the message fits in a Markdown table cell."""
    return text.splitlines()[0][:limit].replace("|", "\\|") if text else ""


def write_markdown(summary: dict, path: Path) -> None:
    lines = [f"# Suite triage: {'GREEN' if summary['green'] else 'NOT GREEN'}", "",
             f"Run at {summary['run_at']} · pytest args: `{' '.join(summary['pytest_args']) or '(full suite)'}`", "",
             "| Category | Passed | Failed | Known gaps (xfail) | Quarantined | Skipped |",
             "|---|---|---|---|---|---|"]
    for category, counts in summary["by_category"].items():
        lines.append(f"| {category} | {counts['passed']} | {counts['failed']} | {counts['xfailed']} | {counts['quarantined']} | {counts['skipped']} |")
    for category in summary["by_category"]:
        lines += ["", f"## {category}", ""]
        for r in (r for r in summary["results"] if r["category"] == category):
            lines.append(f"- `{r['outcome']}` {r['node_id']} ({r['duration_s']}s)")
    if summary["failures"]:
        lines += ["", "## Failures", "", "| Test | Classification | Reruns passed | Message |", "|---|---|---|---|"]
        for f in summary["failures"]:
            lines.append(f"| {f['node_id']} | {f['classification']} | {f['reruns_passed']} | {one_line(f['message'])} |")
        lines += ["", "_Root cause, PR check and actions: see the triage-suite skill report._"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    pytest_args = sys.argv[1:]
    REPORTS.mkdir(exist_ok=True)

    run_pytest(pytest_args, REPORTS / "run.xml")
    results = parse_junit(REPORTS / "run.xml")
    failures = [r for r in results if r["outcome"] in ("failed", "error")]
    if failures:
        rerun_failures(failures)

    by_category = {}
    for r in results:
        counts = by_category.setdefault(r["category"], dict.fromkeys(["passed", "failed", "xfailed", "quarantined", "skipped"], 0))
        counts["failed" if r["outcome"] == "error" else r["outcome"]] += 1

    summary = {
        "run_at": datetime.now().isoformat(timespec="seconds"),
        "pytest_args": pytest_args,
        "green": not failures,
        "by_category": by_category,
        "results": results,
        "failures": failures,
    }
    (REPORTS / "triage.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown(summary, REPORTS / "triage.md")
    print(f"\nTriage: {'GREEN' if summary['green'] else 'NOT GREEN'} -> reports/triage.md, reports/triage.json")
    return 0 if summary["green"] else 1


if __name__ == "__main__":
    sys.exit(main())
