# Phase: GATE-A (Mechanical Check)

> Deterministic structural/auditability check. Does NOT evaluate design quality.
> **Input**: rfc.md + evidence.json
> **Output**: PASS/FAIL + actionable failure list (section/ID located)

## Prerequisites

None. All check logic is built into `scripts/gate_a_check.py`. No reference files need to be loaded by the orchestrator.

**Fallback** (script unavailable): Load `references/methodology.md §4-6` for manual check execution.

## Execution: Run Check Sequence

**Preferred**: Run `scripts/gate_a_check.py` against rfc.md + evidence.json for automated checks.

```bash
python3 scripts/gate_a_check.py .ohrfc/<rfc_id>/rfc.md --evidence .ohrfc/<rfc_id>/evidence.json
```

Exit code 0 = PASS, 1 = FAIL. Stdout contains per-check results.

**Fallback** (if script unavailable): Execute checks manually per the check definitions in the script. All check semantics (IDs, thresholds, format rules) are defined in methodology.md §4-6.

## Result Routing

- **All PASS** → Update state.json: `gate_a_result: "pass"`, `current_phase: "gate_b"`
- **Any FAIL** → Output failure list with section/ID location + fix suggestion. Update state.json: `gate_a_result: "fail"`, `current_phase: "design"`. Return to DESIGN to fix only failing items.

**Hard rule**: Gate-B MUST NOT start unless Gate-A = PASS.
