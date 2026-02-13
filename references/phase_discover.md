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

**Execution**: Launch as `Task(Explore)` sub-agent. Model inherits from orchestrator by default; user can override at INIT.

Execute bounded codebase scan:

1. **Glob**: Find entry files (API/IPC/service stubs/external interface declarations). Limit: 200 paths max.
2. **Grep**: Search requirement keywords (feature name, setting name, error code, module name). Limit: topk=50.
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

### Execution

1. Use `mcp__sequential-thinking__sequentialthinking` or internal reasoning.
2. Input: QUICK_SCAN results + user requirement + clarify rules from discover_assets.md §2.
3. Output:
   - `risks.top` (3-7 items, each: status/consequence/trigger/suggested SCN category)
   - `unknowns.hard` / `unknowns.soft`
   - `strictness_recommendation`
   - Question candidates (4-field format: Evidence/Why/Options/Output)
4. Filter: Delete questions solvable by "scan code again" → convert to EVIDENCE_TARGETED actions.

**Progress report**: After REASONING_PASS, report to user: "Analysis complete — {N} risks identified, {M} unknowns ({H} hard, {S} soft), recommending strictness: {level}."

## Sub-step 3: CLARIFY (user interaction)

1. Show user QUICK_SCAN one-screen summary: confirmed facts + risk signals + strictness recommendation.
2. AskUserQuestion: 1 batch of 3-7 decision-style questions (A/B/C + consequences per option).
   - Each question: Evidence anchor + Why asking + Options + Which IDs affected
3. Write answers to rfc.md as DEC/REQ/SCN/HR.
4. Non-blocking unknowns → Soft-Unresolved with owner + follow-up action.

**Progress report**: After CLARIFY, report to user: "Clarifications recorded — {N} DEC/REQ/SCN written, {M} Soft-Unresolved tracked."

## Sub-step 4: EVIDENCE_TARGETED (30-60s, max 3 rounds)

1. Scan rfc.md for hard assertions (per methodology.md §6):
   - Numbers/limits/thresholds/timeouts
   - "must/forbidden/never/always/only" in boundary/permission/trust context
   - Current-state facts constraining design
2. For each hard assertion → Grep+Read to locate evidence:
   - Record EVD-### in evidence.json (per methodology.md §6 field requirements)
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
- Use `Task(Explore)` sub-agents (max 3) for independent evidence hunts
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
