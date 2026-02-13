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

1. **Extract task list**: Parse rfc.md §11 acceptance chapter → extract each SCN-### as a test task
   - Format: `- [ ] SCN-### : {summary}` (one line per scenario)
   - Write to `.ohrfc/<rfc_id>/tasks.md`

2. **Extract must-pass set**: Filter SCN list for must-pass items → write to `.ohrfc/<rfc_id>/verification_checklist.md`
   - Format: markdown checklist with SCN-### ID, category, and one-line description

3. **Output format**: Markdown by default. Future option: configurable export targets (Jira/Linear/GitHub Issues) via export adapter.

## Hard Rule

After baseline accepted, modifying rfc.md requires baseline change flow:
CHG-### + DEC-### → Gate-A → Gate-B → human re-approval.
