# Phase: INIT

> Execute at workflow start. Creates workspace and rfc.md skeleton.

## Preferred: Script Execution

```bash
python3 scripts/ohrfc_init.py <rfc_id> <rfc_title> [--strictness standard]
```

The script performs steps 2-5 below automatically. Only step 1 (strictness confirmation) requires prior user interaction if not specified via `--strictness`.

## Workspace Routing

When `/ohrfc` is triggered, the orchestrator first checks for existing workspaces before entering the new-RFC flow.

### Detection

```bash
python3 scripts/ohrfc_init.py scan
```

Returns JSON array of workspace status objects. If the array is empty, proceed directly to new-RFC flow (no AskUserQuestion needed).

### Routing Logic

```
/ohrfc triggered
    ↓
Run ohrfc_init.py scan → workspace list
    ↓
├─ Empty list → New-RFC flow (unchanged, skip AskUserQuestion)
│
└─ Non-empty list → Build dynamic options:
     ├─ "新建 RFC" (always present)
     ├─ "变更已有 RFC: <id>" (for each workspace with baseline_accepted=true)
     └─ "继续未完成 RFC: <id>" (for each workspace with baseline_accepted=false AND current_phase≠init)
     ↓
   If only "新建 RFC" qualifies → skip AskUserQuestion, proceed to new-RFC flow
   Otherwise → AskUserQuestion (single-select)
```

### Route: New RFC

Standard INIT flow (unchanged). User provides `rfc_id` and `rfc_title`, script creates workspace.

### Route: Post-Baseline Change

**Precondition**: Selected workspace has `baseline_accepted=true`.

1. Read `.ohrfc/<id>/state.json` → confirm `baseline_accepted=true`
2. Read `.ohrfc/<id>/rfc.md` → load existing baseline
3. AskUserQuestion: "变更内容是什么？" + single-select scope estimate:
   - "局部修改（1-2 个 section）"
   - "跨模块变更（≥3 个 section）"
   - "架构方向调整（推翻核心假设）"
4. Route based on scope:
   - "架构方向调整" → suggest new RFC (user confirms; original RFC unchanged)
   - "局部修改" / "跨模块变更" → enter Post-Baseline Change protocol (see `references/phase_review.md` §Post-Baseline Change Flow)
5. Update state.json: `current_phase: "baseline_change"`

### Route: Resume Unfinished RFC

**Precondition**: Selected workspace has `baseline_accepted=false` AND `current_phase≠init`.

1. Read `state.json` → `current_phase`
2. Read `checkpoint.md` → last interruption point
3. Execute Bootstrap Protocol (per `references/checkpoint_protocol.md` §4):
   `state.json → checkpoint.md → rfc.md + evidence.json → Re-orient → resume from current_phase`

## Context Loading

```
Read: references/rfc_template.md (full — structural skeleton for rfc.md)
Read: assets/schemas/state.schema.json (state tracking fields)
```

## Execution Sequence

1. **Confirm strictness**: If user didn't specify → AskUserQuestion (default Standard). If specified → use directly.

2. **Create workspace**:
   ```
   Bash: mkdir -p .ohrfc/<rfc_id>/.debug .ohrfc/<rfc_id>/.reviews
   ```

3. **Generate rfc.md skeleton**:
   - Write: `.ohrfc/<rfc_id>/rfc.md`
   - Content: template headings only (from rfc_template.md) + meta block
   - Must include: `template_id: rfc_template_os_service`, `template_version: 2026-02-09`, `strictness: <Light|Standard|Full>`
   - Do NOT fill business content — only structural headings and empty fill-in markers

4. **Generate evidence.json**:
   ```json
   { "schema_version": "v1", "items": [] }
   ```

5. **Generate state.json** (per state.schema.json):
   - `rfc_id`, `current_phase: "discover"`, `strictness`, `template_id`, `template_version`
   - `gate_a_result: null`, `gate_b_round: 0`, `gate_b_max_rounds` (Light=0, Standard=2, Full=3)
   - `gate_b_result: null`, `reviewer_count: 3`, `baseline_accepted: false`

## Exit Conditions

- [ ] `.ohrfc/<rfc_id>/rfc.md` exists with meta triple
- [ ] `evidence.json` exists with schema_version = "v1"
- [ ] `state.json` exists with current_phase = "discover"

## Failure Handling

- Directory creation error → inform user, check permissions
- Template read error → confirm skill references/ directory intact
