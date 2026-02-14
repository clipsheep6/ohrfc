# Phase: DISCOVER & CLARIFY

> Scan codebase, identify risks, clarify with user, gather evidence. 4 sequential sub-steps.

## Prerequisites (sub-agent context)

The DISCOVER sub-agent must load:
- `references/discover_assets.md` — QUICK_SCAN template + clarify prompt + risk discovery + coverage checklist + EVIDENCE_TARGETED
- `references/methodology.md §6` — evidence thresholds and evidence.json field requirements
- `references/methodology.md §4` — ID system (HR/DEC/REQ/SCN/EVD naming and rules)
- `references/methodology.md §7` — Unresolved grading (Hard vs Soft)

The orchestrator does NOT read these files. It dispatches the sub-agent and handles CLARIFY (step 3) only.

## Sub-step 1: QUICK_SCAN (5-10s, no user interaction)

**Execution**: Launch as `Task(Explore)` sub-agent. Fallback: `Task(general-purpose)` if Explore unavailable. Model inherits from orchestrator by default; user can override at INIT.

Execute bounded codebase scan:

1. **Code symbol search** (entry points, API/IPC declarations, class/function definitions):
   - Prefer: `mcp__serena__find_symbol` / `mcp__serena__get_symbols_overview` for AST-level precision.
   - Fallback: Grep (if serena unavailable).
   - Glob: Find entry files (API/IPC/service stubs/external interface declarations). Limit: 200 paths max.
2. **Text/config search** (requirement keywords, error codes, config keys):
   - Prefer: Grep. Search requirement keywords (feature name, setting name, error code, module name). Limit: topk=50.
   - Fallback: `mcp__serena__search_for_pattern` (for complex multi-line patterns).
3. **Read**: Key entry files (max 5 files, 200 lines each).
4. Fill QUICK_SCAN output fields (from discover_assets.md §1):
   - `scan.repo_rev`, `scan.layout`, `scan.entrypoints`, `scan.keywords`, `scan.suspicions`
5. If truncated/timeout → Write event to `.debug/events.jsonl`; mark as Unresolved candidate if affects hard assertions.

**Progress report**: After QUICK_SCAN, report to user: "QUICK_SCAN complete — {N} entry files found, {M} keyword hits, {K} suspicions identified."

## Sub-step 2: REASONING_PASS (30-60s)

### Thinking Lens

Apply these lenses during reasoning:
- **First Principles**: "What axioms is this requirement assuming? What is the user's REAL goal?"
- **Future Look-back**: "If traffic/scale 10x in 2 years, does this design still hold?"
- **Inversion**: "What would make this project definitely FAIL? What single mistake would be fatal?"

### Execution

1. Use `mcp__sequential-thinking__sequentialthinking` or internal reasoning.
2. Input: QUICK_SCAN results + user requirement + clarify rules from discover_assets.md §2.
3. Output:
   - `risks.top` (3-7 items, each: status/consequence/trigger/suggested SCN category)
   - `unknowns.hard` / `unknowns.soft`
   - `strictness_recommendation`
   - Question candidates (4-field format: Evidence/Why/Options/Output), generated via the **Question Generation Pipeline**:

#### Question Generation Pipeline

Run four generators sequentially, then merge results:

| Generator | Input | Output | Example |
|-----------|-------|--------|---------|
| **A: Contradiction Detector** | QUICK_SCAN findings vs requirements | Tier 1 questions | "Code caps at 100 connections, but requirement says unlimited clients" |
| **B: Missing Constraint Discoverer** | Coverage Checklist (discover_assets.md §4) vs requirements | Tier 1-2 questions | "No failure recovery strategy mentioned; code does X — keep or change?" |
| **C: Fork Point Identifier** | REASONING analysis → ≥2 valid approaches | Tier 2 questions | "Pull vs Push model: Pull saves resources but adds latency — which?" |
| **D: Assumption Exposer** | must/always/never in requirements + EVD gap check | Tier 2-3 questions | "'Must support X' — from spec/compliance/experience? If preference, can downgrade to recommended" |

```
QUICK_SCAN output + user requirements
    ↓
Contradiction Detector → Missing Constraint Discoverer → Fork Point Identifier → Assumption Exposer
    ↓
Merge + deduplicate → Tier priority sort (see methodology.md §4.2) → Top questions
```

4. Filter: Tier 4 questions (self-answerable) → convert to EVIDENCE_TARGETED actions. Remaining questions sorted by Tier (1>2>3), then by affected ID count (descending).

**Progress report**: After REASONING_PASS, report to user: "Analysis complete — {N} risks identified, {M} unknowns ({H} hard, {S} soft), recommending strictness: {level}."

## Sub-step 3: CLARIFY (user interaction)

1. Show user QUICK_SCAN one-screen summary: confirmed facts + risk signals + strictness recommendation.
2. **Recommendation Pause** (for each question with a recommended option):
   - Use `mcp__sequential-thinking__sequentialthinking` (or internal reasoning) to challenge each recommendation:
   - **Socratic**: "What specific project-context reason supports this recommendation?"
   - **Steelman**: "What's the strongest argument for the option I'm NOT recommending?"
   - Survive: concrete reason exists → keep "(推荐)". Weak reasoning → present neutrally.
3. **Tiered Questioning** (aligned with AskUserQuestion tool limit: max 4 questions per call):
   - **Round 1 (mandatory)**: Tier 1-2 questions, max 4 per AskUserQuestion call.
     - Each question: Evidence anchor + Why asking + Options (2-4) + Which IDs affected
     - If Tier 1-2 ≤ 4 and no remaining Tier 3: CLARIFY complete after Round 1.
   - **Round 2 (conditional)**: Tier 3 questions, max 4 per AskUserQuestion call.
     - Triggered only when: Tier 3 questions exist AND mode is not Light.
     - Light mode: Round 1 only, max 3 questions total.
   - **Limits**: Standard/Full = max 2 rounds × 4 = 8 questions. Light = 1 round × 3 questions.
4. Write answers to rfc.md as DEC/REQ/SCN/HR.
5. Non-blocking unknowns → Soft-Unresolved with owner + follow-up action.

**Progress report**: After CLARIFY, report to user: "Clarifications recorded — {N} DEC/REQ/SCN written, {M} Soft-Unresolved tracked."

## Sub-step 4: EVIDENCE_TARGETED (30-60s, max 3 rounds)

1. Scan rfc.md for hard assertions (per methodology.md §6):
   - Numbers/limits/thresholds/timeouts
   - "must/forbidden/never/always/only" in boundary/permission/trust context
   - Current-state facts constraining design
2. For each hard assertion → locate evidence using appropriate search strategy:
   - **Code symbols** (function/class/interface definitions constraining the assertion): prefer `mcp__serena__find_symbol` / `mcp__serena__get_symbols_overview`. Fallback: Grep.
   - **Text/config** (literal values, error codes, config keys): prefer Grep. Fallback: `mcp__serena__search_for_pattern`.
   - Then Read source to confirm:
   - Record EVD-### in evidence.json (per methodology.md §6 field requirements)
   - **Anti-confirmation-bias**: Also search for evidence that CONTRADICTS the assertion. If contradicting evidence is found, surface it as a risk in rfc.md (Unresolved or DEC).
3. Insufficient evidence → write Unresolved/DEC in rfc.md
4. Truncation events → write `.debug/events.jsonl`
5. Update state.json: `current_phase → "design"`

**Progress report**: After each EVIDENCE_TARGETED round, report to user: "Evidence round {R}/{max} — {N} EVD collected, {M} open gaps remaining."

## Network Search (optional, disabled by default)

When enabled by user (explicit request or configuration):
- Use WebSearch/MCP tools to find external references: best practices, RFC standards, security advisories, vendor documentation.
- All external evidence → evidence.json with additional fields: `source_type: "external"`, `url`, `date`, `scope` (per methodology.md §6 external source requirements).
- External sources complement but do not replace codebase evidence for hard assertions.

## Parallel Optimization

When multiple hard assertions target different files/modules, launch parallel evidence searches:
- Use `Task(Explore)` sub-agents (max 3) for independent evidence hunts. Fallback: `Task(general-purpose)` if Explore unavailable.
- Each sub-agent: Grep+Read within a bounded file set → return EVD candidate
- Orchestrator merges EVD candidates into evidence.json (single-writer)
- Constraint: total parallel + sequential reads ≤ 15 files per round

**Note**: Evidence gathering can be parallelized via sub-agents. The orchestrator dispatches independent search tasks and merges results, maintaining single-writer discipline on evidence.json.

## Exit Conditions (all must be satisfied)

- [ ] rfc.md has ≥1 scope/non-goal REQ or DEC
- [ ] ≥3 hard rules (HR-###) drafts
- [ ] ≥3 falsifiable SCN-### drafts (no TBD/placeholders)
- [ ] Critical unknowns graded Hard/Soft in Unresolved section (per methodology.md §7)
- [ ] state.json current_phase = "design"

## Checkpoint Write (after exit conditions met)

Read `references/checkpoint_protocol.md` §3 DISCOVER Exit Extraction prompt.
Write the DISCOVER Exit section to `.ohrfc/<rfc_id>/checkpoint.md`.
Update state.json: `checkpoint_version += 1`, `last_checkpoint_phase: "discover"`.
