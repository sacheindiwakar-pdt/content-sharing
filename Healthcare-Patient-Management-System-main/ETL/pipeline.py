
import json
import subprocess
import sys
import time

from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent
REPORT_DIR = ROOT.parent / "data" / "processed"
REPORT_FILE = REPORT_DIR / "pipeline_report.json"
LOG_FILE = REPORT_DIR / "pipeline.log"

STAGES = [
    ("Extract", "extract.py"),
    ("Validate", "validate.py"),
    ("Clean", "clean.py"),
    ("Transform", "transform.py"),
    ("Test transformed data", "test_transform.py"),
    ("Load into MySQL", "load.py"),
    ("Verify database", "verify_database.py")
]

def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report = {
        "started_at": datetime.now(timezone.utc).isoformat(),
        "status": "RUNNING",
        "stages": []
    }

    with open(LOG_FILE, "w", encoding="utf-8") as log:
        for name, script in STAGES:
            path = ROOT / script
            stage_start = time.perf_counter()

            print(f"\n{'=' * 55}")
            print(f"STAGE: {name}")
            print(f"{'=' * 55}")

            result = {
                "stage": name,
                "script": script,
                "status": "RUNNING"
            }

            if not path.exists():
                result["status"] = "FAILED"
                result["error"] = f"Script not found: {path}"
                report["stages"].append(result)
                report["status"] = "FAILED"
                break

            try:
                process = subprocess.run(
                    [sys.executable, str(path)],
                    cwd=str(ROOT),
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=3600
                )

                output = process.stdout or ""
                error = process.stderr or ""

                if output:
                    print(output, end="" if output.endswith("\n") else "\n")
                    log.write(f"\n--- {name} ---\n{output}\n")

                if error:
                    print(error, end="" if error.endswith("\n") else "\n")
                    log.write(f"\n--- STDERR: {name} ---\n{error}\n")

                result["status"] = (
                    "SUCCESS" if process.returncode == 0 else "FAILED"
                )
                result["return_code"] = process.returncode

                if process.returncode != 0:
                    result["error"] = (
                        error[-3000:] if error else
                        "Stage exited with a non-zero return code."
                    )

            except subprocess.TimeoutExpired:
                result["status"] = "FAILED"
                result["error"] = "Stage exceeded the 1-hour timeout."

            except Exception as exc:
                result["status"] = "FAILED"
                result["error"] = str(exc)

            result["duration_seconds"] = round(
                time.perf_counter() - stage_start, 2
            )
            report["stages"].append(result)

            print(f"Stage status: {result['status']}")
            print(f"Duration: {result['duration_seconds']} seconds")

            if result["status"] != "SUCCESS":
                report["status"] = "FAILED"
                break
        else:
            report["status"] = "SUCCESS"

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["total_duration_seconds"] = round(
        sum(s.get("duration_seconds", 0) for s in report["stages"]), 2
    )

    REPORT_FILE.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print(f"\nPipeline status: {report['status']}")
    print(f"Execution report: {REPORT_FILE}")
    print(f"Execution log: {LOG_FILE}")

    if report["status"] != "SUCCESS":
        sys.exit(1)

if __name__ == "__main__":
    main()
