# Phase: REVIEW (Human Approval)

> Present completed rfc.md to user for baseline acceptance.
> **Input**: Gate-B PASS (or Gate-B skip for Light) + rfc.md + summary.json
> **Output**: baseline_accepted = true/false

## Prerequisites

No reference files required by the orchestrator. Mode A presents rfc.md directly. Mode B dispatches an isolated sub-agent that loads its own context (rfc.md + evidence.json + summary.json).

## Context Loading

No additional references required. rfc.md is already in context from GATE phases.

## Execution

**Mode selection**: Ask user which review mode to use (default: Standard Review).

### Mode A: Standard Review (default)

1. **Present rfc.md** to user:
   - For short docs (< 200 lines): show full text
   - For long docs: show key-section summary (§4 TL;DR + §11 must-pass + §14 triggers) with offer to show full text

2. **Collect decision** via AskUserQuestion:
   - Option A: Approve (accept as baseline)
   - Option B: Reject (with modification feedback)

### Mode B: Interactive Review (user opt-in, recommended for complex RFCs)

Walk through rfc.md section by section with AI-assisted analysis. Each section gets multi-perspective review before user confirms.

**Execution context**: Interactive Review runs as an **isolated sub-agent** to prevent historical context pollution.

Inputs provided to review sub-agent:
1. `rfc.md` — the RFC document under review
2. `evidence.json` — evidence records supporting hard assertions
3. `.reviews/summary.json` — Gate-B reviewer findings (if Gate-B was run)
4. Gate-A SOFT warnings (checks 15-17, if any)

Not provided (isolation boundary):
- DISCOVER/DESIGN phase conversation history
- Checkpoint reasoning context
- Prior review attempt history

The sub-agent performs each section analysis using only the provided artifacts, ensuring review judgment is independent of accumulated context biases.

**Review sequence** (7 items, each presented via AskUserQuestion):

1. **§3-4 Constraints & Scope**
   - AI analysis: boundary completeness, scope/non-goal coverage, constraint decidability
   - Thinking lens: First Principles — "What axioms are assumed? What if wrong?"
   - User: Confirm / Request changes

2. **§5 Solution Architecture**
   - AI analysis: diagram-text consistency, component boundary clarity, interaction flow completeness
   - Thinking lens: Systems Thinking — "Feedback loops? Emergent behaviors? Cross-system coupling?"
   - Gate-B findings summary (if available): P0/P1 items in this section
   - User: Confirm / Request changes

3. **§7 Decisions & Trade-offs**
   - AI analysis: every DEC has alternatives or single-path justification, residual risks explicit
   - Thinking lens: Future Look-back — "Will these trade-offs still make sense in 2 years? What assumptions expire?"
   - User: Confirm / Request changes

4. **§8-9 Security & Reliability**
   - AI analysis: trust boundary coverage, abuse surface, failure/recovery contracts
   - Thinking lens: Adversarial — "What would an attacker exploit? What is cheapest attack with highest impact?"
   - Ecosystem lens: "How does this interact with adjacent systems? What trust assumptions cross boundaries?"
   - User: Confirm / Request changes

5. **§11 Acceptance Scenarios**
   - AI analysis: SCN category coverage, must-pass set completeness, falsifiability check
   - Thinking lens: Test Thinking — "For each SCN, what does a failing test look like?"
   - User: Confirm / Request changes

6. **§13 Unresolved & §14 Triggers**
   - AI analysis: Hard-Unresolved = 0 verified, Soft-Unresolved has owner+action, trigger format valid
   - Thinking lens: Long-term evolution — "Which Soft-Unresolved items will become urgent? What's the escalation path?"
   - User: Confirm / Request changes

7. **Overall Assessment**
   - Synthesize: confirmed sections, requested changes, cross-section consistency
   - Final AskUserQuestion: Approve / Reject (with aggregated feedback)

### Process result (both modes)

- **Approve** → Update state.json: `baseline_accepted: true`, `current_phase: "finalize"`
- **Reject** → Write rejection reason as DEC/CHG in rfc.md. Update state.json: `current_phase: "design"`. Return to DESIGN with pinpointed feedback from each section review.

## Post-Baseline Change Flow

After `baseline_accepted = true`, any modification to rfc.md requires:
1. Write CHG-### + DEC-### documenting the change
2. Modify only affected sections/IDs
3. Re-run Gate-A (must PASS)
4. Re-run Gate-B (at least Standard level)
5. Human re-approval
