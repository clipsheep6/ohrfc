# Checkpoint Protocol

> Preserve reasoning context across phase boundaries while managing LLM context budget.
> **Rule**: Checkpoint is ALWAYS written at strategic points (low cost). Context restart is mandatory on Gate-B FAIL → DESIGN loop; optional elsewhere based on context pressure.

## 1. Checkpoint Trigger Points

| Transition | Write checkpoint? | Restart context? | Rationale |
|-----------|-------------------|-------------------|-----------|
| DISCOVER → DESIGN | **Yes** | No | Capture user intent nuances while context is still light |
| DESIGN → GATE-A | **Yes** | No | Capture design rationale before mechanical gate |
| GATE-B FAIL → DESIGN | **Yes** | **Yes** | Multi-round accumulation is the primary context exhaustion risk |
| REVIEW Reject → DESIGN | **Yes** | Optional (based on context pressure) | Restart only if context pressure warrants it |

**Context threshold**: With Thin Orchestrator model (orchestrator delegates heavy work to sub-agents), orchestrator context stays light — so restart is rare outside of Gate-B FAIL loops.

**Always-write rationale**: Checkpoint writes are cheap (~200 lines). The cost of NOT writing (losing reasoning context on unexpected crash or context limit) far exceeds the write cost. Therefore, always write at every trigger point regardless of context pressure.

## 2. Checkpoint File Format

**Location**: `.ohrfc/<rfc_id>/checkpoint.md`
**Budget**: 200 lines maximum. Each section group ≤ 40 lines.

```markdown
# Checkpoint: <rfc_id>

## Meta
- checkpoint_version: <integer, incremented on each write>
- last_phase: <discover|design|gate_b_round_N>
- strictness: <Light|Standard|Full>
- artifact_state: rfc.md(<sha256[:8]>), evidence(<N> items), gate_b_round=<N>

---

## DISCOVER Exit

### User Intent Signals
<!-- 3-7 bullets. Nuances from user clarifications BEYOND formal DEC/REQ -->

### Scan Insights
<!-- 2-4 bullets. Codebase patterns that influenced understanding but aren't in evidence.json -->

### Active Tensions
<!-- 1-3 bullets. Where requirements pull in opposite directions or interpretation required judgment -->

---

## DESIGN Exit

### Design Reasoning Notes
<!-- Per major DEC (max 7): close alternatives, fragile assumptions, decisive trade-off weights -->

### Decision Interdependencies
<!-- 2-5 bullets. Non-obvious linkages between DECs/HRs/SCNs -->

### Tricky Sections
<!-- 1-3 bullets. Sections where wording was carefully chosen; changing it breaks something subtle -->

---

## Gate-B Round <N> Exit
<!-- Appended per round. Delete previous round's section to stay within 200-line budget. -->

### Reviewer Feedback Digest
<!-- 3-5 bullets. META theme across reviewers, not individual findings -->

### What Changed This Round
<!-- 1-3 bullets. What was modified and WHY (reasoning, not just the diff) -->

### Active Tensions Updated
<!-- Resolved: / Intensified: / New: -->
```

## 3. Structured Extraction Prompts

At each checkpoint boundary, answer these specific questions. Each answer: **1 line per bullet**.

### DISCOVER Exit Extraction

```
Before proceeding to DESIGN, write checkpoint DISCOVER Exit section:

1. USER INTENT SIGNALS (3-7 bullets):
   - What priorities did the user emphasize beyond formal REQ/DEC entries?
   - Were there moments where the user's tone/emphasis revealed implicit constraints?
   - What was the user flexible about? What were they firm about?

2. SCAN INSIGHTS (2-4 bullets):
   - What codebase patterns will shape design choices but aren't formal evidence?
   - Any surprising discoveries not captured in evidence.json?

3. ACTIVE TENSIONS (1-3 bullets):
   - Where do requirements pull in opposite directions?
   - What's the most fragile assumption carried forward?
```

### DESIGN Exit Extraction

```
Before proceeding to GATE-A, append checkpoint DESIGN Exit section:

1. DESIGN REASONING NOTES (per major DEC, max 7):
   - What almost made you choose the alternative? How close was the decision?
   - What assumption, if invalidated, would flip this decision?

2. DECISION INTERDEPENDENCIES (2-5 bullets):
   - Which pairs of DECs/HRs are secretly coupled?
   - What downstream implications aren't formally tracked?

3. TRICKY SECTIONS (1-3 bullets):
   - Which section of rfc.md required the most careful wording?
   - What would a naive editor accidentally break?
```

### Gate-B FAIL Extraction

```
Before looping back to DESIGN, append checkpoint Gate-B Round <N> Exit section:

1. REVIEWER FEEDBACK DIGEST (3-5 bullets):
   - What is the META theme across all reviewer findings?
   - Which findings were borderline — could have gone either way?
   - Were reviewers aligned or pulling in different directions?

2. WHAT CHANGED THIS ROUND (1-3 bullets):
   - What was modified in rfc.md and what was the reasoning?
   - Was anything NOT changed despite feedback, and why?

3. ACTIVE TENSIONS UPDATED:
   - Resolved: (which earlier tensions?)
   - Intensified: (which got worse?)
   - New: (from this round's feedback?)
```

## 4. Bootstrap Protocol (on Context Restart)

When entering a phase after context restart, execute this exact sequence:

```
Step 0: READ state.json
        → Confirm current_phase, gate_b_round, strictness
        → Verify checkpoint_version > 0

Step 1: READ checkpoint.md (CRITICAL — this replaces conversation history)
        → Focus: ALL sections up to current phase
        → Pay special attention: Active Tensions, Reviewer Feedback Digest

Step 2: READ rfc.md (full) + evidence.json (full)
        → These are the current normative artifacts

Step 3: READ .reviews/summary.json (if gate_b_round > 0)
        → Extract: blocking_reasons, required_actions

Step 4: READ current phase references (per phase Context Loading block)
        → Standard lazy-load — same as normal phase entry

Step 5: RE-ORIENT (30s, sequential-thinking or internal reasoning)
        "Given the checkpoint, current rfc.md, and Gate-B feedback:
         - What is the core issue that caused the gate failure?
         - Which Design Reasoning Notes and Active Tensions are relevant?
         - What is my plan for this revision?"
        This step is internal reasoning — NOT written to any file.

Step 6: EXECUTE phase task (normal phase protocol)
```

## 5. Size Management

- Each section group (DISCOVER/DESIGN/Gate-B Round N): **≤ 40 lines**
- Total checkpoint.md: **≤ 200 lines** (~3K tokens)
- When Gate-B Round N+1 is written, **delete Round N-1** (keep only last 2 rounds)
- If any section exceeds budget: compress, do not truncate — signals over transcripts
