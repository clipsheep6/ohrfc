# Phase: INIT

> Execute at workflow start. Creates workspace and rfc.md skeleton.

## Preferred: Script Execution

```bash
python3 scripts/ohrfc_init.py <rfc_id> <rfc_title> [--strictness standard]
```

The script performs steps 2-5 below automatically. Only step 1 (strictness confirmation) requires prior user interaction if not specified via `--strictness`.

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
