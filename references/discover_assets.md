# DISCOVER & CLARIFY Assets

> Consolidated from quick_scan_template.md + clarify_questions_prompt.txt + discover_assets.md.
> Load this file at the start of the DISCOVER phase.

## 1. QUICK_SCAN Template (5-10s, no user interaction)

Output fields (write to rfc.md DISCOVER section or temp notes):
- `scan.repo_rev`: current version identifier (commit/tag/build id)
- `scan.layout`: key directories & entry points (max 10 lines)
- `scan.entrypoints`: call entries/boundaries — API/IPC/driver/service (max 10 lines)
- `scan.keywords`: requirement keyword hits (max 10 lines)
- `scan.suspicions`: 3-5 risk signals re: boundary/compatibility/acceptance (can be empty)

Recommended scan actions:
- **Entry & boundary**: find external API/IPC declarations; find persistence/state read-write entries
  - Code symbols (functions/classes/interfaces): prefer `mcp__serena__find_symbol` / `mcp__serena__get_symbols_overview`. Fallback: Grep.
  - Text/config (keywords, error codes, config keys): prefer Grep. Fallback: `mcp__serena__search_for_pattern`.
- **Key path**: search requirement keywords (feature name, setting name, error code, module name); trace "who triggers, who decides, who persists, who notifies"
  - Code symbols: prefer serena semantic search for function/class definitions. Fallback: Grep.
  - Text/config: prefer Grep for keyword hits in comments, configs, strings.
- **Reliability**: check startup/restart/recovery paths; check existing rate-limit/quota/timeout/idempotency

Bounds: file count limit, search topk, timeout. If truncated → record `scan.truncated=true` with reason.

## 2. Clarify Questions Prompt

You are an OS-level service product architect and reliability reviewer. Based on the QUICK_SCAN summary, generate "few but critical" clarification questions using the **Question Generation Pipeline**.

### 2.1 Question Generation Pipeline

Run four generators sequentially on QUICK_SCAN output + user requirements:

**Generator A — Contradiction Detector**: Compare QUICK_SCAN findings against requirements. Surface where code contradicts requirements or requirements internally contradict. Each hit → Tier 1 candidate.

**Generator B — Missing Constraint Discoverer**: Walk Coverage Checklist (§4 below) against requirements. For each dimension:
- Requirement mentions it + code has it → check consistency (Generator A if mismatch)
- Requirement silent + code has it → "Requirement doesn't mention X; code does Y — keep or change?" (Tier 1-2)
- Requirement mentions it + code doesn't → "Requirement asks for X; no implementation found" (Tier 1)
- Both silent → "Dimension X has no information — include in scope?" (Tier 2-3)

**Generator C — Fork Point Identifier**: From REASONING analysis, identify points where ≥2 valid architectural approaches exist with distinct trade-offs. Each fork → Tier 2 candidate with trade-off summary.

**Generator D — Assumption Exposer**: Scan requirements for must/always/never/mandatory claims. For each, check if evidence (EVD) supports it. If no evidence or evidence is ambiguous → Tier 2-3 candidate: "Claim X — from spec/compliance/experience? If preference, can downgrade."

### 2.2 Question Format and Prioritization

Each question must have 4 fields:
- **Evidence**: what I observed (evidence anchor from QUICK_SCAN or code)
- **Why**: why asking (what decision it changes, which generator produced it)
- **Options**: 2-4 choices (1 sentence consequence each; recommended option first with "(推荐)" if challenge survives)
- **Output**: which IDs the answer maps to (DEC/REQ/HR/SCN)

**Priority sorting** (per methodology.md §4.2):
- Tier 1 (constraint conflict) > Tier 2 (direction fork) > Tier 3 (boundary clarification)
- Tier 4 (self-answerable): filter out → convert to EVIDENCE_TARGETED action
- Within same Tier: sort by affected ID count (descending)

### 2.3 Questioning Rounds

- **Round 1 (mandatory)**: Top Tier 1-2 questions, max 4 (AskUserQuestion tool limit)
- **Round 2 (conditional)**: Remaining Tier 3 questions, max 4. Only if Tier 3 questions exist AND not Light mode.
- **Light mode**: Round 1 only, max 3 questions.
- **Total limit**: Standard/Full = max 8 questions (2 rounds). Light = max 3 questions (1 round).

## 3. Risk & Opportunity Discovery Template

Output fields (write to rfc.md DISCOVER section, 1-3 lines each):
- `risks.top`: P0/P1 risk candidates (3-7 items; each: status/consequence/trigger/suggested chapter or SCN category)
- `opportunities`: optional optimization points (0-5; explicit "not blocking")
- `unknowns.hard`: Hard-Unresolved candidates (0-5; must state impact scope)
- `unknowns.soft`: Soft-Unresolved candidates (0-5)
- `strictness_recommendation`: suggested strictness + whether to upgrade to 5 roles (with rationale, 1-3 lines)
- `next_actions`: minimum next steps (3-7: which EVD to add / which SCN category to cover / which diagram to draw)

## 4. Coverage Checklist (active input for Generator B)

This checklist serves as the primary input for **Generator B (Missing Constraint Discoverer)**. For each dimension, Generator B checks requirement coverage and code presence, producing questions where gaps exist.

| Dimension | What to check | Generator B logic |
|-----------|---------------|-------------------|
| **Boundary & contract** | Who calls, what input/output, what's out of scope | Requirement silent + code has boundary → ask "keep or change?" |
| **Compatibility** | What must stay unchanged, what changes, default value strategy, rollback | Requirement mentions change + no rollback strategy → ask |
| **Trust boundary** | Who is trusted, where is authorization, how unauthorized/abuse is rejected | Any trust boundary change without explicit requirement → Tier 1 |
| **Resource budget** | CPU/memory/IO/frequency/queue limits and degradation | Code has limits + requirement silent → ask "current limits adequate?" |
| **Failure & recovery** | Dependency down / restart / recovery convergence, forbidden irreversible side effects | No recovery strategy mentioned → ask "add recovery or accept risk?" |
| **Acceptance falsifiability** | Minimum SCN categories covered, must-pass covers high-risk points | Gap in mandatory categories → flag for Generator B |

**Per-dimension evaluation** (Generator B applies this for each row):
1. Does the requirement explicitly address this dimension?
2. Did QUICK_SCAN find related code/config?
3. Are the two consistent?

Inconsistency or gap → produce Tier 1-2 question. Both silent → produce Tier 2-3 question with "include in scope?" framing.

## 5. EVIDENCE_TARGETED (30-60s, ≤3 rounds)

Identify hard assertions in rfc.md:
- Numbers/limits/thresholds/timeouts/size limits
- "must/forbidden/never/always/only" in boundary/permission/data/audit context
- Current-state facts used to constrain design
- Trust boundary & permission model assertions

For each hard assertion → locate evidence using appropriate search strategy:
- **Code symbols** (function/class/interface definitions constraining the assertion): prefer `mcp__serena__find_symbol` / `mcp__serena__get_symbols_overview`. Fallback: Grep.
- **Text/config** (literal values, error codes, config keys, comments): prefer Grep. Fallback: `mcp__serena__search_for_pattern`.
- Then Read source to confirm → record EVD-### in evidence.json:
- evd_id, source_type, locator, repo_rev, summary, truncated, confidence, links_to

Missing evidence → write Unresolved/DEC in rfc.md. Truncation → write events.jsonl.

## 6. STRIDE-lite Security Deep-Dive (optional, for high-risk)

Use when: high-risk / cross-trust-boundary / user requests deep-dive. Output: HR + SCN only, no implementation.

For detailed template → Read `references/security_template.md`

Quick coverage (1-2 HR+SCN per item):
- **S (Spoofing)**: who can call/represent whom? Identity source? → SEC-HR + SCN(reject_authn/authz)
- **T (Tampering)**: which inputs invalid/out-of-bounds? → HR + SCN(limits_quota/abuse)
- **R (Repudiation)**: which actions must be attributable? → audit invariant + SCN(observability/abuse)
- **I (Info disclosure)**: what data must not cross boundaries? → boundary rule + SCN(abuse)
- **D (Denial of service)**: resource bottlenecks? rejection/degradation on limit? → LIMITS-HR + SCN(limits_quota/abuse)
- **E (Elevation)**: privilege escalation/bypass paths? → SEC-HR + SCN(reject_authz/abuse)
