"""Delete all demo conversations/evaluations and recreate empty tables."""
import argparse

import _bootstrap  # noqa: F401
from config.settings import get_settings
from src.database.init_db import reset_db


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes", action="store_true", help="skip confirmation")
    a = ap.parse_args()
    if not a.yes and input("This deletes ALL demo data. Type 'yes' to continue: ").strip().lower() != "yes":
        print("Cancelled.")
        return
    reset_db()
    print(f"Demo data reset: {get_settings().db_path}")


if __name__ == "__main__":
    main()
