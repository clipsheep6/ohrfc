# Phase: GATE-A (Mechanical Check)

> Deterministic structural/auditability check. Does NOT evaluate design quality.
> **Input**: rfc.md + evidence.json
> **Output**: PASS/FAIL + actionable failure list (section/ID located)
> **Checks**: 20 total (17 HARD + 3 SOFT)

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
- **Any FAIL** → Output failure list with section/ID location + fix suggestion. Update state.json: `gate_a_result: "fail"`, `current_phase: "design"`. **Dispatch DESIGN sub-agent** (see below) to fix only failing items — orchestrator NEVER fixes Gate-A failures in the main window.

**Hard rule**: Gate-B MUST NOT start unless Gate-A = PASS.

## Gate-A FAIL Fix Delegation

When Gate-A reports FAIL, the orchestrator dispatches a `Task(general-purpose)` sub-agent to fix the failing items. The orchestrator provides:
1. The Gate-A failure output (section/ID locations + fix suggestions)
2. Current rfc.md content
3. evidence.json content (if evidence-related failures)

The sub-agent must:
- Load `references/phase_design.md` + `references/methodology.md §4-6` for context
- Fix ONLY the failing items (do not rewrite unrelated sections)
- Run `gate_a_check.py --dry-run` to verify fixes pass before returning
- **Return the complete fixed rfc.md content** — NOT analysis, NOT recommendations, but the actual corrected document ready for the orchestrator to write

Sub-agent prompt template:
```
You are a DESIGN fix agent. Gate-A mechanical check has FAILED on the following items:
{gate_a_failure_output}

Fix ONLY these failing items in rfc.md. Do NOT rewrite unrelated sections.
After fixing, run: python3 scripts/gate_a_check.py {rfc_path} --evidence {evidence_path} --dry-run
If dry-run still fails, fix again until WOULD_PASS.

CRITICAL: Return the COMPLETE fixed rfc.md content. Do NOT return analysis or recommendations.
The orchestrator will write your output directly to rfc.md.

Your output will be strictly cross-reviewed by Codex and other models. Ensure precision.
```

The orchestrator writes the returned rfc.md, then re-runs formal Gate-A (`gate_a_check.py` without `--dry-run`).
