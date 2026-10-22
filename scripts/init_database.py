"""Create the SQLite database (if missing). Use --seed to add synthetic sample conversations."""
import argparse

import _bootstrap  # noqa: F401
from config.settings import get_settings
from src.database.init_db import init_db, seed_demo_data


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", action="store_true", help="replay synthetic questions from data/seed/sample_data.json")
    a = ap.parse_args()
    s = get_settings()
    engine = init_db()
    print(f"Database ready at: {s.db_path}")
    if a.seed:
        from src.database.repository import Repository
        from src.llm.llm_service import LLMService
        from src.rag.rag_pipeline import RagPipeline
        from src.services.conversation_service import ConversationService
        from src.services.receptionist_service import ReceptionistService
        import dataclasses
        s_demo = dataclasses.replace(s, gemini_api_key="")  # seed deterministically, never calls the API
        repo = Repository(engine)
        rag = RagPipeline(s_demo); rag.ingest()
        n = seed_demo_data(ReceptionistService(rag, LLMService(s_demo), s_demo, repo), ConversationService(repo))
        print(f"Seeded {n} synthetic questions.")


if __name__ == "__main__":
    main()
