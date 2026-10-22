"""Run the evaluation scenarios and print metrics. Optional: --save stores the run in SQLite."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import get_settings  # noqa: E402
from src.rag.rag_pipeline import RagPipeline  # noqa: E402
from src.services.evaluation_service import run_evaluation  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--save", action="store_true", help="store results in the SQLite database")
    ap.add_argument("--json", action="store_true", help="print full JSON report")
    a = ap.parse_args()
    rag = RagPipeline(get_settings())
    print("Indexing:", rag.ingest())
    report = run_evaluation(rag)
    if a.json:
        print(json.dumps(report, indent=1, default=str))
    print(f"\nScenarios passed: {report['passed']}/{report['total']}")
    for k, v in report["metrics"].items():
        if k != "counts":
            print(f"  {k}: {v}")
    print("\nFailures:")
    fails = [r for r in report["results"] if not r["passed"]]
    for r in fails:
        print(f"  {r['id']} [{r['category']}] {r['question'][:50]!r}: {r['detail']}")
    if not fails:
        print("  none")
    if a.save:
        from src.database.init_db import init_db
        from src.database.repository import Repository
        run_id = Repository(init_db()).save_evaluation(report)
        print(f"Saved as evaluation run #{run_id}")


if __name__ == "__main__":
    main()
