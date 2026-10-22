"""Index (or re-index) knowledge-base documents. Use --force to rebuild even if nothing changed."""
import argparse

import _bootstrap  # noqa: F401
from config.settings import get_settings
from src.rag.rag_pipeline import RagPipeline


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    rag = RagPipeline(get_settings())
    print(rag.backend_note)
    print(rag.ingest(force=a.force))
    for w in rag.warnings:
        print("WARNING:", w)


if __name__ == "__main__":
    main()
