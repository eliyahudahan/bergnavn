
## 🧾 Weekly Log – Migration Issue and Resolution (Week of July 1, 2025)

### ⚠️ Issue Summary: Multiple Alembic Heads

While attempting to run:
```bash
flask db migrate -m "Add nullable departure_port_id and arrival_port_id to voyage_legs"

we encountered the following error:
Error: Multiple heads are present; please specify the head revision on which the new revision should be based, or perform a merge.

🧠 Root Cause:
Alembic detected multiple "head" revisions — this happens when multiple migration branches exist in parallel (e.g., due to running migrations in different branches or out of order). Alembic cannot determine the correct base revision for generating a new one.
🔧 Solution – Step-by-Step:
Check existing heads:

 flask db heads
 Output:

 446d55e96113 (head)
631b182f345c (head)


Merge the heads:

 flask db merge -m "Merge all heads before adding port_id columns" 446d55e96113 631b182f345c


Apply the merged migration:

 flask db upgrade


Generate the new intended migration:

 flask db migrate -m "Add nullable departure_port_id and arrival_port_id to voyage_legs"
flask db upgrade


Confirm DB structure is intact:


Ran python app.py
Verified route display via /api/routes/view
System remained stable with no schema or data loss
✅ Outcome:
Database migration structure was repaired and merged
New migration successfully added foreign keys to voyage_legs
Application routes loaded without errors
Git backup committed successfully

🕊️ "Persistence is stronger than any setback."