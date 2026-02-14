---
name: ohrfc
description: >
  Industrial-grade RFC workflow: requirements → testable rfc.md via evidence-based
  clarification, boundary-first design, and dual quality gates (Gate-A mechanical +
  Gate-B semantic multi-role review). Covers constraints, invariants, trade-offs,
  and falsifiable acceptance criteria. Triggers: "ohrfc", "/ohrfc", "create RFC",
  "design spec", "requirements analysis", "system design review".
---

<!-- skill-meta
version: 2.9.0
date: 2026-02-14
source_rev: git
-->

# OHRFC: Industrial-Grade Design Spec Workflow

## 0. Flow Overview

### Standard / Full path (7 phases)
```
INIT → DISCOVER&CLARIFY → DESIGN → GATE-A → [FAIL→DESIGN]
                                           → GATE-B → [FAIL→DESIGN/DISCOVER]
                                                    → REVIEW → [REJECT→DESIGN]
                                                             → FINALIZE
```

### Light path (user-triggered, simplified)
```
INIT → DISCOVER(simplified) → DESIGN(direct write) → GATE-A → REVIEW → FINALIZE
```
Light skips Gate-B, multi-role review, and convergence loops entirely.
User must explicitly request Light mode. Output is still standard `rfc.md` format.

Gate loop bounds (by strictness):
- Gate-A → DESIGN: unlimited (mechanical fix, typically 1-2 rounds)
- Gate-B → DESIGN: Standard=2 / Full=3 max rounds (Light: no Gate-B)
- Gate-B early breaker: Round 2 FAIL → present user with 3 choices (auto-fix / scope cut / risk accept)
- Gate-B max rounds exceeded: force convergence (scope cut / risk acceptance / escalate)

Workspace: `.ohrfc/<rfc_id>/` containing `rfc.md`, `evidence.json`, `state.json`, `checkpoint.md`.

## 1. Execution Principles

1. **Thin Orchestrator**: The main window (orchestrator) NEVER reads phase-specific reference files directly and NEVER executes codebase exploration tools (Glob/Grep/Read). It only dispatches sub-agents, handles user interaction (AskUserQuestion), writes artifacts (rfc.md/evidence.json/state.json), and manages state transitions. All phase reference reads and heavy tool execution happen inside sub-agents whose context is isolated from the main window. **Exception**: `references/methodology.md` is loaded once by the orchestrator at workflow start — it provides the foundational design philosophy and rules needed for orchestration decisions (convergence, checkpoint extraction, artifact formatting).
2. **Single-writer**: only the main orchestrator writes `rfc.md`, `evidence.json`, `state.json`. Sub-agents write isolated outputs only (`.reviews/`, return values).
3. **rfc.md is the sole normative truth**: any conclusion from gates/reviews/evidence must be written back to rfc.md as DEC/REQ/SCN/CHG.
4. **No implementation code in rfc.md**: only contract-level structured expressions (fenced blocks with `text` or `contract` language tag, ≤30 lines).
5. **Language**: user interaction follows user's language (default Chinese). Internal reasoning, sub-agent prompts, and code comments in English.
6. **Checkpoint at phase boundaries**: Write structured reasoning checkpoint at DISCOVER exit, DESIGN exit, and Gate-B FAIL exit. See `references/checkpoint_protocol.md` for format, extraction prompts, and bootstrap protocol.

### 1.1 Context Budget

The main window context must survive the **entire workflow** (7 phases + failure loops) without hitting the 4% compression threshold. Sub-agents get independent context windows.

| Phase | Orchestrator budget | Sub-agent budget | What orchestrator does |
|-------|-------------------:|----------------:|----------------------|
| START | ~4K | — | Read `references/methodology.md` (once, entire workflow) |
| INIT | ~2K | — (script) | Run `ohrfc_init.py`, AskUserQuestion(strictness) |
| DISCOVER | ~8K | ~40-60K | Dispatch sub-agent, receive summary, CLARIFY(AskUserQuestion), write artifacts |
| DESIGN | ~5K | ~80-120K | Dispatch sub-agent, receive confirmation |
| GATE-A | ~3K | — (script) | Run `gate_a_check.py`, parse result, state transition |
| GATE-B | ~8K | ~30-50K ×N | Dispatch reviewers, read summary.json, PASS predicate, AskUserQuestion(on FAIL) |
| REVIEW | ~8K | ~60-80K (Mode B) | Mode A: present summary + AskUserQuestion; Mode B: dispatch sub-agent |
| FINALIZE | ~3K | ~10K | Dispatch export sub-agent |
| **Total** | **~41K** | — | **< 21% of 200K window** |

**Budget with failure loops** (worst case: 3× Gate-B FAIL + 1× REVIEW Reject):
- Base: ~41K + 4 loops × ~10K = ~81K → **< 41%**. Compression never triggered.

### 1.2 Agent Team Execution Model

```
Orchestrator (main window):
  load methodology.md (once) → dispatch → receive summary → AskUserQuestion → write artifacts → state transition
  NEVER: Read phase references (phase_*.md, *_assets.md) | Glob/Grep/Read codebase | sequential-thinking

Sub-agents (isolated context):
  Read reference files → execute tools → reason → return structured result
  NEVER: AskUserQuestion | write rfc.md/evidence.json/state.json
```

Per-phase delegation:
- **INIT**: Script (`ohrfc_init.py`). No sub-agent needed.
- **DISCOVER**: Staged `Task(Explore)` sub-agents: (1) single Explore for QUICK_SCAN + REASONING_PASS (serial), (2) orchestrator handles CLARIFY, (3) 1-3 parallel Explore agents for EVIDENCE_TARGETED (split by target file/module). Fallback: `Task(general-purpose)` if Explore unavailable.
- **DESIGN**: Single `Task(Plan)` sub-agent for architectural reasoning → returns complete rfc.md draft (orchestrator writes). Fallback: `Task(general-purpose)` if Plan unavailable. Optional: parallel gap-filling `Task(general-purpose)` reviewers + 1 merge sub-agent.
- **GATE-A**: Script (`gate_a_check.py`). No sub-agent needed.
- **GATE-B**: N parallel `Task(general-purpose)` reviewer sub-agents (Map) + 1 reduce sub-agent (Reduce → summary.json). Orchestrator reads summary.json only, applies PASS predicate.
- **REVIEW Mode B/C**: Single isolated `Task(general-purpose)` sub-agent for section/risk analysis. Orchestrator relays AskUserQuestion results.
- **FINALIZE**: Single `Task(general-purpose)` sub-agent for export.

## 2. Default Configuration

| Config | Default | Override |
|--------|---------|----------|
| Strictness | Standard | User specifies Light/Standard/Full at INIT |
| Template | `rfc_template_os_service` | DEC records template choice |
| Gate-B route | Light: skip; Standard: 1-route self-review | Standard auto→3-route on upgrade triggers; Full: 3+meta (4-route) multi-model |
| Gate-B max rounds | Per strictness (Light=N/A, Standard=2, Full=3) | DEC override with justification |
| Sub-agent models | Inherit from orchestrator | User override per sub-agent type at INIT |

For strictness details and Standard→3-route upgrade triggers, see `references/methodology.md` §3.

---

## Phase 1: INIT

**Execution**: Run `scripts/ohrfc_init.py` (no sub-agent needed). Fallback: `references/phase_init.md`.

**Workspace Routing**: Before creating a new RFC, detect existing workspaces:
```bash
python3 scripts/ohrfc_init.py scan
```
- **No workspaces** → proceed directly to new-RFC flow (no AskUserQuestion)
- **Workspaces found** → AskUserQuestion (single-select):
  - "新建 RFC" (always present)
  - "变更已有 RFC: \<id\>" (only if `baseline_accepted=true`) → Post-Baseline Change entry
  - "继续未完成 RFC: \<id\>" (only if `baseline_accepted=false` AND `current_phase≠init`) → Resume via Bootstrap Protocol
- **Only "新建 RFC" qualifies** → skip AskUserQuestion, proceed to new-RFC flow

**New-RFC flow** (unchanged):
```bash
python3 scripts/ohrfc_init.py create <rfc_id> <rfc_title> [--strictness standard]
```

**Summary**:
1. Confirm strictness (default Standard; Light/Full must be explicitly requested) via AskUserQuestion if not specified
2. Create workspace: `mkdir -p .ohrfc/<rfc_id>/{.debug,.reviews}`
3. Read `references/rfc_template.md` → Write rfc.md skeleton (headings + meta only)
4. Write evidence.json (`{ "schema_version": "v1", "items": [] }`)
5. Write state.json (per `assets/schemas/state.schema.json`): `current_phase: "discover"`

**Exit**: rfc.md with meta triple (template_id/template_version/strictness); evidence.json; state.json with current_phase=discover.

---

## Phase 2: DISCOVER & CLARIFY

**Ref** (sub-agent): `references/phase_discover.md` + `references/discover_assets.md` + `references/methodology.md` §6

**Execution**: Staged dispatch of Explore sub-agents:
1. **QUICK_SCAN + REASONING_PASS**: Single `Task(Explore)` sub-agent (serial — REASONING depends on SCAN results). Fallback: `Task(general-purpose)`.
2. **CLARIFY**: Orchestrator handles (user interaction via AskUserQuestion).
3. **EVIDENCE_TARGETED**: 1-3 parallel `Task(Explore)` sub-agents (split by hard assertion target files/modules; orchestrator merges EVD into evidence.json). Fallback: `Task(general-purpose)`.

Dependency chain: `QUICK_SCAN → REASONING_PASS → CLARIFY → EVIDENCE_TARGETED (1-3 parallel)`

**Summary** (4 sequential sub-steps; Light mode uses step 1 + step 3 only):
1. **QUICK_SCAN** [sub-agent]: Glob+Grep+Read bounded codebase scan → fill scan output
2. **REASONING_PASS** [sub-agent]: sequential-thinking on risks/unknowns → question candidates (skip in Light)
3. **CLARIFY** [orchestrator]: Tiered questioning — Round 1: Tier 1-2 questions (max 4, mandatory); Round 2: Tier 3 questions (max 4, conditional; Light: Round 1 only, max 3) → write to rfc.md as DEC/REQ/SCN/HR
4. **EVIDENCE_TARGETED** [sub-agent]: locate evidence for hard assertions → EVD-### in evidence.json (skip in Light)

**Exit**: ≥1 scope/non-goal REQ/DEC, ≥3 HR drafts, ≥3 falsifiable SCN drafts, unknowns graded Hard/Soft. State: current_phase=design. **Checkpoint written** (DISCOVER Exit section).

---

## Phase 3: DESIGN

**Ref** (sub-agent): `references/phase_design.md` + `references/rfc_template.md` + `references/design_assets.md` + `references/methodology.md` §3-8. On demand: `references/security_template.md`

**Execution**: Dispatch single `Task(Plan)` sub-agent for architectural reasoning → returns complete rfc.md draft. Orchestrator receives draft, validates self-check, writes rfc.md + state transition. Fallback: `Task(general-purpose)` if Plan unavailable.

**Summary** (3 steps + optional parallel gap-filling):
1. **Fill review layer** (§1-§6): background, pain points, goals, TL;DR, solution overview, impact/compatibility
2. **Fill normative layer** (§7-§11): decisions, security model, reliability, observability, acceptance (5-category SCN)
3. **Fill gates/appendix** (§12-§16): change log, trigger declarations, release meta, roles + self-check

**Socratic Pause protocol**: Core questions (C1: root problem? C2: still best in 1 year?) + section-fixed questions + context-dynamic questions are embedded at each section's generation point. Includes **emergent fork escalation**: when Socratic Pause reveals an architectural fork with ≤80% confidence, sub-agent returns escalation signal to orchestrator → AskUserQuestion presents fork + trade-offs → user decision resumes design. Max 2 escalations per DESIGN; implementation-level choices stay autonomous. See `references/phase_design.md` Step 1/2 for the full protocol.

**§5.4 API Contract Design**: When the RFC involves public API changes (ArkTS, C/C++ APIs), §5.4 must be filled covering: interface specification, developer model, error codes, versioning strategy, and existing API compatibility.

**§6.1.3 API Compatibility**: §6.1.3 covers API contract compatibility with breaking change rules for OS service APIs.

**Optional parallel gap-filling** (Standard with upgrade triggers / Full):
- Launch 2-3 Task(general-purpose) sub-agents: Architect / Security / QA
- Each reads rfc.md + evidence.json, outputs `.reviews/design/round-01/<role>.md`
- Dispatch merge sub-agent: reads all role outputs + current rfc.md → returns merged draft with selectively adopted findings
- Orchestrator writes merged draft to rfc.md (single-writer)
- Light mode: single sub-agent writes complete draft directly; no parallel gap-filling

**Self-check** (must pass before GATE): Run template §16.2 (11 items) + 6 additional checks (structure/expression/coverage/strictness/auditable/consistency).

**Pre-Gate Dry-Run**: Optional `gate_a_check.py --dry-run` before formal gate entry to reduce DESIGN→GATE-A round-trips.

**Exit**: Self-check passed. State: current_phase=gate_a. **Checkpoint written** (DESIGN Exit section).

---

## Phase 4: GATE-A (Mechanical Check)

**Execution**: Run `scripts/gate_a_check.py` directly (no sub-agent needed). Fallback: `references/phase_gate_a.md`.

**Summary**: Run 17 deterministic checks on rfc.md structure and auditability. 3-state output per check: PASS / WARN / FAIL.

**Preferred**: Execute `scripts/gate_a_check.py`:
```bash
python3 scripts/gate_a_check.py .ohrfc/<rfc_id>/rfc.md --evidence .ohrfc/<rfc_id>/evidence.json
```

| Check | Type | What |
|-------|------|------|
| 1-2 | HARD | Structure match + ID uniqueness |
| 3-4 | HARD | No placeholders + expression rules |
| 5-6 | HARD | Readability + SCN category coverage |
| 7-9 | HARD | Evidence cross-check + strictness + trigger declarations |
| 10 | HARD | HR-SCN binding integrity |
| 11 | HARD | DEC alternatives documented |
| 12 | HARD | Must-pass SCN validity |
| 13 | HARD | Coverage matrix completeness |
| 14 | HARD | Section non-empty |
| 15 | SOFT | Diagram-text pairing |
| 16 | SOFT | Unresolved format compliance |
| 17 | SOFT | Orphan SCN detection |

14 HARD checks block progression (any FAIL → back to DESIGN). 3 SOFT checks produce WARN only (do not block).

**Result**: All HARD PASS → state: gate_a=pass, phase=gate_b. Any HARD FAIL → state: gate_a=fail, phase=design (fix failing items only). SOFT WARN items are logged but do not block.

**Hard rule**: Gate-B MUST NOT start unless Gate-A = PASS.

---

## Phase 5: GATE-B (Semantic Review)

**Ref** (sub-agent reviewers): `references/phase_gate_b.md` + `references/review_assets.md` + `references/reviewer_prompts/<role>.md`

**Orchestrator**: Read summary.json only. Apply 6-condition PASS predicate. Handle early breaker AskUserQuestion on FAIL.

**Note**: Light mode skips Gate-B entirely. Proceed directly from Gate-A PASS to REVIEW.

**Entry check**: Gate-A = PASS AND Hard-Unresolved = 0.

**Map phase**: Launch N parallel Task(general-purpose) reviewers:
- Standard (default): 1-route self-review. If upgrade triggers fire → 3-route parallel (Architect + Security + QA)
- Full: 3-route parallel + meta-reviewer (4 total) with multi-model (via MCP `reviewer_dispatch`)
- Each reviewer gets prompt from `references/reviewer_prompts/<role>.md`
- Output: `.reviews/gateb/round-{N}/<role>.md`

**Reduce phase** [reduce sub-agent → orchestrator]: Reduce sub-agent merges reports into summary.json. Orchestrator reads summary.json, applies 6-condition PASS predicate:
1. P0 == 0
2. Hard-Unresolved == 0
3. All P1 closed (fixed or DEC risk-acceptance)
4. Evidence thresholds met
5. Strictness requirements met
6. Consistency verified

**Early breaker** (M4):
- Round 1 FAIL → automatic fix, enter Round 2
- Round 2 FAIL → present user with 3 choices: (a) automatic fix Round 3 (Full only), (b) scope cut → re-DESIGN, (c) risk acceptance + DEC record

**Result**:
- PASS → state: gate_b=pass, phase=review
- FAIL (rounds left) → **Checkpoint written** (Gate-B Round N Exit section) → **context restart** → state: gate_b=fail, phase=design. Bootstrap via `references/checkpoint_protocol.md` §4.
- FAIL (max rounds) → convergence 3-choice via AskUserQuestion

---

## Phase 6: REVIEW (Human Approval)

**Ref** (Mode B/C sub-agent): `references/phase_review.md`

**Summary**:
1. **RFC Briefing** (non-interactive): Display concise RFC overview before mode selection — title/scope, TL;DR (3-6 points), key DEC decisions, top HR constraints (≤5), must-pass SCN (≤5), accepted risks
2. **Mode selection** via AskUserQuestion: Standard / Progressive (推荐) / Interactive
3. Execute selected mode
4. Approve → state: baseline_accepted=true, phase=finalize
5. Reject → write rejection as DEC/CHG → state: phase=design

**Review Modes**:
- **Mode A: Standard Review** (default) — present rfc.md, binary approve/reject
- **Mode C: Progressive Review** — AI-guided risk-prioritized review with thinking models + Socratic challenges; AI recommends, user decides (recommended for Standard strictness)
- **Mode B: Interactive Review** — full section-by-section walkthrough with isolated sub-agent providing multi-perspective AI analysis; supports chapter selection + early exit (recommended for Full strictness / high-risk RFCs)

---

## Phase 7: FINALIZE

**Ref** (sub-agent): `references/phase_finalize.md`

**Summary**:
1. Export derivatives (tasks.md from SCN, acceptance checklist)
2. Archive process artifacts (events.jsonl, summary.json)
3. Lock rfc.md normative content. State: phase=finalize.

**Hard rule**: Post-baseline modification requires: CHG+DEC → Gate-A → Gate-B → re-approval.

---

## Post-Baseline Change

After baseline acceptance (`baseline_accepted=true`, `current_phase="finalize"`), modifications to rfc.md follow the Post-Baseline Change protocol instead of starting a new RFC.

**Entry**: `/ohrfc` → INIT workspace routing detects baselined RFC → user selects "变更已有 RFC: \<id\>"

**Flow**:
```
User selects change → scope estimate AskUserQuestion
    ↓
├─ "架构方向调整" → recommend new RFC
├─ "局部修改" / "跨模块变更" → enter change protocol:
│    DISCOVER-lite (scoped impact analysis) → CHG-### + DEC-###
│    → DESIGN-lite (modify affected sections only)
│    → Gate-A → Gate-B (strictness ≥ Standard) → REVIEW → Approve
```

**Key rules**:
- Gate-B strictness = `max(Standard, original_strictness)` (Light originals upgrade to Standard)
- Gate-B reviews full rfc.md (cascading effects); reviewer prompt marks changed sections
- No checkpoint/context restart unless Gate-B FAIL loop triggers it
- Change vs New RFC criteria: see `references/methodology.md` §9.3

**State transitions**: `finalize → baseline_change → design → gate_a → gate_b → review → finalize`

**Ref**: `references/phase_review.md` §Post-Baseline Change Flow, `references/methodology.md` §9.3

---

## Failure Loop State Transitions

> Light mode: only gate_a FAIL → design transition applies. No Gate-B loops.

| Current | Event | Target | Action |
|---------|-------|--------|--------|
| gate_a | FAIL | design | Located feedback; reset gate_a_result |
| gate_b | FAIL (round 1) | design | Automatic fix; reset gate_b_result |
| gate_b | FAIL (round 2) | — | Early breaker: 3-choice (auto-fix R3 if Full / scope cut / risk accept) |
| gate_b | FAIL (evidence gap) | discover | Evidence-only detour (1 per round max) |
| gate_b | FAIL (max rounds) | — | Convergence 3-choice; write DEC |
| review | Reject | design | Rejection reason as DEC/CHG |
| finalize | Scope change | baseline_change | CHG+DEC → gate_a → gate_b → review |

---

## Checkpoint Strategy

**See**: `references/checkpoint_protocol.md` (format, extraction prompts, bootstrap protocol)

**Principle**: Checkpoint is ALWAYS written at strategic boundaries. Context restart is mandatory on Gate-B FAIL → DESIGN (prevents accumulation from multiple Gate-B rounds pushing orchestrator toward compression threshold).

| Transition | Write? | Restart? |
|-----------|--------|----------|
| DISCOVER → DESIGN | Yes | No |
| DESIGN → GATE-A | Yes | No |
| GATE-B FAIL → DESIGN | Yes | **Yes** |
| REVIEW Reject → DESIGN | Yes | Optional |

**Reasoning preservation**: Each checkpoint uses structured extraction prompts (not open-ended "summarize"). Captures: user intent signals, design reasoning notes, decision interdependencies, reviewer feedback digest, active tensions. Budget: 200 lines / ~3K tokens.

**Bootstrap on restart**: state.json → checkpoint.md → rfc.md + evidence.json → Gate-B summary.json → phase references → Re-orient (sequential-thinking) → execute.

---

## Reference File Index

| File | Purpose | Load at |
|------|---------|---------|
| `references/phase_init.md` | INIT execution protocol | Phase 1 |
| `references/phase_discover.md` | DISCOVER execution protocol | Phase 2 |
| `references/phase_design.md` | DESIGN execution protocol | Phase 3 |
| `references/phase_gate_a.md` | GATE-A execution protocol | Phase 4 |
| `references/phase_gate_b.md` | GATE-B execution protocol | Phase 5 |
| `references/phase_review.md` | REVIEW execution protocol | Phase 6 |
| `references/phase_finalize.md` | FINALIZE execution protocol | Phase 7 |
| `references/methodology.md` | Core rules (strictness, IDs, expression, evidence, SCN) | Orchestrator (once at start) + sub-agents per phase |
| `references/rfc_template.md` | RFC section structure + skeleton | INIT, DESIGN |
| `references/design_assets.md` | SCN/DEC/Sources writing templates | DESIGN |
| `references/discover_assets.md` | QUICK_SCAN + clarify + risk templates | DISCOVER |
| `references/review_assets.md` | Reviewer output format + severity | GATE-B, DESIGN parallel |
| `references/security_template.md` | STRIDE deep-dive template | DESIGN (high-risk) |
| `references/reviewer_prompts/*.md` | Per-role review perspectives | GATE-B Map |
| `references/checkpoint_protocol.md` | Checkpoint format, extraction prompts, bootstrap | DISCOVER exit, DESIGN exit, GATE-B FAIL |
| `scripts/gate_a_check.py` | Automated 17-check Gate-A script (14 HARD + 3 SOFT) | GATE-A |
| `scripts/ohrfc_init.py` | Automated INIT phase (workspace + skeleton + state) | INIT |
| `assets/schemas/state.schema.json` | State tracking schema | INIT |
| `assets/schemas/evidence.schema.json` | Evidence record schema | DISCOVER |
| `assets/schemas/review_summary.schema.json` | Gate-B summary schema | GATE-B Reduce |
| `assets/examples/evidence.example.json` | Evidence record example | DISCOVER, DESIGN |
| `assets/examples/review_summary.example.json` | Gate-B summary example | GATE-B Reduce |
| `assets/examples/events.example.jsonl` | Debug events example | All phases (on truncation/timeout) |
