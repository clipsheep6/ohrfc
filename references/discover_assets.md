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
- **Key path**: search requirement keywords (feature name, setting name, error code, module name); trace "who triggers, who decides, who persists, who notifies"
- **Reliability**: check startup/restart/recovery paths; check existing rate-limit/quota/timeout/idempotency

Bounds: file count limit, search topk, timeout. If truncated → record `scan.truncated=true` with reason.

## 2. Clarify Questions Prompt

You are an OS-level service product architect and reliability reviewer. Based on the QUICK_SCAN summary, generate "few but critical" clarification questions.

Rules:
1. First list confirmed facts from scan (max 8), each with evidence anchor (path/keyword/observation).
2. Only ask questions whose answers change: interface contract, system boundary, compatibility, acceptance scenarios, security red lines, resource budgets, failure/recovery strategy.
3. Each question must have 4 fields:
   - **Evidence**: what I observed (evidence anchor)
   - **Why**: why asking (what decision it changes)
   - **Options**: A/B/C (if applicable; 1 sentence consequence each)
   - **Output**: which IDs the answer maps to (DEC/REQ/HR/SCN)
4. Delete questions solvable by "scan code again" → convert to EVIDENCE_TARGETED action.
5. Final output: max 1 batch, 3-7 questions, priority-ordered.

## 3. Risk & Opportunity Discovery Template

Output fields (write to rfc.md DISCOVER section, 1-3 lines each):
- `risks.top`: P0/P1 risk candidates (3-7 items; each: status/consequence/trigger/suggested chapter or SCN category)
- `opportunities`: optional optimization points (0-5; explicit "not blocking")
- `unknowns.hard`: Hard-Unresolved candidates (0-5; must state impact scope)
- `unknowns.soft`: Soft-Unresolved candidates (0-5)
- `strictness_recommendation`: suggested strictness + whether to upgrade to 5 roles (with rationale, 1-3 lines)
- `next_actions`: minimum next steps (3-7: which EVD to add / which SCN category to cover / which diagram to draw)

## 4. Coverage Checklist (anti-omission, 1-sentence conclusion per item)

- **Boundary & contract**: who calls, what input/output, what's out of scope
- **Compatibility**: what must stay unchanged, what changes, default value strategy, rollback
- **Trust boundary**: who is trusted, where is authorization, how unauthorized/abuse is rejected without side effects
- **Resource budget**: CPU/memory/IO/frequency/queue limits and degradation
- **Failure & recovery**: dependency down / restart / recovery convergence, forbidden irreversible side effects
- **Acceptance falsifiability**: minimum SCN categories covered, must-pass covers high-risk points

## 5. EVIDENCE_TARGETED (30-60s, ≤3 rounds)

Identify hard assertions in rfc.md:
- Numbers/limits/thresholds/timeouts/size limits
- "must/forbidden/never/always/only" in boundary/permission/data/audit context
- Current-state facts used to constrain design
- Trust boundary & permission model assertions

For each hard assertion → Grep+Read to locate evidence → record EVD-### in evidence.json:
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
