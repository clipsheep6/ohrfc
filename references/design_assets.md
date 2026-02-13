# DESIGN Writing Templates

> Load this file at DESIGN phase for SCN/DEC/Sources writing format guidance.

## 1. SCN (Acceptance Scenario) Template

```text
SCN-###: <category> / <short title>
WHEN <trigger/condition>
AND <additional condition> (optional)
THEN system SHALL <observable result>
AND SHALL NOT <forbidden side effect>
AND SHALL log <audit or observable output> (as needed)
Links: HR-### / REQ-### / DEC-### / CHG-### (as needed)
Source: EVD-### | external | user_input (only when not hard assertion)
```

Tips:
- WHEN/AND/THEN on separate lines (readable, harder to skip)
- Prioritize: observable result + forbidden side effect + audit point
- Category must be one of: normal, reject_authn, reject_authz, limits_quota, dependency_down, abuse

## 2. DEC (Decision) Template

Full format:
```text
DEC-###: <decision title>
Context: <why decide now>
Options considered: A / B / C (or "only one viable path" + reason)
Decision: <chosen option + key rationale>
Trade-offs: <what gained/lost>
Risks: <P0/P1 remaining>
Mitigations: <how contained>
Follow-ups: <owner + trigger/date>
Sources: EVD-### / external / user_input
```

Short DEC (Light/Standard recommended):
- Conclusion (1 line)
- Rationale (1-2 lines)
- Acceptance binding (1 line: Links: SCN-...)
- (Optional) Residual risk or follow-up (1 line)

Risk acceptance minimum: residual risk + why acceptable + mitigation/observation + owner for review/tracking.

## 3. Sources Table (section-end)

```text
| Ref | Type | Summary | Locator | Notes |
|-----|------|---------|---------|-------|
| EVD-001 | code | supports <hard assertion> | path:line-range | confidence=high |
| EXT-001 | external | <policy/spec> | doc/version/date | rationale |
```

## 4. Evidence Record (human-readable format)

```text
EVD-001
  source_type: code
  locator: src/auth/authorizer.ts#L10-L80
  repo_rev: <git-sha>
  summary: Current authz model and role mapping.
  truncated: false
  confidence: high
  links_to: REQ-004, HR-012, SCN-010
```

## 5. Option Set Writing Guide

**No real trade-off** (constrained to single path): don't write A/B/C. Write 1 short DEC: 2-4 sentences explaining "why only one viable path", name 1-3 excluded alternatives.

**Real trade-off exists**:
- Light/Standard: 2-column comparison table (3-5 rows) + 1-sentence conclusion. Details go to HR/SCN/Unresolved.
- Keep only differentiating dimensions; delete rows where columns agree (noise reduction).
- Full: 2-3 options mandatory; single option requires DEC explaining "why no viable alternatives".
