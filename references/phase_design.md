# Phase: DESIGN

> Fill rfc.md with full design content: review layer → normative layer → gates/appendix.

## Prerequisites (sub-agent context)

**Sub-agent type**: `Task(Plan)` preferred (architectural reasoning optimized; has Read/Glob/Grep/Bash/MCP but no Write/Edit — orchestrator remains single-writer). Fallback: `Task(general-purpose)` if Plan unavailable.

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

**Interrupt-resume for fork escalation**: When the sub-agent encounters an emergent fork (see Socratic Pause → Emergent Fork Escalation), execution is interrupted:
1. Sub-agent returns partial draft + fork escalation signal (instead of complete draft)
2. Orchestrator presents fork to user via AskUserQuestion
3. Orchestrator dispatches new sub-agent with: partial draft + user's fork decision as additional constraint + original context
4. New sub-agent completes the remaining sections, incorporating the fork resolution
5. If a second fork occurs, the same interrupt-resume cycle applies (max 2 per DESIGN phase)

**Relation to gap-filling**: Fork escalation happens *during* DESIGN (direction decisions). Gap-filling reviewers run *after* DESIGN (completeness/quality checks). The two mechanisms are complementary and do not conflict.

## Step 1: Fill Review Layer (rfc.md §1-§6)

### Socratic Pause Protocol

Use `mcp__sequential-thinking__sequentialthinking` (or internal reasoning) for each section's Socratic Pause — structured multi-step thinking helps surface non-obvious architectural trade-offs and cross-section dependencies.

At each section, the sub-agent MUST pause and answer internally:
1. **Core (always)**: C1 "Are we solving symptoms or the ROOT problem?" + C2 "Looking back one year, would this still be the best choice?"
2. **Section-fixed**: The specific Pause question listed below for this section
3. **Context-dynamic** (0-2): Scan DISCOVER outputs (risks.top, unknowns.hard, evidence gaps) for unresolved items relevant to this section. If found, construct a targeted question using these rules:

| Context Signal | Dynamic Question Template | Trigger |
|----------------|--------------------------|---------|
| DISCOVER `risks.top` | "Risk R-{N} says {risk}. Has the current design addressed it?" | Each DESIGN section: check unclosed risks |
| `unknowns.hard` list | "Hard unknown U-{N} is still unresolved. Does it affect this section?" | When hard unknown relates to current section |
| `evidence.json` with `truncated=true` | "Evidence E-{N} was truncated. Does this HR depend on that evidence?" | When writing HR that cites truncated evidence |
| strictness=Full | "Under Full strictness, does this DEC need an option set (≥2 alternatives)?" | When writing DEC |
| Security / trust boundary change in DISCOVER | "Trust boundary change → do we need SEC-HR + reject/abuse SCN?" | Before writing §8, check DISCOVER findings |
| Compatibility risk in DISCOVER | "Is the default value strategy explicit? Is old behavior explicitly preserved?" | Before writing §6, check DISCOVER findings |

#### Emergent Fork Escalation

When Socratic Pause reveals a fork (§5 or §7: "Why this over the 2nd best?" has no clear answer):

**Confidence assessment**:
- **High confidence (>80%)**: Select recommended approach. Record in DEC-### with alternatives + rationale.
- **Low confidence (≤80%)**: Trigger escalation signal → return to orchestrator for user decision.

**Escalation signal format** (returned to orchestrator):
```text
FORK_ESCALATION:
  section: §5 / §7
  description: <what the fork is about>
  option_a: { summary, trade_offs, affected_ids[] }
  option_b: { summary, trade_offs, affected_ids[] }
  recommendation: A / B / none
  confidence: 0-100
```

**Orchestrator handling**:
1. Pause/restart DESIGN sub-agent
2. Present fork to user via AskUserQuestion (options with trade-offs + recommendation if any)
3. User's choice becomes a new constraint → sub-agent continues design with choice as input

**Conservative trigger constraints** (prevent over-escalation):
- Max 2 escalations per DESIGN phase
- Only **architectural-level** forks qualify (affects ≥3 IDs OR spans ≥2 rfc.md sections)
- Implementation-level choices (library selection within same architecture) → sub-agent decides autonomously via DEC-###

Only proceed to write after all Pause questions are answered satisfactorily (including any fork escalation resolution).

- §1 背景:
  - **Pause**: "What's the ONE fact that, if wrong, invalidates everything below?"
  - Write: Current state + why now (facts, no code)

- §2 用户痛点:
  - **Pause**: "Is this the user's REAL pain, or what we ASSUME they feel?"
  - Write: User-perceivable problems only (no internal terms)

- §3 目标与非目标:
  - **Pause**: "What goal, if NOT achieved, makes the whole project pointless?"
  - Write: Verifiable goals (4 quality categories) + success criteria table + glossary

- §4 一页结论 (write LAST — synthesize from §1-§3, §5-§6):
  - **Pause**: "Are these conclusions decidable? Can someone say YES/NO to each?"
  - Write: 3-6 decidable conclusions + impact table + must-pass SCN set + quality closure summary + reading guide

- §5 方案概览:
  - **Pause**: "Is this the simplest design that satisfies ALL constraints?"
  - Write: End-to-end main path + contracts + design diagrams (A: architecture/boundary, B: interaction sequence, C: failure/convergence) + Notes per diagram

- §6 影响分析与兼容性:
  - **Pause**: "What downstream change triggers a cascade we haven't mapped?"
  - Write: Unchanged/changed/default strategy + breaking changes + rollback + evidence spot-checks

## Step 2: Fill Normative Layer (rfc.md §7-§11)

Same Socratic Pause Protocol applies (Core C1+C2 + Section-fixed + Context-dynamic).

- §7 关键决策:
  - **Pause per DEC**: "Why this over the 2nd best? What's the strongest counterargument?"
  - Write: DEC-### with alternatives + rationale + trade-offs; Unresolved table (Hard/Soft)

- §8 安全模型:
  - **Pause**: "What's the cheapest attack with highest impact we haven't covered?"
  - Write: SEC-HR rules → why → SCN → evidence (if high-risk: load security_template.md for STRIDE deep-dive)

- §9 可靠性:
  - **Pause**: "Assume 3AM failure, no one on-call. What happened? Trace back."
  - Write: REL-HR rules → why → SCN → invariants/forbidden states

- §10 可观测性:
  - **Pause**: "How would we NOT know the system is broken?"
  - Write: Minimum observability requirements + SCN binding

- §11 验收:
  - **Pause**: "What single test failure would prove our entire design is wrong?"
  - Write: 5-category SCN (per methodology.md §8) + must-pass set + risk coverage matrix

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
- **Pre-mortem**: "Assume this RFC causes a production incident. Which section was the weak link?"
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

## Pre-Gate Dry-Run (recommended)

After self-check passes, run Gate-A in advisory mode to catch mechanical issues before formal gate entry:

```bash
python3 scripts/gate_a_check.py .ohrfc/<rfc_id>/rfc.md --evidence .ohrfc/<rfc_id>/evidence.json --dry-run
```

- If WOULD_PASS: proceed to Checkpoint Write → state transition
- If WOULD_FAIL: fix failing items (same as self-check fix loop), re-run dry-run
- Dry-run failures do NOT trigger state transition to gate_a; they are advisory only

This step reduces DESIGN→GATE-A round-trips by catching structural/mechanical issues before the formal gate.

## Checkpoint Write (after self-check passed)

Read `references/checkpoint_protocol.md` §3 DESIGN Exit Extraction prompt.
Append the DESIGN Exit section to `.ohrfc/<rfc_id>/checkpoint.md`.
Update state.json: `checkpoint_version += 1`, `last_checkpoint_phase: "design"`.
