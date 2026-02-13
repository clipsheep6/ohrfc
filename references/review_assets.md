# REVIEW & Gate-B Assets

> **Load**: Gate-B phase (full text). Also used during DESIGN parallel gap-filling.
> **Purpose**: Standardized formats for reviewer output, design gap-fill, and human review checklist.
> **Sections**: §1 for Gate-B modes & output, §2 for DESIGN parallel agents, §3 for human REVIEW.

## 1. Gate-B Modes & Reviewer Output Format (P0/P1/P2)

### Gate-B Review Modes

Gate-B supports three review modes, determined by strictness and configuration:

| Mode | Routes | Reviewers | When Used |
|------|--------|-----------|-----------|
| **1-route self-review** | 1 | Merged checklist (Architect+Security+QA) | Light mode; Standard default |
| **3-route parallel (current model)** | 3 | Architect, Security, QA (parallel Task agents) | Standard (upgraded) |
| **3-route parallel (multi-model)** | 3 | Architect, Security, QA (via MCP/external models) | Standard/Full with `reviewer_dispatch` configured |

**Full mode** adds **Meta-Reviewer** as a 4th parallel agent (cross-cutting coherence analysis).

### Reviewer Roles

| Role | Focus | Mode Availability |
|------|-------|-------------------|
| **Architect** | Structural soundness, boundary clarity, design coherence | All modes (merged in 1-route) |
| **Security** | Trust boundaries, authorization, abuse prevention, auditability | All modes (merged in 1-route) |
| **QA** | Acceptance scenario quality, coverage completeness, falsifiability | All modes (merged in 1-route) |
| **Meta-Reviewer** | Cross-cutting coherence, thinking-lens analysis | Full mode only (or Standard-upgraded if explicitly added) |

> **Note**: Ops and Performance reviewer roles are **deprecated in v2.0**. Their checks are now absorbed by Architect (structural), Security (trust), and QA (testability).

### Output Format

Each Gate-B reviewer agent outputs findings using this format:

```text
Severity: P0 | P1 | P2
Location: <section/ID in rfc.md>
Issue: <what is wrong or missing>
Risk: <why it matters - consequence if not fixed>
Action: <concrete change - add/replace/delete which HR/DEC/SCN>
Evidence: EVD-### | external | user_input (if applicable)
```

Severity grading:
- **P0**: Boundary failure / security incident / data corruption / unrecoverable error / untestable acceptance (blocks Gate-B, one-veto)
- **P1**: Incomplete boundary/limits, unclear failure strategy, insufficient acceptance, high uncertainty from evidence gaps
- **P2**: Readability / consistency / minor gaps (does not block core correctness)

## 2. DESIGN Parallel Gap-Fill Output Format

When DESIGN phase uses parallel sub-agents for gap-filling, each agent writes isolated output:

Output path: `.reviews/design/round-*/<role>.md`

```text
Role: <Architect | Security | QA>
Bounds: <what reviewed / what NOT reviewed>

Findings:
- P0: <0..N> (Location + Issue + Risk + Action)
- P1: <0..N> (Location + Issue + Risk + Action)
- P2: <0..N> (optional)

Proposed edits (copy-paste ready):
- Add/Replace HR-###: <draft> (Links: SCN/DEC)
- Add/Replace SCN-###: <draft> (category=..., WHEN/AND/THEN multiline)
- Add/Replace DEC-###: <draft>

Hard assertions needing evidence:
- <assertion> → needs EVD-### (or move to Unresolved/DEC)

Unresolved to add:
- Hard: <...>
- Soft: <...>
```

## 3. Human REVIEW Checklist (10 items)

Present to user during REVIEW phase as evaluation guide:

1. **Baseline qualification**: rfc.md declares single normative truth; Gate-A PASS + Gate-B PASS confirmed
2. **One-page summary**: Goals / success criteria / scope & non-goals / top 3–5 constraints — complete and consistent
3. **System boundary**: Clear "what we do / don't do"; key interaction flows can be restated
4. **Constraints & red lines**: Specific and decidable (not slogans)
5. **Trust & abuse**: Assets and trust boundaries explicit; at least one executable abuse SCN (reject + no side effects)
6. **Failure closure**: Failure/recovery/degradation triggers and consequences clear; no unrecoverable/data-corruption risks uncovered
7. **Observability & audit**: Can support diagnosis and accountability (what to observe / what to audit)
8. **Acceptance falsifiability**: SCN are testable; minimum category coverage met
9. **Options & trade-offs**: Option Set and final DEC explain trade-offs and residual risks; hard assertions have verifiable sources
10. **Unresolved & risk**: Hard-Unresolved = 0; Soft-Unresolved has owner + follow-up action
