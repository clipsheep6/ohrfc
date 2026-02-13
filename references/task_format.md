# Task Format Specification

> **Load**: FINALIZE phase (task export) and post-baseline implementation.
> **Purpose**: Defines the structure for implementation tasks derived from rfc.md. Tasks are execution artifacts; rfc.md remains the sole normative truth.
> **Companion refs**: `phase_finalize.md` for export protocol; `methodology.md` §4 for ID system; `design_assets.md` for SCN/DEC writing format.

---

## 1. Task vs Spec (rfc.md)

| Aspect | rfc.md (Spec) | Task |
|--------|---------------|------|
| Authority | **Normative** — sole source of truth | **Derived** — execution artifact |
| Lifecycle | Survives baseline; changes require CHG+DEC+gates | Consumable; closed on completion |
| Granularity | System-level design decisions | Actionable implementation unit |
| Audience | Reviewers, architects, future maintainers | Developers, testers |

**Hard rule**: If a task contradicts rfc.md, rfc.md wins. Tasks MUST NOT introduce requirements not traceable to rfc.md.

---

## 2. Task Fields (6-field specification)

Each task consists of 4 **permanent** fields (retained for the task's entire lifecycle) and 2 **fade-out** fields (can be dropped after internalization).

### 2.1 `scope` (permanent)

Defines what the task touches and what it must not touch.

| Sub-field | Purpose | Example |
|-----------|---------|---------|
| `modify` | Files, modules, or components to change | `src/auth/authorizer.ts`, `config/permissions.yaml` |
| `boundary` | What is explicitly out of scope | `src/auth/token.ts` (no changes to token lifecycle) |

```text
scope:
  modify: src/auth/authorizer.ts, src/auth/policy_loader.ts
  boundary: token lifecycle (src/auth/token.ts), session management
```

### 2.2 `depends` (permanent)

Inter-task dependency by task ID. A task MUST NOT start until all dependencies are completed.

```text
depends: TASK-002, TASK-005
```

Use `none` when there are no dependencies.

### 2.3 `acceptance` (permanent)

Inline acceptance scenarios in SCN WHEN/THEN format, derived from rfc.md §11. Each task must bind to at least one SCN from the spec.

```text
acceptance:
  - SCN-003: WHEN unauthorized caller requests resource THEN system SHALL return 403 AND SHALL log denial
  - SCN-007: WHEN policy config missing THEN system SHALL use hardcoded defaults AND SHALL NOT fail open
```

### 2.4 `invariants` (permanent)

One-liner invariants that must hold during and after implementation, derived from rfc.md §8.1 (SEC-HR) / §9.1 (REL-HR) / §9.4 (INV).

```text
invariants:
  - INV-001: Policy evaluation MUST complete within 50ms p99
  - SEC-HR-003: Denied requests MUST be auditable within 24h
  - REL-HR-002: Dependency failure MUST NOT cascade to caller timeout
```

### 2.5 `context` (fade-out)

One-liner excerpts of design decisions (DEC) and historical rationale (HR) relevant to this task. Provides "why" context for implementers unfamiliar with the full spec.

```text
context:
  - DEC-004: Chose policy-pull over push — reduces coupling to config service
  - HR: Previous implementation had race condition on concurrent policy reload (see §7 DEC-004)
```

### 2.6 `on-ambiguity` (fade-out)

Protocol for handling cases not covered by the spec. Prevents implementers from making undocumented design decisions.

```text
on-ambiguity:
  - If policy format is unrecognized: reject + log (do NOT silently ignore)
  - If unsure about scope boundary: escalate to spec author before implementing
  - Unresolved: create DEC draft and flag for next rfc.md revision
```

---

## 3. Complete Task Example

```text
TASK-003: Implement policy-based authorization gate

scope:
  modify: src/auth/authorizer.ts, src/auth/policy_loader.ts, tests/auth/authorizer_test.ts
  boundary: token lifecycle (src/auth/token.ts), session management, API routing

depends: TASK-001, TASK-002

acceptance:
  - SCN-003: WHEN unauthorized caller requests resource THEN system SHALL return 403 AND SHALL log denial
  - SCN-007: WHEN policy config missing THEN system SHALL use hardcoded defaults AND SHALL NOT fail open
  - SCN-012: WHEN policy reload fails THEN system SHALL continue with last-known-good policy

invariants:
  - INV-001: Policy evaluation MUST complete within 50ms p99
  - SEC-HR-003: Denied requests MUST be auditable within 24h
  - REL-HR-002: Dependency failure MUST NOT cascade to caller timeout

context:
  - DEC-004: Chose policy-pull over push — reduces coupling to config service
  - DEC-007: Hardcoded defaults chosen over fail-open for security posture

on-ambiguity:
  - Unrecognized policy format: reject + log (do NOT silently ignore)
  - If boundary unclear: escalate to spec author before implementing
```

---

## 4. Traceability

Every task field should be traceable to its source section in rfc.md. Use HTML comment isolation for traceability annotations in generated task files:

```markdown
<!-- TRACE: §6.1 → TASK-003.scope.modify -->
<!-- TRACE: §11.3 → TASK-003.acceptance[SCN-003] -->
<!-- TRACE: §8.1 SEC-HR-003 → TASK-003.invariants -->
<!-- TRACE: §7 DEC-004 → TASK-003.context -->
<!-- TRACE: §7.1 Hard-Unresolved → TASK-003.on-ambiguity -->
```

Traceability comments are placed at the end of the task file or within an appendix block. They do NOT appear inline within task field values.

---

## 5. Task Generation Rules

Mapping from rfc.md sections to task fields:

| rfc.md Section | Task Field | What to Extract |
|----------------|------------|-----------------|
| §6 (Impact/Scope Analysis) | `scope` | Affected files/modules → `modify`; unchanged boundaries → `boundary` |
| §11 (Acceptance Scenarios) | `acceptance` | SCN-### in WHEN/THEN format (filter by task scope) |
| §8.1 / §9.1 (Security/Reliability Rules) | `invariants` | SEC-HR / REL-HR / INV relevant to task scope |
| §9.4 (Invariants) | `invariants` | INV-### one-liners |
| §1 TL;DR + §7 (Decisions) | `context` | DEC-### excerpts + historical rationale relevant to task |
| §7.1 (Open Questions) | `on-ambiguity` | Hard/Soft unresolved items affecting this task's scope |

**Generation process** (FINALIZE phase):

1. Parse rfc.md §11 → group SCN-### by module/component affinity
2. For each group, create a TASK with acceptance = grouped SCNs
3. Fill `scope.modify` from §6 impact analysis (files/modules mapped to those SCNs)
4. Fill `scope.boundary` from §4.2 non-goals + adjacent modules not in `modify`
5. Fill `invariants` from §8.1 + §9.1 + §9.4 filtered to task scope
6. Fill `context` from §7 DEC-### relevant to task scope
7. Fill `on-ambiguity` from §7.1 unresolved items intersecting task scope
8. Resolve `depends` from inter-task data/control flow analysis

---

## 6. Field Retirement Conditions

Fade-out fields can be dropped when their information is no longer needed for active development:

| Field | Retirement Condition | Rationale |
|-------|---------------------|-----------|
| `context` | Team has internalized design decisions (2+ sprint cycles after baseline) | DEC/HR context is absorbed through implementation experience; rfc.md remains available for deep reference |
| `on-ambiguity` | Spec gaps are resolved and merged back into rfc.md via CHG+DEC | Once the spec covers the ambiguous case, the handling protocol is redundant |

**Retirement process**: Remove fade-out fields from open tasks. Closed tasks retain all fields for audit trail.

---

## 7. Task ID Convention

Tasks use the prefix `TASK-` followed by a 3-digit zero-padded number:

```text
TASK-001, TASK-002, ..., TASK-NNN
```

Task IDs are unique within a single rfc.md workspace (`.ohrfc/<rfc_id>/`). Cross-RFC references use the full path: `<rfc_id>/TASK-###`.
