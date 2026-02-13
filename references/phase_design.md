# Phase: DESIGN

> Fill rfc.md with full design content: review layer → normative layer → gates/appendix.

## Prerequisites (sub-agent context)

The DESIGN sub-agent must load:
- `references/rfc_template.md` — section structure and fill-in skeleton
- `references/design_assets.md` — SCN/DEC/Sources writing templates
- `references/methodology.md §3-8` — strictness, expression rules, evidence thresholds, ID system, Unresolved grading, SCN coverage
- On demand: `references/security_template.md` — high-risk / cross-trust-boundary scenarios

The orchestrator dispatches the sub-agent and validates the returned draft against self-check criteria.

**If entering from Gate-B FAIL (context restart)**:
Orchestrator executes Bootstrap Protocol from `references/checkpoint_protocol.md` §4. Provides checkpoint.md content in sub-agent prompt as reasoning context from previous phases.

## Execution Model

DESIGN execution uses a single sub-agent to write the complete rfc.md draft. The orchestrator dispatches with all context (requirements + evidence + constraints from DISCOVER), and the sub-agent returns the completed draft. The orchestrator then validates the draft against self-check criteria before proceeding.

## Step 1: Fill Review Layer (rfc.md §1-§6)

- §1 背景: Current state + why now (facts, no code)
- §2 用户痛点: User-perceivable problems only (no internal terms)
- §3 目标与非目标: Verifiable goals (4 quality categories) + success criteria table + glossary
- §4 一页结论: 3-6 decidable conclusions + impact table + must-pass SCN set + quality closure summary + reading guide
- §5 方案概览: End-to-end main path + contracts + design diagrams (A: architecture/boundary, B: interaction sequence, C: failure/convergence) + Notes per diagram
- §6 影响分析与兼容性: Unchanged/changed/default strategy + breaking changes + rollback + evidence spot-checks

## Step 2: Fill Normative Layer (rfc.md §7-§11)

- §7 关键决策: DEC-### with alternatives + rationale + trade-offs; Unresolved table (Hard/Soft)
- §8 安全模型: SEC-HR rules → why → SCN → evidence (if high-risk: load security_template.md for STRIDE deep-dive)
- §9 可靠性: REL-HR rules → why → SCN → invariants/forbidden states
- §10 可观测性: Minimum observability requirements + SCN binding
- §11 验收: 5-category SCN (per methodology.md §8) + must-pass set + risk coverage matrix

## Step 3: Fill Gates/Release/Appendix (rfc.md §12-§16)

- §12 变更记录 (if post-baseline)
- §14 门禁声明: Trigger declarations YES/NO + Links (Gate-A checks this mechanically)
- §15 发布元信息
- §16 角色 + 11-item self-check + document meta (template_id/template_version/strictness)

## Parallel Gap-Filling (optional)

**Trigger**: Standard (with upgrade triggers) or Full strictness AND any upgrade trigger hit (trust boundary change, resource limit change, recovery path change, compatibility behavior change).

**Execution**:
1. Launch 2-3 Task(general-purpose) sub-agents with roles: Architect / Security / QA
2. Each sub-agent reads rfc.md + evidence.json
3. Output: `.reviews/design/round-01/<role>.md` (using review_assets.md §2 format)
4. Dispatch merge sub-agent: reads all role outputs + current rfc.md → returns merged draft with selectively adopted findings (P0/P1 adopted, P2 at discretion)
5. Orchestrator writes merged draft to rfc.md (single-writer)

Sub-agent prompt template:
```
You are a {role} reviewer. Read rfc.md and evidence.json. Identify gaps from your perspective.
Output findings as P0/P1/P2 with Location+Issue+Risk+Action.
Include proposed HR/SCN/DEC edits (copy-paste ready).
Flag hard assertions needing evidence.
Write ONLY to your isolated output file. Do NOT modify rfc.md.
```

## DESIGN Self-Check (must pass before GATE)

### Thinking Lens

Apply these lenses during self-check:
- **Systems Thinking**: "What feedback loops exist? What emergent behaviors could appear?"
- **Adversarial Thinking**: "What would an attacker exploit first?"

### Check Items

Run template §16.2 self-check (11 items), then these 6 additional checks:

- [ ] **Structure**: All sections present, meta triple filled
- [ ] **Expression**: All SCN use WHEN/AND/THEN on separate lines; no wall-of-text (per methodology.md §5)
- [ ] **Coverage**: Minimum SCN categories present (per methodology.md §8)
- [ ] **Strictness**: Full has coverage matrix + option set; Standard missing items have DEC justification
- [ ] **Auditable**: Hard-Unresolved locatable with convergence action; hard assertions have evidence or Unresolved/DEC (per methodology.md §6)
- [ ] **Consistency**: Design diagrams match text bullet points (no conflicts)

All passed → Update state.json: `current_phase → "gate_a"`
Any failed → Fix and re-check (do NOT enter GATE)

## Checkpoint Write (after self-check passed)

Read `references/checkpoint_protocol.md` §3 DESIGN Exit Extraction prompt.
Append the DESIGN Exit section to `.ohrfc/<rfc_id>/checkpoint.md`.
Update state.json: `checkpoint_version += 1`, `last_checkpoint_phase: "design"`.
