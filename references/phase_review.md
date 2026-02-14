# Phase: REVIEW (Human Approval)

> Present completed rfc.md to user for baseline acceptance.
> **Input**: Gate-B PASS (or Gate-B skip for Light) + rfc.md + summary.json
> **Output**: baseline_accepted = true/false

## Prerequisites

No reference files required by the orchestrator. Mode A presents rfc.md directly. Mode B dispatches an isolated sub-agent that loads its own context (rfc.md + evidence.json + summary.json).

## Context Loading

No additional references required. rfc.md is already in context from GATE phases.

## Execution

### RFC Briefing (pre-mode-selection)

Before presenting the mode selection AskUserQuestion, display a concise RFC content briefing as a progress report (non-interactive). This helps the user make an informed mode choice.

**Extract from rfc.md**:
- **Title + Scope** (§3): RFC title, scope boundaries, non-goals (2-3 lines)
- **Core Conclusions** (§4 TL;DR): 3-6 key points
- **Key Decisions** (DEC-### list): each on 1 line — decision + chosen option + rationale
- **Core Constraints** (top HR-###): up to 5 hard rules/red lines
- **Must-pass Scenarios** (§11 must-pass set): up to 5 critical acceptance scenarios
- **Accepted Risks** (DEC risk-acceptance items): if any exist

**Format**: Present as a structured text block (~10-15 lines). This is a progress report, NOT an AskUserQuestion.

**Relationship to Mode A**: Mode A subsequently presents rfc.md content in detail (full text for short docs, key-section summary for long docs). The Briefing is a more concise overview (~10-15 lines) to inform mode selection; Mode A's presentation is for the approval decision itself. They do not conflict.

### Mode Selection

**Mode selection**: Present review mode options via AskUserQuestion:

```
AskUserQuestion:
  header: "评审模式"
  question: "选择 RFC 评审模式"
  multiSelect: false
  options:
    - label: "Standard Review"
      description: "适合短文档或已充分了解内容，直接批准或拒绝"
    - label: "Progressive Review (推荐)"
      description: "AI 风险分析 + 优先级引导，{N} 个 Gate-B findings 待评审"
    - label: "Interactive Review"
      description: "逐章深度评审，适合高风险/复杂 RFC"
```

### Mode A: Standard Review (default)

1. **Present rfc.md** to user:
   - For short docs (< 200 lines): show full text
   - For long docs: show key-section summary (§4 TL;DR + §11 must-pass + §14 triggers) with offer to show full text

2. **Collect decision** via AskUserQuestion:
   - Option A: Approve (accept as baseline)
   - Option B: Reject (with modification feedback)

### Mode C: Progressive Review (AI-guided, recommended for Standard strictness)

AI-driven risk-prioritized review. AI does the heavy lifting (analysis + challenge + recommendation), user makes lightweight decisions (confirm/override).

**Execution context**: Progressive Review runs as an **isolated sub-agent** (same isolation boundary as Mode B) to prevent historical context pollution.

Inputs provided to review sub-agent:
1. `rfc.md` — the RFC document under review
2. `evidence.json` — evidence records supporting hard assertions
3. `.reviews/summary.json` — Gate-B reviewer findings (if Gate-B was run)
4. Gate-A SOFT warnings (checks 15-17, if any)

Not provided (isolation boundary):
- DISCOVER/DESIGN phase conversation history
- Checkpoint reasoning context
- Prior review attempt history

**Step 1: AI Pre-Analysis** (isolated sub-agent)

Use `mcp__sequential-thinking__sequentialthinking` (or internal reasoning) to apply multiple thinking models across the full RFC:

| Thinking Model | Challenge Question | Focus |
|---------------|-------------------|-------|
| First Principles | "哪些假设未被验证？" | Unvalidated assumptions in HR/DEC |
| Adversarial | "攻击者会利用什么？" | Security gaps, abuse surfaces |
| Systems Thinking | "跨系统耦合和反馈回路？" | Cross-boundary dependencies, emergent behaviors |
| Future Look-back | "2 年后这些决策还成立吗？" | Assumption expiry, scalability limits |
| Socratic Challenge | "我们在解决症状还是根因？" | Root cause vs symptom fixes |

Output: **Risk-sorted Focus Items list**, each containing:
- `location`: section + ID (e.g., "§5 DEC-003")
- `finding`: what was found
- `thinking_model`: which model surfaced it
- `severity`: P0 / P1 / P2
- `recommended_action`: specific fix or acceptance with rationale
- `socratic_question`: a question to help user think about the finding

Merge strategy: related low-priority items are grouped under the highest-severity item they relate to.

**Step 2: High-Priority Guided Review** (max 4 rounds AskUserQuestion)

Present Focus Items from high to low severity. Each round:
1. Show finding summary + thinking model analysis result
2. Present Socratic challenge question (guide user thinking)
3. AskUserQuestion:
   - Recommended action (推荐) + rationale
   - Alternative action(s)
   - "跳过此项" (defer to Step 3 batch)

Related lower-priority items are shown alongside their parent high-priority item.
Upper bound: 4 rounds of AskUserQuestion. Remaining items overflow to Step 3.

**Step 3: Low-Risk Batch Confirmation** (1 round AskUserQuestion)

Aggregate remaining items:
- Low-risk findings not covered in Step 2
- Sections with no findings (auto-confirmed)

AskUserQuestion (multiSelect=true):
- header: "批量确认"
- question: "以下低风险项和无发现章节，选择需要追加深度评审的项（未选中项自动通过）"
- Options: list of remaining items (label: location + 1-line summary)

Selected items → return to Step 2 format for one additional round.
Unselected items → auto-confirmed.

**Step 4: Final Verdict** (1 round AskUserQuestion)

Present decision summary:
- All confirmed items (from Steps 2-3)
- All modification requests (from Steps 2-3)
- Cross-section consistency check result

AskUserQuestion:
- header: "最终裁决"
- question: "确认评审结果"
- multiSelect: false
- Options:
  - "Approve" — accept RFC as baseline
  - "Reject" — return to DESIGN with aggregated feedback from all steps

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

**Step 0: Section Selection** (AskUserQuestion, multiSelect=true)

Present all 7 review sections with Gate-B findings count for each:

```
AskUserQuestion:
  header: "章节选择"
  question: "选择需要深度评审的章节（未选中章节展示摘要后自动通过）"
  multiSelect: true
  options:
    - label: "§3-4 约束与范围"
      description: "{N} 个 Gate-B findings"
    - label: "§5 方案架构"
      description: "{N} 个 Gate-B findings"
    - label: "§7 决策与权衡"
      description: "{N} 个 Gate-B findings"
    - label: "§8-9 安全与可靠性"
      description: "{N} 个 Gate-B findings"
    - label: "§11 验收场景"
      description: "{N} 个 Gate-B findings"
    - label: "§13-14 未决项与触发器"
      description: "{N} 个 Gate-B findings"
    - label: "整体评估"
      description: "跨章节一致性 + 最终裁决"
```

- Unselected sections: show 1-line summary, auto-mark as Confirmed.
- Selected sections: enter full AI analysis + Confirm/Request changes flow (Steps 1-7 below).
- If user selects "Other" → treat as "select all" (full Mode B).

**Review sequence** (selected sections only, each presented via AskUserQuestion):

1. **§3-4 Constraints & Scope**
   - AI analysis: boundary completeness, scope/non-goal coverage, constraint decidability
   - Thinking lens: First Principles — "What axioms are assumed? What if wrong?"
   - User: Confirm / Request changes / Early approve (approve all remaining sections)

2. **§5 Solution Architecture**
   - AI analysis: diagram-text consistency, component boundary clarity, interaction flow completeness
   - Thinking lens: Systems Thinking — "Feedback loops? Emergent behaviors? Cross-system coupling?"
   - Gate-B findings summary (if available): P0/P1 items in this section
   - User: Confirm / Request changes / Early approve

3. **§7 Decisions & Trade-offs**
   - AI analysis: every DEC has alternatives or single-path justification, residual risks explicit
   - Thinking lens: Future Look-back — "Will these trade-offs still make sense in 2 years? What assumptions expire?"
   - User: Confirm / Request changes / Early approve

4. **§8-9 Security & Reliability**
   - AI analysis: trust boundary coverage, abuse surface, failure/recovery contracts
   - Thinking lens: Adversarial — "What would an attacker exploit? What is cheapest attack with highest impact?"
   - Ecosystem lens: "How does this interact with adjacent systems? What trust assumptions cross boundaries?"
   - User: Confirm / Request changes / Early approve

5. **§11 Acceptance Scenarios**
   - AI analysis: SCN category coverage, must-pass set completeness, falsifiability check
   - Thinking lens: Test Thinking — "For each SCN, what does a failing test look like?"
   - User: Confirm / Request changes / Early approve

6. **§13 Unresolved & §14 Triggers**
   - AI analysis: Hard-Unresolved = 0 verified, Soft-Unresolved has owner+action, trigger format valid
   - Thinking lens: Long-term evolution — "Which Soft-Unresolved items will become urgent? What's the escalation path?"
   - User: Confirm / Request changes / Early approve

7. **Overall Assessment**
   - Synthesize: confirmed sections, requested changes, cross-section consistency
   - Final AskUserQuestion: Approve / Reject (with aggregated feedback)

**Early Approve**: If user selects "Early approve" at any section step, all remaining unreviewed sections are auto-confirmed and the flow jumps directly to step 7 (Overall Assessment).

**Request Changes → Re-Review Protocol**:
When user selects "Request changes" for a section:
1. User provides modification feedback (via AskUserQuestion "Other" or description)
2. Orchestrator applies changes to rfc.md
3. Re-present the modified section with updated AI analysis
4. User re-confirms: Confirm / Request changes again
5. Loop until confirmed (max 2 re-review rounds per section; if still unresolved, record as modification request in Overall Assessment)

### Process result (both modes)

- **Approve** → Update state.json: `baseline_accepted: true`, `current_phase: "finalize"`
- **Reject** → Write rejection reason as DEC/CHG in rfc.md. Update state.json: `current_phase: "design"`. Return to DESIGN with pinpointed feedback from each section review.

## Post-Baseline Change Flow

> After `baseline_accepted = true`, any modification to rfc.md follows this protocol.
> Entry: via `/ohrfc` INIT routing → user selects "变更已有 RFC: <id>" (see `references/phase_init.md` §Workspace Routing).

### Entry Conditions

- `baseline_accepted = true` in state.json
- User selects scope estimate via AskUserQuestion (see INIT routing):
  - "局部修改（1-2 个 section）" → proceed
  - "跨模块变更（≥3 个 section）" → proceed
  - "架构方向调整" → recommend new RFC; if user confirms, create new RFC and leave original unchanged

### DISCOVER-lite

Scoped version of DISCOVER — only analyzes change-affected areas.

1. Read existing `rfc.md` + user's change description
2. Identify affected sections, IDs (HR/DEC/SCN/REQ), and cross-references
3. Impact analysis: what else could be affected by the change (cascading dependencies)
4. Generate:
   - **CHG-###**: Change record — documents WHAT changed (affected sections, before/after delta)
   - **DEC-###**: Change decision — documents WHY the change was made, alternatives considered, trade-offs
5. Update state.json: `current_phase: "design"`

**Not performed** (vs full DISCOVER): full codebase scan, QUICK_SCAN, REASONING_PASS, evidence gathering for unrelated sections.

### DESIGN-lite

Scoped version of DESIGN — only modifies affected areas.

1. Modify only sections/IDs identified in DISCOVER-lite
2. Update all linked HR/SCN/DEC to maintain referential integrity
3. Self-check: verify the change does not introduce new Hard-Unresolved items
4. If new Hard-Unresolved found → must resolve before proceeding (same rules as normal DESIGN)
5. Update state.json: `current_phase: "gate_a"`

### Gate-A → Gate-B → REVIEW

Reuse existing gate and review phases without modification.

**Gate-B strictness for changes** (G2): The change Gate-B runs at `max(Standard, original_strictness)`. This means:
- Light original → change Gate-B at Standard level (upgrade)
- Standard original → change Gate-B at Standard level (same)
- Full original → change Gate-B at Full level (same)

**Gate-B review scope for changes** (G3): Gate-B reviews the **full rfc.md** (not just changed sections), because changes may have cascading effects on untouched sections. However, the reviewer prompt explicitly marks which sections/IDs were changed (via CHG-### references) so reviewers can focus their attention.

### Checkpoint Behavior (G5)

Post-Baseline Change flow does **not** use checkpoint/context restart by default. Rationale: change scope is bounded and context window is sufficient.

**Exception**: If the change triggers a Gate-B FAIL loop (Round 2+), the normal checkpoint/context restart logic applies (see `references/checkpoint_protocol.md`).

### State Transition Sequence

```
baseline_accepted=true, current_phase="finalize"
    ↓ user triggers change via INIT routing
current_phase="baseline_change"
    ↓ DISCOVER-lite complete
current_phase="design"
    ↓ DESIGN-lite + self-check complete
current_phase="gate_a"
    ↓ Gate-A PASS
current_phase="gate_b"
    ↓ Gate-B PASS
current_phase="review"
    ↓ Approve
baseline_accepted=true, current_phase="finalize"
```

### Result

- **Approve** → baseline updated. State: `baseline_accepted: true`, `current_phase: "finalize"`
- **Reject** → return to DESIGN-lite. Rejection reason written as DEC/CHG. State: `current_phase: "design"`
