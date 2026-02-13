# OHRFC Methodology Reference

> Consolidated from SSOT.md + PHASES.md + GATES.md + EXECUTION.md.
> This file is loaded when the executing agent needs rule context. It does NOT redefine rules — SSOT.md is the canonical source if discrepancies arise.

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [Phase Sequence & Bounds](#2-phase-sequence--bounds)
3. [Strictness Levels](#3-strictness-levels)
4. [ID System](#4-id-system)
5. [Expression Rules](#5-expression-rules)
6. [Evidence Thresholds](#6-evidence-thresholds)
7. [Unresolved Grading](#7-unresolved-grading)
8. [SCN Category Coverage](#8-scn-category-coverage)
9. [Convergence & Exit](#9-convergence--exit)
10. [Parallel & Audit Rules](#10-parallel--audit-rules)
11. [Thinking Checklist](#11-thinking-checklist)

---

## 1. Core Principles

Design = confirm constraint set → narrow solution space → clarify trade-offs → verifiable acceptance

Essence of `rfc.md`:
- Constraint set: boundaries / prohibitions / limits (determine solution space)
- Invariants: red lines (security, no side effects, auditable)
- Trade-offs: how to choose among feasible paths (locked via DEC-###)
- Evidence: where key facts come from (verifiable)
- Acceptance: falsify/verify via SCN-### (not "feels right")

1. `rfc.md` is the sole normative truth — conclusions must be written back as DEC/REQ/SCN/CHG
2. Gate order fixed: Gate-A (mechanical) → Gate-B (semantic) → human REVIEW
3. Scan before asking; all expensive operations bounded (limits/timeouts)
4. Parallel only where outputs are naturally isolated; core state = single-writer
5. No implementation code/logs/configs in rfc.md; evidence referenced, not embedded
6. External assets must be explicitly Read (path link ≠ execution)

### 1.1 Tool Priority

| Purpose | Preferred | Fallback |
|---------|-----------|----------|
| Find files/symbols | `Glob` / `mcp__serena__find_symbol` | `Grep` |
| Search code/text | `Grep` / `mcp__code-index__search_code_advanced` | `mcp__serena__search_for_pattern` |
| Read files | `Read` | `mcp__serena__find_symbol` (include_body) |
| Create/write files | `Write` | `Edit` (for modifying existing files) |
| Reasoning/planning | `mcp__sequential-thinking__sequentialthinking` | Internal reasoning |
| User interaction | `AskUserQuestion` | — |
| Parallel subtasks | `Task` (subagent_type per need) | — |

### 1.2 Per-Phase Tool Permissions

| Phase | Allowed Tools |
|-------|--------------|
| INIT | Read, Write, Bash (mkdir), AskUserQuestion |
| DISCOVER | Read, Glob, Grep, Write, Edit, AskUserQuestion, sequential-thinking |
| DESIGN | Read, Write, Edit, Task (sub-agents: gap-filling), sequential-thinking |
| GATE-A | Read, Grep (mechanical checks), Write (summary), Edit (rfc.md fix) |
| GATE-B | Read, Task (sub-agents: parallel role review), Write (summary.json), Edit (rfc.md fix) |
| REVIEW | Read, AskUserQuestion |
| FINALIZE | Read, Write |

**All-phase prohibitions**:
- Do not execute implementation code (Skill output is design docs, not code)
- Do not modify methodology/reference files under `references/`

## 2. Phase Sequence & Bounds

```
INIT → DISCOVER&CLARIFY → DESIGN → GATE-A → [FAIL→DESIGN]
                                           → GATE-B → [FAIL→DESIGN/DISCOVER]
                                                    → REVIEW → [REJECT→DESIGN]
                                                             → FINALIZE
```

**Time boxes**: INIT <5s | DISCOVER 2-10min | DESIGN 2-5min | GATE 1-2min/round | REVIEW human | FINALIZE <30s

**Time-box expiry minimum output contract**:
- Do not extend discussions; surface key unknowns explicitly as Hard/Soft Unresolved and use `DEC-###` to lock current choices/assumptions/risk acceptance.
- Keep `rfc.md` at least in "Gate-A checkable" form: structure complete, IDs no placeholders, minimum SCN categories met, hard assertions either have evidence or are in Unresolved/DEC.

**Gate loop bounds**:
- Gate-A → DESIGN: unlimited (mechanical fix)
- Gate-B → DESIGN: Light=N/A / Standard=2 / Full=3 max rounds
- Gate-B → DISCOVER: max 1 per round (evidence gaps only)
- Max rounds exceeded: force convergence 3-choice

**Phase exit minimum contracts**:
- DISCOVER exit: ≥1 scope/non-goal REQ/DEC, ≥3 HR drafts, ≥3 SCN drafts, unknowns graded Hard/Soft
- DESIGN exit: structure complete, IDs no placeholders, minimal SCN categories met, self-check passed
- GATE-A exit: all 14 HARD checks must PASS; 3 SOFT checks produce warnings only (17 total)
- GATE-B exit: PASS predicate (6 conditions) satisfied

## 3. Strictness Levels

Three strictness levels control review depth, coverage requirements, and evidence obligations.

### 3.1 Light (user-triggered)

Simplified path for low-risk, well-understood changes.

- **Path**: DISCOVER (simplified: quick scan + 1 round clarification) → DESIGN (direct write, single sub-agent) → Gate-A (all HARD checks) → Human REVIEW
- **Skip**: Gate-B, multi-role review, convergence loops
- **Gate-B**: N/A (no Gate-B)
- **SCN coverage**: Mandatory minimum categories only; no coverage matrix required
- **Evidence**: Hard assertions only; minimal evidence obligation
- **Output**: Standard `rfc.md` format (less thorough, but structurally valid)
- **Activation**: User must explicitly request Light mode at INIT

### 3.2 Standard (default)

Full 7-phase path. Balances quality with efficiency.

| Dimension | Standard |
|-----------|----------|
| Goal | Quality/efficiency balance |
| Gate-B route | Default: 1-route self-review. If upgrade triggers fire → 3-route parallel |
| Option Set | Recommended (2-3) |
| DEC length | 4-6 lines, complex up to 10 |
| SCN coverage | Mandatory minimum + recommended matrix |
| Evidence | Hard assertions + key decisions |
| Gate-B max rounds | 2 |

**Standard auto-upgrade to 3-route parallel** (any trigger): trust boundary/auth changes, cross-process interaction, resource limits/quotas, startup/recovery/SLA impact, degradation/failure strategy changes, sensitive data/compliance, abuse scope expansion.

### 3.3 Full (user-triggered)

Full 7-phase path with maximum rigor.

| Dimension | Full |
|-----------|------|
| Goal | Conservative, reduce uncertainty |
| Gate-B route | 3-route parallel with multi-model (via MCP `reviewer_dispatch`) |
| Option Set | Mandatory (2-3, single-path needs DEC) |
| DEC length | Rigorous but not longer; prefer tables |
| SCN coverage | Mandatory minimum + mandatory matrix |
| Evidence | All decisions; gaps must be Hard-Unresolved |
| Gate-B max rounds | 3 |

### 3.4 OS/Framework 3 mandatory categories (all levels, cannot skip without DEC)

1. Reliability (recovery convergence): ≥1 REL-HR + ≥1 dependency_down SCN
2. Performance/resource bounds: ≥1 PERF-HR or LIMITS-HR + ≥1 limits_quota SCN
3. Security/trust boundary: ≥1 SEC-HR + ≥1 reject/abuse SCN

## 4. ID System

| ID | Purpose | Notes |
|----|---------|-------|
| HR-### | Hard rule / red line / limit | Must be decidable. Optional domain prefix: SEC-HR, REL-HR, API-HR |
| DEC-### | Decision & trade-off | Includes risk acceptance & mitigation |
| REQ-### | Requirement & constraint | Includes scope/non-goal |
| SCN-### | Acceptance scenario (EARS) | Chinese + WHEN/AND/THEN, must declare category |
| CHG-### | Post-baseline change | |
| EVD-### | Evidence | Must exist in evidence.json |

Rules: IDs globally unique; referenced IDs must exist (no dangling); deletion requires CHG/DEC; no TBD/XXX/TODO placeholders.

### 4.1 Concept Domain Coordination (Orthogonal Axes)

The most common confusion is not "nothing was written" but "the same term means different things in different sections." Fix: decompose concepts into orthogonal axes; define each axis in exactly one place.

**Orthogonal axes** (do not substitute one for another):
- Phase: INIT / DISCOVER&CLARIFY / DESIGN / GATE (A then B) / REVIEW / FINALIZE
- Strictness: Light / Standard / Full (controls coverage and review depth; never bypasses hard constraints)
- Artifact layer: `rfc.md` (normative truth) vs auxiliary inputs (evidence.json, summary, events)
- IDs: DEC/REQ/SCN/CHG/EVD (optionally TST) — anchor discussion results into documents for Gate scanning
- Gate semantics: Gate-A mechanical; Gate-B semantic; failure loops and bounds are fixed

**Maintenance rules** (prevent drift):
- To change "concept meaning / rule caliber," only modify the canonical source (SSOT); other documents reference, never redefine.
- Before adding a new concept, check: can it fit an existing axis? If yes, extend that axis's single definition; only add a new axis if not.

## 5. Expression Rules

**Forbidden in rfc.md**: implementation code, algorithm pseudo-code, log paste, config paste.

**Allowed fenced blocks**: language tag `text` or `contract` only; ≤30 lines or ≤2000 chars; must bind to at least one ID.

**Mermaid**: no parentheses `()` or semicolons `;` in text (renderer instability).

**Diagrams**: cannot be sole carrier of normative info; must pair with text bullet list.

**SCN format**: WHEN/AND/THEN on separate lines; no wall-of-text.

**Paragraph limit**: ≤10 consecutive lines of prose; break into list/table if longer.

### 5.1 Template Positioning (v1)

Templates provide the "exact headings / minimum skeleton" for rfc.md. They can change the "skin" (heading layout), but cannot change these hard facts:
- `rfc.md` is the sole normative truth
- Gate-A precedes Gate-B
- Bounded and auditable rules remain in force

**v1**: Only `rfc_template_os_service` is provided (OS/platform/framework service designs).

**Domain applicability**: For non-OS domains (Web API, DB migration, protocol design), the methodology (constraint set → solution space → trade-offs → acceptance) still applies, but template sections may be trimmed/replaced subject to:
- Write `DEC-###` explaining what was trimmed, why, and impact on coverage
- Must not violate core constraints (§1): sole truth, Gate order, bounded operations, single-writer, no implementation code, explicit asset loading
- Minimum SCN category coverage (§8) still applies (category names may be replaced with domain equivalents, but mapping must be documented in DEC)

## 6. Evidence Thresholds

**Hard assertions** (numbers/limits/thresholds/must/forbidden + boundary/permission/trust):
- Must have `source_type ≠ user_input` with verifiable `locator + repo_rev`
- If truncated and supporting hard assertion: must surface as Unresolved/DEC in rfc.md

**Evidence fields** (evidence.json per schema): evd_id, source_type, locator, repo_rev, summary, truncated, truncation_reason, confidence, links_to.

**External sources**: must specify origin/link, version, date, applicability scope.

**Network search (optional)**: DISCOVER phase optionally supports web search (via MCP/WebSearch tools) for external evidence. Default off; user can enable at INIT. External evidence written to `evidence.json` with `source_type=external`, and must include: `url`, `date`, `applicability_scope`. Network-sourced evidence is subject to the same hard-assertion verification rules as local evidence.

## 7. Unresolved Grading

**Hard-Unresolved** (blocks Gate-B): system boundary, trust/auth boundary, hard limits/red lines/compliance, acceptance criteria/rejection strategy.

**Soft-Unresolved** (allowed in Gate-B): everything else; must have owner + follow-up action.

**Rule**: Hard-Unresolved = 0 before entering Gate-B (fix or DEC risk-acceptance).

## 8. SCN Category Coverage

Minimum categories (each ≥1 SCN):
- `normal` — happy path
- `reject_authn` or `reject_authz` -- auth failure (Full: both recommended)
- `limits_quota` — resource/quota enforcement
- `dependency_down` — dependency unavailable
- `abuse` — attack/misuse

Coverage matrix: Full mandatory, Standard recommended, Light optional.

**Expansion triggers** (must add HR+SCN when hit):
- Trust boundary / authorization model change: ≥1 SEC-HR + ≥1 reject/abuse SCN
- Resource limit / degradation policy change: ≥1 LIMITS-HR or PERF-HR + ≥1 limits_quota SCN
- Recovery path change: ≥1 REL-HR + ≥1 dependency_down SCN
- Compatibility behavior change (defaults/error semantics/scope/observable behavior): ≥1 compatibility spot-check SCN

**Coverage obligation**: Every "new mechanism / new branch / new failure path" must bind ≥1 SCN (otherwise considered not closed).

**"Write beyond minimum" trigger**: When any expansion trigger is hit, the corresponding HR/SCN must be added; merely meeting the minimum category count is not sufficient.

## 9. Convergence & Exit

### 9.1 Early Breaker (per-round behavior)

- **Round 1 FAIL**: Automatic fix → enter Round 2
- **Round 2 FAIL**: Present user with three choices:
  1. **Automatic fix** → enter Round 3 (if max rounds allows; Full only)
  2. **Scope cut** → re-DESIGN (remove features causing failure)
  3. **Risk acceptance** → DEC record with residual risk + mitigation + tracking + owner + trigger

This replaces the previous "wait until max rounds" behavior. The user gets early visibility and control at Round 2.

### 9.2 Max-rounds convergence

When Gate-B hits max rounds (Standard=2, Full=3), the same 3-choice applies:
1. Scope cut -- remove features causing failure
2. Risk acceptance -- DEC with residual risk + mitigation + tracking + owner + trigger
3. Escalate -- get external input, retry (still bounded)

**Risk acceptance constraints**: P0 never acceptable; hard assertion evidence gaps prefer choice 1 or 3; unclear requirements prefer choice 1 or 3.

## 10. Parallel & Audit Rules

- **Single-writer**: only orchestrator writes rfc.md/evidence.json/state.json
- **Parallel workers**: write isolated outputs only (`.reviews/design/round-*/<role>.md`, `.reviews/gateb/round-*/<role>.md`)
- **Merge**: deterministic; scan partition results → evidence.json; Gate-B Map → Reduce summary
- **Audit**: truncation/timeout/limit-hit → events.jsonl; if affecting hard assertions → must map to Unresolved/DEC
- **Retention**: keep only last round of `.reviews/` by default; historical rounds require DEC

## 11. Thinking Checklist (Optional, not gated)

Before writing, consider:
- Decision variables: what dimensions can be chosen/traded?
- Objective function: what to optimize, why now?
- Failure modes: dependency down, restart, config churn, flooding → expected behavior → can SCN falsify?
- Resource bounds: CPU/memory/threads/queues/frequency → explicit limits + rejection/degradation?
- Security bounds: trust boundary, authorization point, unauthorized attempt → reject without side effects → attributable?
- Compatibility: what must not change, what will change, default value strategy, rollback?
- Observability: how to prove "decision happened / state converged / unauthorized rejected"?

**Socratic Pause**: In addition to this checklist, DESIGN and DISCOVER phases embed mandatory Socratic Pause questions at each section. See `references/phase_design.md` Step 1/2 and `references/phase_discover.md` Sub-step 2/3 for the full protocol.
