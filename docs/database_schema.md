# Database schema

SQLite file: **`data/storage/qassist.db`** (created automatically on first start, or with `python scripts/init_database.py`). Diagram source: [`database_erd.mmd`](database_erd.mmd).

| Table | Purpose | Key constraints |
|---|---|---|
| conversations | one chat session | PK id; index session_id, started_at |
| messages | user/assistant turns | FK conversation_id (cascade); CHECK role IN ('user','assistant') |
| intent_records | classification + outcome per user message | FK message_id UNIQUE; indexes on label, answer_mode, created_at |
| source_records | retrieved chunks cited for a message | FK message_id; index source |
| admin_requests | simulated workflow request | FK message_id; `simulated` flag; indexes type/status |
| escalation_events | urgent/human escalations | FK message_id; `reason` is a category only |
| evaluation_runs / evaluation_results | saved evaluation runs | FK run_id (cascade) |

Privacy: no API keys stored; obvious emails/phones/NHS numbers/dates/postcodes are redacted; urgent messages are stored as `[urgent message - content not stored]`. `rule_matches` is a count of matched rules, not a probability.

Reset demo data: `python scripts/reset_demo_data.py --yes`, the Dashboard "Reset demo data" button, or delete `data/storage/qassist.db`.

## Example SQL (used by `repository.py`)
```sql
-- Total enquiries / conversations / escalations
SELECT COUNT(DISTINCT m.conversation_id), COUNT(*), SUM(i.escalation_required)
FROM intent_records i JOIN messages m ON m.id = i.message_id;

-- Intent distribution
SELECT label, COUNT(*) FROM intent_records GROUP BY label ORDER BY 2 DESC;

-- Request status distribution (simulated workflows)
SELECT status, COUNT(*) FROM admin_requests GROUP BY status;

-- LLM vs demo vs fixed-rule usage
SELECT answer_mode, COUNT(*) FROM intent_records GROUP BY answer_mode;

-- Source retrieval statistics
SELECT source, COUNT(*) AS retrievals, ROUND(AVG(score),3) FROM source_records GROUP BY source;
```
