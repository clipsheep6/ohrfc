# Phase: FINALIZE

> Export derivatives, archive process artifacts, lock baseline.
> **Input**: baseline_accepted = true + rfc.md + evidence.json
> **Output**: Archived workspace with optional derivative exports

## Prerequisites

No reference files required by the orchestrator. Export sub-agent loads `references/methodology.md §4` (ID system) if needed for ID validation.

## Context Loading

No additional references required.

## Execution

1. **Export derivatives** (as needed):
   - Extract SCN chapter → `tasks.md` (acceptance test task list)
   - Generate acceptance checklist from must-pass set → `verification_checklist.md`
   - Other project-specific exports per user request

2. **Archive process artifacts**:
   - Ensure `.debug/events.jsonl` preserved (truncation/timeout audit trail)
   - Ensure `.reviews/summary.json` preserved (Gate-B final result)
   - Ensure `evidence.json` preserved (evidence chain)

3. **Lock normative content**:
   - Do NOT modify rfc.md normative content
   - Update state.json: `current_phase: "finalize"`

## Task Export (optional)

When task export is requested or configured:

**Reference**: Read `references/task_format.md` for the 6-field task specification (scope, depends, acceptance, invariants, context, on-ambiguity).

### Generation Process

1. **Parse & group**: Parse rfc.md §11 acceptance chapter → group SCN-### by module/component affinity
2. **Create tasks**: For each group, create a TASK-### with:

| rfc.md Section | Task Field | What to Extract |
|----------------|------------|-----------------|
| §6 (Impact/Scope) | `scope.modify` | Affected files/modules mapped to grouped SCNs |
| §4.2 (Non-goals) + adjacent | `scope.boundary` | Out-of-scope modules and boundaries |
| Inter-task analysis | `depends` | Data/control flow dependencies between tasks |
| §11 (Acceptance) | `acceptance` | SCN-### in WHEN/THEN format, filtered by task scope |
| §8.1 / §9.1 / §9.4 (Rules/Invariants) | `invariants` | SEC-HR / REL-HR / INV relevant to task scope |
| §1 TL;DR + §7 (Decisions) | `context` | DEC-### excerpts + historical rationale |
| §7.1 (Open Questions) | `on-ambiguity` | Hard/Soft unresolved items affecting task scope |

3. **Extract must-pass set**: Filter SCN list for must-pass items → write to `.ohrfc/<rfc_id>/verification_checklist.md`
   - Format: markdown checklist with SCN-### ID, category, and one-line description

4. **Write output**: `.ohrfc/<rfc_id>/tasks.md` — Markdown by default. Future option: configurable export targets (Jira/Linear/GitHub Issues) via export adapter.

5. **Traceability**: Append `<!-- TRACE: §section → TASK-###.field -->` comments at end of tasks.md (see task_format.md §4).

## Hard Rule

After baseline accepted, modifying rfc.md requires baseline change flow:
CHG-### + DEC-### → Gate-A → Gate-B → human re-approval.
