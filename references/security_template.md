# Security Model Deep-Dive Template

> **Load**: DESIGN phase, only when high-risk or cross-trust-boundary scenarios are detected.
> **Purpose**: STRIDE-based security analysis structure for rfc.md §8 expansion or standalone appendix.
> **When to use**: Trust boundary changes, auth model changes, sensitive data handling, abuse scope expansion.
> **Output**: Produces HR + SCN pairs; does NOT produce implementation code.

## Structure

### 1. 摘要
- Security boundary adjustments (1–3 sentences)
- Top 3 conclusions: C1 who can do what / C2 authorization point / C3 audit & anti-abuse baseline

### 2. 资产 (3–7 items)
- A-001: User intent in settings/policies
- A-002: System service availability & stability
- A-003: Accountability (caller attribution & audit evidence)
- A-004: Sensitive information

### 3. 参与方与攻击者模型
- **Trusted**: System services/apps/components
- **Untrusted**: Third-party apps/injectable paths/abnormal input sources
- **Attacker capabilities**: High-frequency calls, illegal parameter construction, identity spoofing (but cannot control OS identity source)

### 4. 入口与信任边界

| 入口ID | 调用方 | 输入 | 关键风险 |
|---|---|---|---|
| EP-001 | <API/IPC> | <参数> | <越权/注入/洪泛> |
| EP-002 | <配置源> | <键值/事件> | <非法值/抖动/不可用> |

Identity source: Must specify the ONLY trusted source + explicitly forbidden fields.

### 5. 威胁枚举 (STRIDE, 5-10 items)

| Category | ID | Threat | Output |
|---|---|---|---|
| S Spoofing | T-S-001 | <identity forgery> | SEC-HR + SCN(reject_authn/authz) |
| T Tampering | T-T-001 | <illegal params> | HR + SCN(limits_quota/abuse) |
| R Repudiation | T-R-001 | <unattributable action> | audit invariant + SCN(abuse) |
| I Info Disclosure | T-I-001 | <log leaks> | boundary rule + SCN(abuse) |
| D DoS | T-D-001 | <resource exhaustion> | LIMITS-HR + SCN(limits_quota/abuse) |
| E Elevation | T-E-001 | <privilege escalation> | SEC-HR + SCN(reject_authz/abuse) |

### 6. 缓解措施
| 威胁 | 缓解 | 控制点 | 证据/可观测 | 验收 SCN |
|---|---|---|---|---|

### 7. 审计与隐私
- Must audit: privilege use, auth failures, policy changes
- Attribution minimum: caller identity + input + decision + rejection reason
- Anti-flood: rate-limit/aggregate, no self-amplification, preserve attribution
- Privacy: minimize, anonymize, access control

### 8. 残余风险
- RR-001: <description> (acceptance reason + tracking owner)

### 9. 验收绑定
- At least 2-5 must-pass SCN covering: 越权/归因/洪泛/边界
