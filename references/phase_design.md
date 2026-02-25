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

## Quality Bar

> **Your output will be strictly cross-reviewed by multiple independent AI models, including Codex.**
>
> The rfc.md draft you produce will go through:
> 1. **Gate-A**: 22 automated mechanical checks (17 HARD blockers + 5 SOFT warnings) — structural compliance, ID uniqueness, expression format, SCN coverage, evidence cross-references, impact table dimensions, diagram type coverage, compatibility dimensions, cross-section redundancy, implementation detail detection
> 2. **Gate-B**: Multi-route semantic review by independent AI reviewers — including but not limited to **Codex** (known for strict, rigorous structural and logical analysis), plus Architect, Security, and QA perspective reviewers
>
> **Every failure triggers a rework cycle that wastes orchestrator context budget and delays delivery.** A single Gate-A HARD failure sends the entire draft back for revision. A Gate-B P0 finding blocks progression entirely.
>
> **Get it right the first time.** Treat every SCN expression format, every ID cross-reference, every evidence citation, and every section completeness requirement as non-negotiable. When in doubt, refer to `methodology.md` for the exact rules rather than guessing.

**If entering from Gate-A FAIL (fix cycle)**:
Orchestrator dispatches `Task(general-purpose)` sub-agent with Gate-A failure list + current rfc.md. Sub-agent follows **Batch Edit Protocol** (read once → analyze all → group edits → execute minimally → verify once with formal `gate_a_check.py`). Returns Gate-A PASS confirmation. Orchestrator trusts result and updates state directly.

**If entering from Gate-B FAIL (context restart)**:
Orchestrator executes Bootstrap Protocol from `references/checkpoint_protocol.md` §4. Provides checkpoint.md content in sub-agent prompt as reasoning context from previous phases. Sub-agent **must return the complete fixed rfc.md content** — not analysis or recommendations. The single-writer principle means the orchestrator writes rfc.md, but the sub-agent must produce the full document ready to write.

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
| §5 中出现方法/类名 | "Could a developer achieve the same external behavior with a different class/method name? If yes, abstract to functional role." | 编写 §5.1/§5.3 时 |
| §5.2 中出现同步原语 | "Is this a concurrency REQUIREMENT (no data race) or an implementation CHOICE (use mutex)? Only the former belongs." | 编写 §5.2 时 |

#### Emergent Fork Escalation

When Socratic Pause reveals a fork (§5 or §7: "Why this over the 2nd best?" has no clear answer):

**Escalation criteria** — escalate to user when ANY of:
1. **No dominant option**: No single option dominates on ≥2 of 3 axes (performance / complexity / maintainability)
2. **High blast radius**: Affects ≥3 downstream IDs AND spans ≥2 rfc.md sections
3. **Missing information**: Requires information unavailable to sub-agent (user preference / business priority / external constraint)

If none of the 3 criteria are met → sub-agent selects the recommended approach autonomously and records in DEC-### with alternatives + rationale.

**Escalation signal format** (returned to orchestrator):
```text
FORK_ESCALATION:
  section: §5 / §7
  description: <what the fork is about>
  criteria_met: [1|2|3]  # which escalation criteria triggered
  option_a: { summary, trade_offs, affected_ids[] }
  option_b: { summary, trade_offs, affected_ids[] }
  recommendation: A / B / none
```

**Orchestrator handling**:
1. Pause/restart DESIGN sub-agent
2. Present fork to user via AskUserQuestion (options with trade-offs + recommendation if any)
3. User's choice becomes a new constraint → sub-agent continues design with choice as input

**Conservative trigger constraints** (prevent over-escalation):
- Max 2 escalations per DESIGN phase
- Only **architectural-level** forks qualify (criteria 2 serves as minimum impact filter)
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

- §7 关键决策:
  - **Pause per DEC**: "Why this over the 2nd best? What's the strongest counterargument?"
  - Write: DEC-### with alternatives + rationale + trade-offs; Unresolved table (Hard/Soft)

- §5 方案概览:
  - **Pause**: "Is this the simplest design that satisfies ALL constraints?"
  - Write: End-to-end main path + contracts + design diagrams (A: architecture/boundary, B: interaction sequence, C: failure/convergence) + Notes per diagram

  **§5 抽象层级规则**:
  设计文档定义行为契约和性能边界，不预设实现方式。

  ❌ "模块 A 调用 ModuleB.getData() 获取 vector<pair<int, shared_ptr<Channel>>>"
  ✅ "数据分发层通过客户端映射服务按标识查询对应通道"

  ❌ "通过 mutex 保护内部状态"
  ✅ "内部状态并发访问安全（无数据竞争）"

  ❌ "使用 unordered_map 实现 O(1) 查询"
  ✅ "O(1) 查询复杂度（如通过哈希表实现）"

- §6 影响分析与兼容性:
  - **Pause**: "What downstream change triggers a cascade we haven't mapped?"
  - Write: Unchanged/changed/default strategy + breaking changes + rollback + evidence spot-checks

## Step 2: Fill Normative Layer (rfc.md §8-§11)

> **Cross-Section Deduplication**: Before writing §8/§9/§11, check if the constraint/scenario is already expressed in §5.2 (contracts) or §7 (decisions). If so, write a back-reference ('see DEC-###') instead of re-expressing the full logic. Each behavioral fact should have ONE authoritative location; other sections link to it.

Same Socratic Pause Protocol applies (Core C1+C2 + Section-fixed + Context-dynamic).

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

## Integrated Gate-A Check (mandatory)

After self-check passes, run formal Gate-A inside the DESIGN sub-agent:

```bash
python3 scripts/gate_a_check.py .ohrfc/<rfc_id>/rfc.md --evidence .ohrfc/<rfc_id>/evidence.json
```

- If PASS: capture output → proceed to Checkpoint Write → return rfc.md + Gate-A output to orchestrator
- If FAIL: fix failing items (following Batch Edit Protocol), re-run until PASS
- **Loop until PASS** — do NOT return a draft that fails Gate-A
- Orchestrator receives PASS result → updates state.json directly (gate_a_result: "pass", current_phase: "gate_b"), skips redundant re-run

This eliminates the double-execution pattern (dry-run + formal) while preserving audit integrity through the Gate-A output attached to the return.

## Checkpoint Write (after self-check passed)

Read `references/checkpoint_protocol.md` §3 DESIGN Exit Extraction prompt.
Append the DESIGN Exit section to `.ohrfc/<rfc_id>/checkpoint.md`.
Update state.json: `checkpoint_version += 1`, `last_checkpoint_phase: "design"`.
