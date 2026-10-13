---
name: sarcoscan-docs-sync
description: Keeps the SarcoScan docs, skills, and README true after a change. Use at the end of any task that added or changed an endpoint, a table or column, a security control, a model or dataset, a screen, a folder, a dependency, or a team decision, and whenever asked to update or check the docs.
---

# Keeping SarcoScan docs in sync

The docs describe the plan and what has been built. They are only useful while they are true. Fix them in the same change that made them wrong.

## Which file to update

| What changed | Update |
|---|---|
| Endpoint added, changed, finished, or dropped | `docs/API.md` (row and status) |
| Table or column added or changed | `docs/DATABASE.md` |
| Security control built or changed | `docs/SECURITY.md` (the section and the checklist row) |
| Model trained, evaluated, or exported; dataset added | `docs/ML.md` (status table, dataset table, Results table); the folder tree in `ml/README.md` if a dataset folder was added |
| Screen built; anything about PWA or the shells | `docs/FRONTEND.md` |
| A part added, removed, or swapped (framework, storage, queue) | `docs/ARCHITECTURE.md` ("Parts", "What we build first", "Decisions") |
| Task finished, or a new task appears | `docs/PLAN.md` (tick or add the box) |
| A team decision made or reversed | "Decisions" in `docs/ARCHITECTURE.md`, and "Open questions" in `docs/PLAN.md` |
| Folder added, moved, or renamed; owner changed | `README.md` layout table, `AGENTS.md` owner table, the folder's own `README.md` |
| A working rule for an area changed | The matching `SKILL.md` in `.claude/skills/`, and `AGENTS.md` if the rule applies to everyone |
| Anything that changes what may be claimed | `docs/PITCH.md` |
| Setup or run commands changed | The folder's own `README.md` |

## How to update

1. Change the fact where it lives. Each fact has one home; other files link to it. Do not copy a table into a second file.
2. Use the three statuses only: `planned`, `in progress`, `done` (plus `later` and `dropped` in `docs/API.md`). Mark something `done` only after it was run and seen working.
3. Set "Last updated" at the top of each doc you touched to today's date.
4. Do not describe unbuilt things as if they exist.
5. Do not add a number that was not measured. Measured results go in the Results table in `docs/ML.md` and nowhere else first.

## Checks when asked to review the docs

- Every route in `backend/routers/` has a row in `docs/API.md`, and every row marked `done` has a route.
- Every table in `backend/models.py` matches `docs/DATABASE.md`.
- Every `done` row in the `docs/SECURITY.md` checklist can be pointed to in the code.
- Every model file in `ml/models/` has a row in the Results table.
- Every ticked box in `docs/PLAN.md` is true.
- The layout table in `README.md` matches the folders that exist.
- The spec PDF named in `README.md` and `AGENTS.md` is the one in `docs/`.

Report what was out of date and what you changed. If a doc and the code disagree and it is not clear which is right, ask the owner named at the top of the doc.
