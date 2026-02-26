# Phase: FINALIZE

> Export derivatives, archive process artifacts, lock baseline.
> **Input**: baseline_accepted = true + rfc.md + evidence.json
> **Output**: Archived workspace with optional derivative exports

## Prerequisites

No reference files required by the orchestrator. Export sub-agent loads `references/methodology.md §4` (ID system) if needed for ID validation.

## Context Loading

No additional references required.

## Execution

1. **AskUserQuestion: Export derivatives?**
   Ask user whether to export derivative artifacts:
   - Options: "导出任务清单和验收清单 (tasks.md + verification_checklist.md)" / "导出人可读摘要 (readable_digest.md)" / "全部导出" / "仅归档，不导出"
   - Default behavior: **archive-only** (no export unless user explicitly opts in)

2. **If export requested**: Dispatch sub-agent for derivative export (see Task Export / Readable Digest below)

3. **Archive process artifacts**:
   - Ensure `.debug/events.jsonl` preserved (truncation/timeout audit trail)
   - Ensure `.reviews/summary.json` preserved (Gate-B final result)
   - Ensure `evidence.json` preserved (evidence chain)

4. **Lock normative content**:
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

## Readable Digest Export (optional)

When readable digest export is requested:

Run `scripts/export_readable.py` to generate a stakeholder-friendly summary:

```bash
python3 <skill_dir>/scripts/export_readable.py <user_project_dir>/.ohrfc/<rfc_id>/rfc.md -o <user_project_dir>/.ohrfc/<rfc_id>/readable_digest.md
```

**What it produces**:
- Keeps: §1 背景, §2 痛点, §3 目标, §4 一页结论, §5 决策, §6 方案概览 (with diagrams), §7 影响分析
- Strips: §12-§15 (gate declarations, self-check, release meta, change log)
- Cleans: removes dense inline EVD/REQ references for readability

**Options**:
- `--include-normative`: also include §8 安全, §9 可靠性, §10 可观测性, §11 验收 (summary only)
- `--no-diagrams`: strip Mermaid blocks (for text-only review)

Output: `.ohrfc/<rfc_id>/readable_digest.md`

## Hard Rule

After baseline accepted, modifying rfc.md requires baseline change flow:
CHG-### + DEC-### → Gate-A → Gate-B → human re-approval.
