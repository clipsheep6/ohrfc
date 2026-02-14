# Phase: GATE-B (Semantic Review)

> Semantic review evaluating boundary/limit/failure strategy/acceptance quality.
> **Input**: rfc.md + evidence.json + role-specific review perspectives
> **Output**: PASS/FAIL + summary.json with P0/P1/P2 issues + required_actions

## Prerequisites (sub-agent reviewers)

Each reviewer sub-agent loads its own context:
- `references/methodology.md §3,7-9` — strictness, Unresolved grading, SCN coverage, convergence
- `references/review_assets.md` — reviewer output format + severity definitions
- `references/reviewer_prompts/<role>.md` — role-specific review perspective

The orchestrator does NOT load these files. It reads only `.reviews/summary.json` after the Reduce phase, then applies the 6-condition PASS predicate (fixed rules, no reference file needed).

## Entry Check (must pass before proceeding)

1. Gate-A = PASS (else Gate-B = FAIL, blocked)
2. Hard-Unresolved in rfc.md = 0 (else Gate-B = FAIL, blocked)

## Execution by Strictness

### Light

No Gate-B review. Skip directly to REVIEW phase.
Update state.json: `gate_b_result: "skip"`, `current_phase: "review"`.

### Standard (no upgrade triggers)

**1-route comprehensive self-review** using merged checklist:
1. Single review pass covering all perspectives (architecture + security + QA) using merged checklist from `references/reviewer_prompts/`
2. Output: `.reviews/gateb/round-{N}/self_review.md`
3. Apply PASS predicate (see below)

### Standard (with upgrade triggers)

**3-route parallel review** (Architect + Security + QA), all using current model:
1. Launch 3 `Task(general-purpose)` sub-agents in parallel
2. Each receives: rfc.md + evidence.json + role-specific prompt from `references/reviewer_prompts/<role>.md`
3. Output: `.reviews/gateb/round-{N}/<role>.md`
4. Reduce: merge into summary.json, apply PASS predicate

### Full

**3-route parallel + meta-reviewer**, using reviewer_dispatch config for multi-model (MCP):
1. Launch 3 role reviewers using `reviewer_dispatch` config from state.json (may route to different models via MCP)
2. Each receives: rfc.md + evidence.json + role-specific prompt
3. Output: `.reviews/gateb/round-{N}/<role>.md`
4. **Meta-reviewer**: additional cross-cutting review that checks for inter-role contradictions, coverage gaps between roles, and systemic issues no single role would catch
5. Output: `.reviews/gateb/round-{N}/meta.md`
6. Reduce: merge all reports (including meta) into summary.json, apply PASS predicate

**Fallback**: If MCP models unavailable in Full mode, fall back to current model for all routes (same as Standard with upgrade triggers, plus meta-reviewer).

**Note**: Gate-B includes thinking lenses via reviewer prompts. See `references/reviewer_prompts/` for role-specific analytical perspectives.

## Reduce Phase: Merge & Evaluate

**Steps 1-2** [reduce sub-agent]: Dispatch `Task(general-purpose)` sub-agent to merge reviewer reports.

1. Read all role reports from `.reviews/gateb/round-{N}/`
2. Use `mcp__sequential-thinking__sequentialthinking` (or internal reasoning) to resolve cross-report conflicts: contradictory severity ratings, overlapping findings with different recommendations, and coverage gap identification across roles.
3. Merge into `.reviews/summary.json` (per `schemas/review_summary.schema.json`):
   - Aggregate P0/P1/P2 issues
   - Generate `required_actions` (each: Location + specific Edit — no vague "improve/enhance")
   - Record `role_votes: {role: pass|fail}`

**Step 3** [orchestrator]: Read summary.json only. Apply **PASS predicate** (all must hold):
   1. P0 == 0
   2. Hard-Unresolved == 0
   3. All P1 closed: fixed, or DEC risk-acceptance with mitigation/tracking
   4. Hard assertion evidence thresholds met (per methodology.md §6)
   5. Strictness requirements met (per methodology.md §3)
   6. Consistency: key terms/category codes match methodology; inconsistencies count as P1

## Result Routing

### PASS
Write summary.json. Update state.json: `gate_b_result: "pass"`, `current_phase: "review"`.

### FAIL — Early Circuit Breaker

- **Round 1 FAIL** → Automatic fix. Write checkpoint (see below). Update state.json: `gate_b_result: "fail"`, `gate_b_round += 1`, `current_phase: "design"`. If evidence gap: allow one DISCOVER detour per round. Loop to DESIGN.

- **Round 2 FAIL** → Present AskUserQuestion with 3 options:
  - (a) Auto-fix Round 3 (if max rounds allow — Full only)
  - (b) Scope cut — remove features causing failure
  - (c) Risk acceptance — DEC with residual risk + mitigation + tracking
  Write choice as DEC-###.

  **State transitions per choice**:
  - (a) Auto-fix → `gate_b_round += 1`, `current_phase: "design"`. After DESIGN fix → `current_phase: "gate_a"` → normal gate flow.
  - (b) Scope cut → `current_phase: "design"`. Re-enter DESIGN to remove scoped features, then re-run Gate-A → Gate-B.
  - (c) Risk acceptance → Write DEC-### with risk acceptance fields. Re-evaluate PASS predicate with the DEC in place: if all 6 conditions now satisfied → `gate_b_result: "pass"`, `current_phase: "review"`; if still failing → `current_phase: "design"` (further fixes needed).

- **Max rounds reached** → Force convergence (per methodology.md §9). AskUserQuestion with 3 choices:
  1. Scope cut — remove features causing failure
  2. Risk acceptance — DEC with residual risk + mitigation + tracking
  3. Escalate review + retry
  Write choice as DEC-###.

### FAIL Checkpoint & Restart

On any FAIL: Read `references/checkpoint_protocol.md` §3 Gate-B FAIL Extraction prompt. Append Gate-B Round N Exit section to checkpoint.md. Update state.json: `checkpoint_version += 1`, `last_checkpoint_phase: "gate_b"`. **Then restart context** — next DESIGN entry uses Bootstrap Protocol (checkpoint_protocol.md §4).

## P1 Risk Acceptance Constraints

**P0**: Never acceptable — must fix or scope cut.

**P1 involving hard assertion evidence gaps**:
- If the assertion remains as HR / hard constraint: must provide verifiable source (per methodology.md §6 — else PASS condition 4 fails).
- If source cannot be provided: must downgrade from HR to "assumption / risk acceptance" — remove from hard rules and rewrite as verifiable constraint; record residual risk in DEC-###.
- Preference: scope cut or escalate over risk acceptance for evidence gaps.

**P1 risk acceptance DEC-### minimum fields**:
- Residual risk (P0/P1 severity)
- Mitigation measures
- Observability / audit point
- Owner
- Trigger condition or deadline
- Linked SCN-### affected by the acceptance

**Convergence type constraints** (prevent abuse of risk acceptance):
- Hard assertion evidence gaps → prefer scope cut (choice 1) or escalate (choice 3)
- Unclear requirements → prefer scope cut (choice 1) or escalate (choice 3)
- Value trade-off disputes → all 3 choices allowed
