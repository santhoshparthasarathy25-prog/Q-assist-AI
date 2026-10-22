"""Small held-out style check: fresh questions that were NOT used to tune thresholds/stop-words.
(Once you tune against these, they stop being held out - keep results honest.)"""
import dataclasses
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config.settings import get_settings  # noqa: E402
from src.llm.llm_service import LLMService  # noqa: E402
from src.rag.rag_pipeline import RagPipeline  # noqa: E402
from src.services.receptionist_service import ReceptionistService  # noqa: E402

F, A, P, D = ("sample_clinic_faq.txt", "sample_appointment_policy.txt", "sample_prescription_policy.txt", "sample_admin_policy.txt")
QS = [("Is there a hearing loop?", F), ("Where can I find the surgery's address?", F),
      ("How far ahead can I book a routine appointment?", A), ("What happens if I arrive late?", A),
      ("Can I change my nominated pharmacy?", P), ("How do I make a complaint?", D),
      ("How do I register as a new patient?", D), ("What should I do in an emergency?", F),
      ("Do you do blood tests?", None), ("Can you recommend a good restaurant?", None),
      ("What is the price of a flu jab?", None), ("Do you have a dentist?", None)]

s = dataclasses.replace(get_settings(), gemini_api_key="")
rag = RagPipeline(s); rag.ingest()
svc = ReceptionistService(rag, LLMService(s), s)
ok = 0
for q, exp in QS:
    r = svc.handle(q, persist=False)
    got = [x["source"] for x in r.sources]
    good = (exp in got) if exp else r.response_type == "fallback"
    ok += good
    print("OK " if good else "MISS", q, "->", r.response_type, got[:2], round(r.best_score, 3))
print(f"{ok}/{len(QS)} correct (answerable: expected source retrieved; unanswerable: fallback returned)")
