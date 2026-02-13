#!/usr/bin/env python3
"""
Gate-A: Structural validation for rfc.md (17 checks: 14 HARD + 3 SOFT).

HARD checks (block progression):
1. Structure completeness (required sections)
2. ID integrity (format, uniqueness, no dangling refs)
3. Placeholder residuals (TBD/XXX/TODO/FIXME)
4. Expression rules (Mermaid brackets, fenced block tags)
5. Readability (SCN WHEN/THEN lines, paragraph length)
6. SCN category coverage (5 minimum categories)
7. Evidence cross-check (hard assertions -> EVD in evidence.json)
8. Strictness visibility (strictness field + upgrade DEC)
9. Trigger declarations (YES/NO format, Links non-empty)
10. HR→SCN binding (every HR referenced by at least one SCN)
11. DEC alternatives (every DEC has alternatives or single-path justification)
12. Must-pass validity (all SCN IDs in must-pass set exist)
13. Coverage matrix (Standard/Full strictness requires risk→SCN mapping)
14. Section non-empty (required sections have ≥3 non-whitespace lines)

SOFT checks (WARNING only, do not block):
15. Diagram-text pairing (mermaid blocks have nearby prose)
16. Unresolved format (Hard-Unresolved items have owner/action/convergence)
17. Orphan SCN (SCN not referenced by any HR or must-pass set)

Usage:
    python3 gate_a_check.py <rfc.md> [--evidence <evidence.json>] [--template <template.md>] [--dry-run]

Exit codes:
    0 - PASS (all hard checks passed, no soft warnings)
    0 - WARN (all hard checks passed, soft warnings exist; printed in report)
    1 - FAIL (any hard check failed)

Dry-run mode (--dry-run):
    Runs all 17 checks in advisory mode. Output is prefixed with [DRY-RUN].
    Final line shows DRY-RUN RESULT: WOULD_PASS or DRY-RUN RESULT: WOULD_FAIL (N HARD failures).
    Exit code is always 0 (advisory, not blocking).
"""

import sys
import re
import json
import copy
import argparse
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


# ─── Default configuration (used when gate_a_config.json is absent) ───

DEFAULT_CONFIG = {
    "min_scn_categories": [
        "normal", "reject_authn", "reject_authz",
        "limits_quota", "dependency_down", "abuse",
    ],
    "reject_categories": [
        "reject_authn", "reject_authz",
    ],
    "allowed_lang_tags": [
        "", "text", "contract", "json", "mermaid", "bash",
    ],
    "meta_fields": [
        "template_id", "template_version", "strictness",
    ],
    "review_keywords": [
        "背景", "痛点", "目标", "结论", "方案", "影响",
    ],
    "normative_keywords": [
        "安全", "可靠", "验收", "决策", "可观测",
    ],
    "heading_category_map": {
        "normal": "normal", "正常": "normal",
        "authn": "reject_authn", "authz": "reject_authz",
        "权限": "reject_authz", "越权": "reject_authz", "reject": "reject_authz",
        "limits": "limits_quota", "quota": "limits_quota",
        "非法值": "limits_quota", "边界": "limits_quota",
        "dependency": "dependency_down", "依赖": "dependency_down",
        "故障": "dependency_down", "recovery": "dependency_down",
        "abuse": "abuse", "滥用": "abuse", "鲁棒": "abuse",
    },
    "placeholder_patterns": [
        r"(?<![A-Za-z])TBD(?![A-Za-z])",
        r"(?<![A-Za-z])XXX(?![A-Za-z])",
        r"(?<![A-Za-z])TODO(?![A-Za-z])",
        r"(?<![A-Za-z])FIXME(?![A-Za-z])",
        r"<\.\.\.>",
    ],
}


def load_config(config_path: Optional[str] = None) -> dict:
    """Load gate-a configuration from JSON file, falling back to built-in defaults.

    Resolution order:
      1. Explicit *config_path* argument (if provided and file exists).
      2. ``gate_a_config.json`` next to this script.
      3. Built-in DEFAULT_CONFIG.

    Any key present in the JSON file overrides the corresponding default;
    keys absent from the JSON keep their default values.
    """
    cfg = copy.deepcopy(DEFAULT_CONFIG)  # deep copy to prevent mutation leaks

    if config_path is None:
        config_path = str(Path(__file__).resolve().parent / "gate_a_config.json")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)
        cfg.update(overrides)
    except (FileNotFoundError, json.JSONDecodeError):
        pass  # gracefully fall back to built-in defaults

    return cfg


# ─── Load configuration and derive module-level constants ───

_CFG = load_config()

MIN_SCN_CATEGORIES: Set[str] = set(_CFG["min_scn_categories"])
REJECT_CATEGORIES: Set[str] = set(_CFG["reject_categories"])
ALLOWED_LANG_TAGS: Set[str] = set(_CFG["allowed_lang_tags"])
META_FIELDS: List[str] = list(_CFG["meta_fields"])
REVIEW_KEYWORDS: List[str] = list(_CFG["review_keywords"])
NORMATIVE_KEYWORDS: List[str] = list(_CFG["normative_keywords"])
HEADING_CATEGORY_MAP: Dict[str, str] = dict(_CFG["heading_category_map"])
PLACEHOLDER_PATTERNS: List[str] = list(_CFG["placeholder_patterns"])

# Compiled regex patterns (built from configurable parts)
PLACEHOLDER_PATTERN = re.compile("|".join(PLACEHOLDER_PATTERNS))

# ID pattern: TYPE-NNN (3+ digits)
ID_PATTERN = re.compile(r'\b(HR|DEC|REQ|SCN|CHG|EVD)-(\d{3,})\b')
# Domain-prefixed HR pattern: e.g. SEC-HR-001, REL-HR-001, OBS-HR-001, LIMITS-HR-001
DOMAIN_HR_PATTERN = re.compile(r'\b([A-Z]+)-HR-(\d{3,})\b')

# Fenced block pattern
FENCED_BLOCK_PATTERN = re.compile(r'^```(\w*)', re.MULTILINE)

# Mermaid block content
MERMAID_BLOCK_PATTERN = re.compile(r'```mermaid\n(.*?)```', re.DOTALL)
MERMAID_BAD_CHARS = re.compile(r'[();]')

# SCN category declaration pattern
SCN_CATEGORY_PATTERN = re.compile(r'SCN-\d{3,}:\s*(\w+)')

# Hard assertion keyword patterns (for Check 7 proactive scan)
# Note: CJK characters don't support \b word boundaries; use lookaround or direct matching
HARD_ASSERTION_KEYWORDS = re.compile(
    r'(?:\b(?:must|forbidden|never|always|only|shall not)\b|(?:必须|禁止|不得|仅允许|不可))',
    re.IGNORECASE
)
HARD_ASSERTION_CONTEXT = re.compile(
    r'(?:\b(?:boundary|trust|permission|auth|security|limit|threshold|timeout|quota)\b|'
    r'(?:边界|信任|权限|安全|上限|阈值|超时|配额))',
    re.IGNORECASE
)


class CheckResult:
    def __init__(self, name: str, kind: str = "hard"):
        self.name = name
        self.kind = kind  # "hard" or "soft"
        self.passed = True
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def fail(self, msg: str):
        self.passed = False
        self.issues.append(msg)

    def warn(self, msg: str):
        self.warnings.append(msg)

    def __str__(self):
        if self.kind == "soft":
            status = "PASS" if not self.warnings else "WARN"
        else:
            status = "PASS" if self.passed else "FAIL"
        result = f"  [{status}] {self.name}"
        for issue in self.issues:
            result += f"\n         - {issue}"
        for w in self.warnings:
            result += f"\n         - [WARN] {w}"
        return result


def read_file(path: str) -> str:
    return Path(path).read_text(encoding='utf-8')


def load_evidence(path: Optional[str]) -> dict:
    if not path or not Path(path).exists():
        return {"items": []}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _domain_hr_spans(text: str) -> Set[Tuple[int, int]]:
    """Return character spans of domain-prefixed HR matches to avoid double-counting."""
    return {(m.start(), m.end()) for m in DOMAIN_HR_PATTERN.finditer(text)}


def _is_inside_domain_hr(pos: int, end: int, spans: Set[Tuple[int, int]]) -> bool:
    """Check if an ID_PATTERN match falls within a DOMAIN_HR match."""
    return any(s <= pos and end <= e for s, e in spans)


def extract_ids(text: str) -> Set[str]:
    """Extract all ID references (HR-001, DEC-002, etc.) from text."""
    ids = set()
    domain_spans = _domain_hr_spans(text)
    for m in ID_PATTERN.finditer(text):
        if not _is_inside_domain_hr(m.start(), m.end(), domain_spans):
            ids.add(f"{m.group(1)}-{m.group(2)}")
    for m in DOMAIN_HR_PATTERN.finditer(text):
        ids.add(f"{m.group(1)}-HR-{m.group(2)}")
    return ids


def extract_defined_ids(text: str) -> Tuple[Set[str], Set[str]]:
    """Extract IDs that are defined (appear at start of line or after heading) vs referenced."""
    lines = text.split('\n')
    defined = set()
    all_ids = set()

    for line in lines:
        stripped = line.strip()
        domain_spans = _domain_hr_spans(stripped)
        # ID at start of line, after bullet/heading, or in table cell = definition
        for m in ID_PATTERN.finditer(stripped):
            if _is_inside_domain_hr(m.start(), m.end(), domain_spans):
                continue
            full_id = f"{m.group(1)}-{m.group(2)}"
            all_ids.add(full_id)
            if (stripped.startswith(full_id)
                    or re.match(r'^[-*>#\d.]+\s*' + re.escape(full_id), stripped)
                    or re.match(r'^\|\s*' + re.escape(full_id), stripped)):
                defined.add(full_id)
        for m in DOMAIN_HR_PATTERN.finditer(stripped):
            full_id = f"{m.group(1)}-HR-{m.group(2)}"
            all_ids.add(full_id)
            if (stripped.startswith(full_id)
                    or re.match(r'^[-*>#\d.]+\s*' + re.escape(full_id), stripped)
                    or re.match(r'^\|\s*' + re.escape(full_id), stripped)):
                defined.add(full_id)

    return defined, all_ids


def extract_headings(text: str) -> List[str]:
    """Extract markdown headings."""
    return [line.strip().lstrip('#').strip() for line in text.split('\n') if line.strip().startswith('#')]


# === 9 CHECKS ===

def check_1_structure(rfc: str, template: Optional[str]) -> CheckResult:
    """Check 1: Structure & template consistency."""
    r = CheckResult("1. Structure & template consistency")

    rfc_headings = extract_headings(rfc)

    # Must have meta fields (anchored to line start to avoid substring false positives)
    for field in META_FIELDS:
        if not re.search(r'(?m)^\s*' + re.escape(field) + r'\s*[:：]', rfc):
            r.fail(f"Missing meta field: {field}")

    # Must have review layer + normative layer sections
    rfc_heading_text = ' '.join(rfc_headings)
    has_review = any(kw in rfc_heading_text for kw in REVIEW_KEYWORDS)
    has_normative = any(kw in rfc_heading_text for kw in NORMATIVE_KEYWORDS)

    if not has_review:
        r.fail("Missing review layer sections (背景/痛点/目标/结论/方案/影响)")
    if not has_normative:
        r.fail("Missing normative layer sections (安全/可靠/验收/决策/可观测)")

    if template:
        template_headings = extract_headings(template)
        # Check key template headings exist in rfc
        missing = []
        for th in template_headings[:20]:  # check first 20 template headings
            if th and not any(th in rh for rh in rfc_headings):
                missing.append(th)
        if len(missing) > 5:
            r.fail(f"Multiple template headings missing ({len(missing)}): {', '.join(missing[:5])}...")

    return r


def check_2_id_integrity(rfc: str) -> CheckResult:
    """Check 2: ID format, uniqueness, no dangling references."""
    r = CheckResult("2. ID integrity & references")

    defined, all_ids = extract_defined_ids(rfc)
    referenced = all_ids - defined

    # Check for duplicates (by counting occurrences at definition positions)
    lines = rfc.split('\n')
    id_def_count: Dict[str, int] = {}
    for line in lines:
        stripped = line.strip()
        domain_spans = _domain_hr_spans(stripped)
        for m in ID_PATTERN.finditer(stripped):
            if _is_inside_domain_hr(m.start(), m.end(), domain_spans):
                continue
            full_id = f"{m.group(1)}-{m.group(2)}"
            if stripped.startswith(full_id):
                id_def_count[full_id] = id_def_count.get(full_id, 0) + 1
        for m in DOMAIN_HR_PATTERN.finditer(stripped):
            full_id = f"{m.group(1)}-HR-{m.group(2)}"
            if stripped.startswith(full_id) or re.match(r'^[-*>#\d.]+\s*' + re.escape(full_id), stripped):
                id_def_count[full_id] = id_def_count.get(full_id, 0) + 1

    for id_str, count in id_def_count.items():
        if count > 1:
            r.fail(f"Duplicate ID definition: {id_str} (defined {count} times)")

    # Check dangling references
    dangling = referenced - defined
    if dangling:
        for d in sorted(dangling)[:10]:
            r.fail(f"Dangling reference: {d} (referenced but not defined)")

    return r


def check_3_placeholders(rfc: str) -> CheckResult:
    """Check 3: No TBD/XXX/TODO/FIXME/<...> residuals."""
    r = CheckResult("3. Placeholder residuals")

    for i, line in enumerate(rfc.split('\n'), 1):
        for m in PLACEHOLDER_PATTERN.finditer(line):
            r.fail(f"Line {i}: placeholder '{m.group()}' found")

    return r


def check_4_expression_rules(rfc: str) -> CheckResult:
    """Check 4: Mermaid brackets/semicolons; fenced block language tags."""
    r = CheckResult("4. Expression rules")

    # Check Mermaid blocks for bad characters
    for m in MERMAID_BLOCK_PATTERN.finditer(rfc):
        content = m.group(1)
        for i, line in enumerate(content.split('\n'), 1):
            if MERMAID_BAD_CHARS.search(line):
                r.fail(f"Mermaid block contains forbidden char [();] in: {line.strip()[:60]}")

    # Check fenced block language tags
    for m in FENCED_BLOCK_PATTERN.finditer(rfc):
        lang = m.group(1).lower()
        if lang and lang not in ALLOWED_LANG_TAGS:
            r.fail(f"Fenced block uses non-allowed language tag: '{lang}' (allowed: text, contract, json, mermaid, bash)")

    # Check for implementation code blocks
    impl_patterns = [r'^\s*(import |from |#include |package |using )', r'^\s*(def |class |func |fn |function )']
    in_code = False
    code_lang = ''
    for line in rfc.split('\n'):
        if line.strip().startswith('```'):
            if in_code:
                in_code = False
            else:
                in_code = True
                code_lang = line.strip()[3:].lower()
            continue
        if in_code and code_lang not in ('text', 'contract', 'mermaid', 'json', 'bash', ''):
            for pat in impl_patterns:
                if re.match(pat, line):
                    r.fail(f"Implementation code detected in fenced block ({code_lang}): {line.strip()[:60]}")
                    break

    return r


def check_5_readability(rfc: str) -> CheckResult:
    """Check 5: SCN WHEN/THEN separate lines; paragraph <=10 lines."""
    r = CheckResult("5. Readability")

    lines = rfc.split('\n')

    # Check SCN format: WHEN and THEN should be on separate lines
    in_scn = False
    scn_id = ''
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if re.match(r'SCN-\d{3,}', stripped):
            in_scn = True
            scn_id = stripped[:8]
        elif in_scn and (stripped.startswith('#') or stripped == '' or re.match(r'(HR|DEC|REQ|CHG)-\d{3,}', stripped)):
            in_scn = False

        if in_scn:
            # Check if WHEN and THEN are on the same line
            if 'WHEN' in stripped and 'THEN' in stripped:
                r.fail(f"Line {i}: {scn_id} has WHEN and THEN on same line (must be separate lines)")

    # Check consecutive paragraph length (skip code/mermaid blocks)
    consecutive_text = 0
    in_block = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('```'):
            in_block = not in_block
            consecutive_text = 0
            continue
        if in_block:
            continue
        if stripped and not stripped.startswith('#') and not stripped.startswith('-') and not stripped.startswith('|') and not stripped.startswith('>'):
            consecutive_text += 1
            if consecutive_text > 10:
                r.fail(f"Line {i}: consecutive text paragraph exceeds 10 lines (break into list/table)")
                consecutive_text = 0  # reset to avoid flooding
        else:
            consecutive_text = 0

    return r


def check_6_scn_coverage(rfc: str) -> CheckResult:
    """Check 6: Minimum SCN category coverage (5 types)."""
    r = CheckResult("6. SCN category coverage")

    found_categories = set()

    # Pattern 1: Inline SCN category declaration (e.g. "SCN-001: normal / ...")
    for m in SCN_CATEGORY_PATTERN.finditer(rfc):
        found_categories.add(m.group(1).lower())

    # Pattern 2: Category keyword in SCN lines
    for line in rfc.split('\n'):
        stripped = line.strip().lower()
        if 'scn-' in stripped:
            for cat in MIN_SCN_CATEGORIES:
                if cat in stripped:
                    found_categories.add(cat)

    # Pattern 3: Category in section headings (e.g. "### 12.2 正常路径（normal）")
    for line in rfc.split('\n'):
        stripped = line.strip()
        if stripped.startswith('#'):
            lower = stripped.lower()
            for keyword, cat in HEADING_CATEGORY_MAP.items():
                if keyword in lower:
                    found_categories.add(cat)

    has_reject = bool(found_categories & REJECT_CATEGORIES)
    required_non_reject = MIN_SCN_CATEGORIES - REJECT_CATEGORIES
    missing = required_non_reject - found_categories
    if not has_reject:
        missing.add("reject_authn or reject_authz")

    if missing:
        # Check if there's a DEC justifying the missing categories
        for cat in list(missing):
            cat_str = cat.replace("_", ".")
            if f"不适用" in rfc and cat_str in rfc.lower():
                missing.discard(cat)

        if missing:
            r.fail(f"Missing SCN categories (no DEC justification found): {', '.join(sorted(missing))}")

    return r


def check_7_evidence(rfc: str, evidence: dict) -> CheckResult:
    """Check 7: Evidence cross-check (hard assertions -> EVD in evidence.json).

    Two-part check:
      A) Existing: EVD refs in rfc.md must exist in evidence.json; truncated EVD must be surfaced.
      B) Proactive: HR definitions and hard assertion patterns must have EVD backing.
    """
    r = CheckResult("7. Evidence cross-check")

    evd_ids_in_json = set()
    for item in evidence.get("items", []):
        evd_id = item.get("evd_id", "")
        evd_ids_in_json.add(evd_id)
        # Check truncated evidence
        if item.get("truncated") and item.get("links_to"):
            links = item["links_to"] if isinstance(item["links_to"], list) else [item["links_to"]]
            for link in links:
                if "HR-" in str(link) or "REQ-" in str(link):
                    # Truncated evidence supporting hard assertion
                    if "Unresolved" not in rfc and "unresolved" not in rfc.lower():
                        r.fail(f"Truncated evidence {evd_id} supports hard assertion but no Unresolved/DEC in rfc.md")

    # Part A: Check EVD references in rfc exist in evidence.json
    rfc_evd_refs = set()
    for m in re.finditer(r'EVD-\d{3,}', rfc):
        rfc_evd_refs.add(m.group())

    missing_evd = rfc_evd_refs - evd_ids_in_json
    if missing_evd and evidence.get("items"):  # only check if evidence.json has items
        for evd in sorted(missing_evd)[:5]:
            r.fail(f"EVD referenced in rfc.md but missing in evidence.json: {evd}")

    # Part B: Proactive scan — HR definitions must have EVD backing
    # Build a map: for each paragraph/section, which EVD refs are nearby
    lines = rfc.split('\n')
    hr_definitions = []  # (line_num, hr_id, line_text)

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Find HR-### definitions (at start of line or after bullet/heading)
        for m in ID_PATTERN.finditer(stripped):
            if m.group(1) == 'HR':
                hr_id = f"HR-{m.group(2)}"
                hr_definitions.append((i, hr_id, stripped))
        for m in DOMAIN_HR_PATTERN.finditer(stripped):
            hr_id = f"{m.group(1)}-HR-{m.group(2)}"
            hr_definitions.append((i, hr_id, stripped))

    # For each HR, check if EVD is referenced within a +-10 line window or same section
    evd_line_pattern = re.compile(r'EVD-\d{3,}')
    for line_num, hr_id, line_text in hr_definitions:
        window_start = max(0, line_num - 10)
        window_end = min(len(lines), line_num + 11)
        window_text = '\n'.join(lines[window_start:window_end])
        has_evd_nearby = bool(evd_line_pattern.search(window_text))
        # Also check if any EVD in evidence.json links_to this HR
        has_evd_linked = False
        for item in evidence.get("items", []):
            links = item.get("links_to", [])
            if isinstance(links, str):
                links = [links]
            if any(hr_id in str(link) for link in links):
                has_evd_linked = True
                break
        if not has_evd_nearby and not has_evd_linked:
            r.fail(f"Hard rule {hr_id} has no EVD reference nearby or linked in evidence.json")

    # Part B.2: Scan for implicit hard assertions (must/forbidden/never in boundary/trust context)
    # that are NOT inside an HR definition (those are already checked above)
    hr_line_nums = {ln for ln, _, _ in hr_definitions}
    implicit_hard_count = 0
    implicit_hard_without_evd = 0
    for i, line in enumerate(lines):
        if i in hr_line_nums:
            continue
        stripped = line.strip()
        # Skip headings, empty lines, code blocks
        if not stripped or stripped.startswith('#') or stripped.startswith('```'):
            continue
        if HARD_ASSERTION_KEYWORDS.search(stripped) and HARD_ASSERTION_CONTEXT.search(stripped):
            implicit_hard_count += 1
            window_start = max(0, i - 5)
            window_end = min(len(lines), i + 6)
            window_text = '\n'.join(lines[window_start:window_end])
            if not evd_line_pattern.search(window_text):
                # Check if there's an HR nearby that already covers this
                has_hr_nearby = any(abs(i - ln) <= 5 for ln in hr_line_nums)
                if not has_hr_nearby:
                    implicit_hard_without_evd += 1

    if implicit_hard_without_evd > 0:
        r.fail(f"{implicit_hard_without_evd} implicit hard assertion(s) "
               f"(must/forbidden/never in boundary/trust context) lack EVD reference "
               f"(out of {implicit_hard_count} detected)")

    return r


def check_8_strictness(rfc: str) -> CheckResult:
    """Check 8: Strictness visibility (Light/Standard/Full or L1/L2/L3 declared)."""
    r = CheckResult("8. Strictness visibility")

    if 'strictness' not in rfc.lower():
        r.fail("No 'strictness' field found in rfc.md")
        return r

    # Accept both naming schemes: light/standard/full and L1/L2/L3
    strictness_match = re.search(
        r'strictness[）)：:\s]*(light|standard|full|L[123])',
        rfc, re.IGNORECASE
    )
    if not strictness_match:
        strictness_match = re.search(
            r'(?:strictness|严格度)[^\n]{0,20}(light|standard|full|L[123])',
            rfc, re.IGNORECASE
        )
        if not strictness_match:
            r.fail("Strictness field exists but no valid value found "
                   "(expected: light/standard/full or L1/L2/L3)")
            return r

    # Normalize to canonical level
    raw_level = strictness_match.group(1).lower()
    level_map = {
        'l1': 'L1', 'l2': 'L2', 'l3': 'L3',
        'light': 'L1', 'standard': 'L2', 'full': 'L3',
    }
    level = level_map.get(raw_level, raw_level.upper())

    # If L2/Standard with upgrade triggers, should have DEC
    if level == 'L2':
        upgrade_literal = ['升级', 'upgrade', '5-role']
        upgrade_regex = [r'5\s*个?\s*角色', r'5\s*roles?']
        has_upgrade = (any(kw in rfc.lower() for kw in upgrade_literal)
                       or any(re.search(pat, rfc, re.IGNORECASE) for pat in upgrade_regex))
        if has_upgrade:
            if not re.search(r'DEC-\d{3,}.*升级|DEC-\d{3,}.*upgrade', rfc, re.IGNORECASE):
                r.fail("Standard/L2 with upgrade to 5 roles detected but no DEC recording upgrade rationale")

    return r


def check_9_triggers(rfc: str) -> CheckResult:
    """Check 9: Trigger declarations (S14 or equivalent trigger block)."""
    r = CheckResult("9. Trigger declarations")

    # Find trigger section (match heading then capture until next same-or-higher-level heading)
    trigger_section = re.search(
        r'(?:#{1,4}\s*.*?(?:触发器|trigger|门禁触发|Gate Trigger).*?)\n(.*?)(?=\n#{1,3}\s|\Z)',
        rfc, re.DOTALL | re.IGNORECASE
    )
    if not trigger_section:
        r.fail("No trigger declaration section found (expected §14 or equivalent)")
        return r

    trigger_text = trigger_section.group(1)
    trigger_lines = trigger_text.split('\n')

    # Collect all defined IDs in the rfc for cross-reference validation
    defined_ids, _ = extract_defined_ids(rfc)

    # Parse trigger entries: support both table format and list format
    # Table format: | trigger name | YES/NO | Links: HR-001, SCN-002 |
    # List format: - trigger name: YES (Links: HR-001, SCN-002)
    yes_triggers_found = 0
    no_triggers_found = 0

    for i, line in enumerate(trigger_lines):
        stripped = line.strip()
        if not stripped:
            continue

        is_yes = bool(re.search(r'\bYES\b', stripped, re.IGNORECASE))
        is_no = bool(re.search(r'\bNO\b', stripped, re.IGNORECASE))

        if not is_yes and not is_no:
            continue

        if is_no:
            no_triggers_found += 1
            continue

        # YES trigger
        yes_triggers_found += 1

        # Extract trigger name for error messages
        trigger_name = stripped[:60].replace('|', ' ').strip()

        # Look for Links in current line and next 2 lines (for multi-line formats)
        search_window = stripped
        for offset in range(1, min(3, len(trigger_lines) - i)):
            search_window += ' ' + trigger_lines[i + offset].strip()

        # Find Links field
        links_match = re.search(r'Links?\s*[:：]\s*(.+?)(?:\||$)', search_window, re.IGNORECASE)

        if not links_match:
            r.fail(f"YES trigger missing 'Links:' field: {trigger_name}")
            continue

        links_content = links_match.group(1).strip()

        # Check Links is non-empty (not just whitespace/dashes/N-A)
        if not links_content or links_content in ('-', 'N/A', 'n/a', '—', '无', ''):
            r.fail(f"YES trigger has empty Links: {trigger_name}")
            continue

        # Validate referenced IDs exist
        linked_ids = set()
        domain_spans = _domain_hr_spans(links_content)
        for m in ID_PATTERN.finditer(links_content):
            if not _is_inside_domain_hr(m.start(), m.end(), domain_spans):
                linked_ids.add(f"{m.group(1)}-{m.group(2)}")
        for m in DOMAIN_HR_PATTERN.finditer(links_content):
            linked_ids.add(f"{m.group(1)}-HR-{m.group(2)}")

        if not linked_ids:
            r.fail(f"YES trigger Links contains no valid IDs: {trigger_name} → '{links_content}'")
            continue

        # Check linked IDs are defined
        dangling = linked_ids - defined_ids
        if dangling:
            r.fail(f"YES trigger Links references undefined IDs: {', '.join(sorted(dangling))} in: {trigger_name}")

    if yes_triggers_found == 0 and no_triggers_found == 0:
        r.fail("Trigger section has no YES/NO declarations")

    return r


# === NEW HARD CHECKS 10-14 ===

def check_10_hr_scn_binding(rfc: str) -> CheckResult:
    """Check 10: Every HR-### defined in rfc.md is referenced by at least one SCN-### body."""
    r = CheckResult("10. HR→SCN binding")

    defined, _ = extract_defined_ids(rfc)
    hr_ids = {did for did in defined if re.match(r'(?:[A-Z]+-)?HR-\d{3,}$', did)}

    if not hr_ids:
        return r  # No HR definitions, nothing to check

    # Extract SCN blocks and their content
    lines = rfc.split('\n')
    scn_blocks: Dict[str, str] = {}
    current_scn = None
    current_lines: List[str] = []

    for line in lines:
        stripped = line.strip()
        scn_match = re.match(r'(SCN-\d{3,})', stripped)
        if scn_match:
            if current_scn:
                scn_blocks[current_scn] = '\n'.join(current_lines)
            current_scn = scn_match.group(1)
            current_lines = [stripped]
        elif current_scn:
            # End SCN block at next heading or another ID definition
            if stripped.startswith('#') or re.match(r'(HR|DEC|REQ|CHG)-\d{3,}', stripped):
                scn_blocks[current_scn] = '\n'.join(current_lines)
                current_scn = None
                current_lines = []
            else:
                current_lines.append(stripped)

    if current_scn:
        scn_blocks[current_scn] = '\n'.join(current_lines)

    # Gather all IDs referenced inside SCN blocks
    scn_referenced_ids: Set[str] = set()
    for scn_id, scn_text in scn_blocks.items():
        scn_referenced_ids.update(extract_ids(scn_text))

    # Also check if HR is referenced in any line containing SCN (broader search)
    for line in lines:
        if 'SCN-' in line:
            scn_referenced_ids.update(extract_ids(line))

    for hr_id in sorted(hr_ids):
        if hr_id not in scn_referenced_ids:
            r.fail(f"HR {hr_id} is not referenced by any SCN block")

    return r


def check_11_dec_alternatives(rfc: str) -> CheckResult:
    """Check 11: Every DEC-### block contains alternatives or single-path justification."""
    r = CheckResult("11. DEC alternatives")

    defined, _ = extract_defined_ids(rfc)
    dec_ids = {did for did in defined if did.startswith('DEC-')}

    if not dec_ids:
        return r

    lines = rfc.split('\n')
    alternative_keywords = re.compile(
        r'替代|备选|alternative|option|trade-off|trade\s*off|方案\s*[A-Z]|方案\s*[一二三四五]',
        re.IGNORECASE
    )
    single_path_keywords = re.compile(
        r'唯一方案|single[- ]path|no\s+alternative|唯一选择|别无选择|only\s+option',
        re.IGNORECASE
    )

    for dec_id in sorted(dec_ids):
        # Find the DEC block: from definition line to next heading or ID definition
        in_dec = False
        dec_lines: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(dec_id) or re.match(r'^[-*>#\d.]+\s*' + re.escape(dec_id), stripped):
                in_dec = True
                dec_lines = [stripped]
                continue
            if in_dec:
                if stripped.startswith('#') or re.match(r'(HR|DEC|REQ|SCN|CHG)-\d{3,}', stripped):
                    break
                dec_lines.append(stripped)

        dec_text = '\n'.join(dec_lines)

        has_alternatives = bool(alternative_keywords.search(dec_text))
        has_single_path = bool(single_path_keywords.search(dec_text))

        if not has_alternatives and not has_single_path:
            # Also check broader context: ±5 lines around DEC definition for section-level alternatives
            dec_line_idx = None
            for i, line in enumerate(lines):
                if dec_id in line.strip():
                    dec_line_idx = i
                    break
            if dec_line_idx is not None:
                window = '\n'.join(lines[max(0, dec_line_idx - 5):dec_line_idx + 10])
                has_alternatives = bool(alternative_keywords.search(window))
                has_single_path = bool(single_path_keywords.search(window))

            if not has_alternatives and not has_single_path:
                r.fail(f"{dec_id} lacks alternatives/options or single-path justification")

    return r


def check_12_must_pass_validity(rfc: str) -> CheckResult:
    """Check 12: All SCN IDs listed in must-pass set (§11) exist as defined SCN-###."""
    r = CheckResult("12. Must-pass validity")

    defined, _ = extract_defined_ids(rfc)
    defined_scns = {did for did in defined if did.startswith('SCN-')}

    # Find §11 (验收) section
    section_11 = _extract_section(rfc, r'(?:11|验收)')
    if not section_11:
        return r  # No §11 found, skip check

    # Find must-pass set: look for must-pass/必须通过/must_pass patterns
    must_pass_pattern = re.compile(r'must[_-]?pass|必须通过|必通过', re.IGNORECASE)
    must_pass_text = ''
    lines = section_11.split('\n')
    in_must_pass = False
    for line in lines:
        stripped = line.strip()
        if must_pass_pattern.search(stripped):
            in_must_pass = True
            must_pass_text += stripped + '\n'
            continue
        if in_must_pass:
            if stripped.startswith('#') or stripped == '':
                if must_pass_text:
                    break
            else:
                must_pass_text += stripped + '\n'

    # If no explicit must-pass set, check all SCN references in §11
    if not must_pass_text:
        must_pass_text = section_11

    # Extract SCN IDs from must-pass text
    must_pass_scns: Set[str] = set()
    for m in re.finditer(r'SCN-\d{3,}', must_pass_text):
        must_pass_scns.add(m.group())

    # Validate all referenced SCN IDs exist
    for scn_id in sorted(must_pass_scns):
        if scn_id not in defined_scns:
            r.fail(f"Must-pass SCN {scn_id} is not defined in rfc.md")

    return r


def check_13_coverage_matrix(rfc: str) -> CheckResult:
    """Check 13: At Standard/Full strictness, §11 contains a risk→SCN mapping table."""
    r = CheckResult("13. Coverage matrix")

    # Determine strictness level
    strictness_match = re.search(
        r'(?:strictness|严格度)[^L\n]{0,20}(L[123])',
        rfc, re.IGNORECASE
    )
    if not strictness_match:
        # Also try Standard/Full/Light naming
        strictness_match = re.search(
            r'strictness[）)：:\s]*(Standard|Full|Light)',
            rfc, re.IGNORECASE
        )
        if not strictness_match:
            return r  # Can't determine strictness, skip

    level = strictness_match.group(1)
    # L1 or Light does not require coverage matrix
    if level.upper() in ('L1', 'LIGHT'):
        return r

    # Standard (L2) and Full (L3) require coverage matrix
    # Look for a table in §11 or a coverage matrix section
    section_11 = _extract_section(rfc, r'(?:11|验收)')
    coverage_section = _extract_section(rfc, r'(?:覆盖矩阵|coverage.?matrix|SCN.?覆盖)')

    search_text = (section_11 or '') + '\n' + (coverage_section or '')

    # Check for table with risk→SCN mapping (pipe-delimited table rows with SCN refs)
    table_rows = re.findall(r'^\s*\|.*SCN-\d{3,}.*\|', search_text, re.MULTILINE)
    if not table_rows:
        # Also accept list-based mapping with risk keywords
        risk_keywords = ['风险', '维度', 'risk', 'dimension', 'category', '路径', 'path']
        has_risk_scn_mapping = False
        for line in search_text.split('\n'):
            lower = line.lower()
            if any(kw in lower for kw in risk_keywords) and 'SCN-' in line:
                has_risk_scn_mapping = True
                break
        if not has_risk_scn_mapping:
            r.fail(f"Strictness {level} requires a risk→SCN coverage matrix in §11 but none found")

    return r


def check_14_section_non_empty(rfc: str) -> CheckResult:
    """Check 14: Each required template section has ≥3 lines of non-whitespace content."""
    r = CheckResult("14. Section non-empty")

    # Required sections (by heading pattern)
    required_sections = [
        (r'背景', '背景'),
        (r'目标', '目标'),
        (r'方案', '方案'),
        (r'(?:安全|安全模型)', '安全模型'),
        (r'(?:可靠|健壮)', '可靠性'),
        (r'验收', '验收'),
        (r'(?:决策|取舍)', '决策'),
    ]

    lines = rfc.split('\n')

    for pattern, label in required_sections:
        section_text = _extract_section(rfc, pattern)
        if section_text is None:
            continue  # Section doesn't exist; check_1 handles missing sections

        # Count non-whitespace lines (exclude heading itself and blank lines)
        content_lines = [
            l for l in section_text.split('\n')
            if l.strip() and not l.strip().startswith('#')
        ]
        if len(content_lines) < 3:
            r.fail(f"Section '{label}' has only {len(content_lines)} non-whitespace content line(s) (minimum 3)")

    return r


# === SOFT CHECKS 15-17 ===

def check_15_diagram_text_pairing(rfc: str) -> CheckResult:
    """Check 15 (SOFT): Every mermaid block has non-diagram text within 10 lines before or after."""
    r = CheckResult("15. Diagram-text pairing", kind="soft")

    lines = rfc.split('\n')
    in_mermaid = False
    mermaid_start = None

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped == '```mermaid':
            in_mermaid = True
            mermaid_start = i
        elif in_mermaid and stripped == '```':
            in_mermaid = False
            mermaid_end = i

            # Check for non-diagram text within 10 lines before start
            has_text_before = False
            for j in range(max(0, mermaid_start - 10), mermaid_start):
                l = lines[j].strip()
                if l and not l.startswith('```') and not l.startswith('#'):
                    has_text_before = True
                    break

            # Check for non-diagram text within 10 lines after end
            has_text_after = False
            for j in range(mermaid_end + 1, min(len(lines), mermaid_end + 11)):
                l = lines[j].strip()
                if l and not l.startswith('```') and not l.startswith('#'):
                    has_text_after = True
                    break

            if not has_text_before and not has_text_after:
                r.warn(f"Mermaid block at line {mermaid_start + 1} has no prose text within 10 lines before or after")

    return r


def check_16_unresolved_format(rfc: str) -> CheckResult:
    """Check 16 (SOFT): Hard-Unresolved items contain owner/action/convergence keywords."""
    r = CheckResult("16. Unresolved format", kind="soft")

    # Find Unresolved sections/items
    unresolved_pattern = re.compile(
        r'(?:Hard[- ]?Unresolved|硬性未决|未决事项)',
        re.IGNORECASE
    )
    owner_action_keywords = re.compile(
        r'(?:owner|负责人|action|行动|convergence|收敛|deadline|截止|DRI|assignee)',
        re.IGNORECASE
    )

    lines = rfc.split('\n')
    in_unresolved = False
    unresolved_items: List[Tuple[int, str]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if unresolved_pattern.search(stripped):
            in_unresolved = True
            continue
        if in_unresolved:
            if stripped.startswith('#'):
                in_unresolved = False
                continue
            if stripped.startswith('-') or stripped.startswith('*') or re.match(r'^\d+\.', stripped):
                unresolved_items.append((i + 1, stripped))

    for line_num, item_text in unresolved_items:
        if not owner_action_keywords.search(item_text):
            r.warn(f"Unresolved item at line {line_num} lacks owner/action/convergence keywords: {item_text[:60]}")

    return r


def check_17_orphan_scn(rfc: str) -> CheckResult:
    """Check 17 (SOFT): SCN-### not referenced by any HR or §11 must-pass set."""
    r = CheckResult("17. Orphan SCN", kind="soft")

    defined, _ = extract_defined_ids(rfc)
    defined_scns = {did for did in defined if did.startswith('SCN-')}

    if not defined_scns:
        return r

    # Collect SCN refs from HR lines and must-pass sections
    lines = rfc.split('\n')
    hr_referenced_scns: Set[str] = set()
    must_pass_scns: Set[str] = set()

    for line in lines:
        stripped = line.strip()
        # HR lines referencing SCNs
        if re.search(r'(?:[A-Z]+-)?HR-\d{3,}', stripped):
            for m in re.finditer(r'SCN-\d{3,}', stripped):
                hr_referenced_scns.add(m.group())

    # Must-pass set in §11
    section_11 = _extract_section(rfc, r'(?:11|验收)')
    if section_11:
        must_pass_pattern = re.compile(r'must[_-]?pass|必须通过', re.IGNORECASE)
        in_must_pass = False
        for line in section_11.split('\n'):
            stripped = line.strip()
            if must_pass_pattern.search(stripped):
                in_must_pass = True
            if in_must_pass or must_pass_pattern.search(stripped):
                for m in re.finditer(r'SCN-\d{3,}', stripped):
                    must_pass_scns.add(m.group())

    # Also check trigger Links for SCN references
    trigger_scns: Set[str] = set()
    trigger_section = _extract_section(rfc, r'(?:触发器|trigger|门禁触发|Gate Trigger)')
    if trigger_section:
        for m in re.finditer(r'SCN-\d{3,}', trigger_section):
            trigger_scns.add(m.group())

    all_referenced = hr_referenced_scns | must_pass_scns | trigger_scns

    for scn_id in sorted(defined_scns):
        if scn_id not in all_referenced:
            r.warn(f"Orphan SCN: {scn_id} is not referenced by any HR, must-pass set, or trigger Links")

    return r


# === Helper: extract a section by heading pattern ===

def _extract_section(rfc: str, heading_pattern: str) -> Optional[str]:
    """Extract section content from first heading matching pattern to next same-or-higher-level heading."""
    lines = rfc.split('\n')
    section_lines: List[str] = []
    in_section = False
    section_level = 0

    for line in lines:
        stripped = line.strip()
        heading_match = re.match(r'^(#{1,6})\s+(.+)', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2)
            if in_section:
                if level <= section_level:
                    break
                section_lines.append(stripped)
            elif re.search(heading_pattern, title, re.IGNORECASE):
                in_section = True
                section_level = level
                section_lines.append(stripped)
        elif in_section:
            section_lines.append(stripped)

    return '\n'.join(section_lines) if section_lines else None


# === Output aggregation ===

def run_gate_a(
    hard_results: List[CheckResult],
    soft_results: List[CheckResult],
) -> dict:
    """Aggregate check results into the 3-state output format.

    Returns:
        {
            "hard_pass": [check_name, ...],
            "hard_fail": [check_name, ...],
            "soft_warn": [check_name, ...],
            "overall": "PASS" | "FAIL" | "WARN",
            "details": { check_name: {"passed": bool, "issues": [...], "warnings": [...]} }
        }
    """
    hard_pass = [r.name for r in hard_results if r.passed]
    hard_fail = [r.name for r in hard_results if not r.passed]
    soft_warn = [r.name for r in soft_results if r.warnings]

    details = {}
    for r in hard_results + soft_results:
        details[r.name] = {
            "passed": r.passed,
            "issues": r.issues,
            "warnings": r.warnings,
        }

    if hard_fail:
        overall = "FAIL"
    elif soft_warn:
        overall = "WARN"
    else:
        overall = "PASS"

    return {
        "hard_pass": hard_pass,
        "hard_fail": hard_fail,
        "soft_warn": soft_warn,
        "overall": overall,
        "details": details,
    }


def main():
    parser = argparse.ArgumentParser(description='Gate-A: Structural validation for rfc.md')
    parser.add_argument('rfc_path', help='Path to rfc.md')
    parser.add_argument('--evidence', '-e', help='Path to evidence.json', default=None)
    parser.add_argument('--template', '-t', help='Path to template.md for structure comparison', default=None)
    parser.add_argument('--config', '-c', help='Path to gate_a_config.json', default=None)
    parser.add_argument('--dry-run', action='store_true',
                        help='Run all checks in advisory mode (exit code always 0)')
    args = parser.parse_args()

    if not Path(args.rfc_path).exists():
        print(f"Error: {args.rfc_path} not found")
        sys.exit(2)

    rfc = read_file(args.rfc_path)
    evidence = load_evidence(args.evidence)
    template = read_file(args.template) if args.template and Path(args.template).exists() else None
    cfg = load_config(args.config)

    hard_checks_cfg = cfg.get("hard_checks", {})
    soft_checks_cfg = cfg.get("soft_checks", {})

    # Checks 1-9 always run (no config toggle)
    hard_results = [
        check_1_structure(rfc, template),
        check_2_id_integrity(rfc),
        check_3_placeholders(rfc),
        check_4_expression_rules(rfc),
        check_5_readability(rfc),
        check_6_scn_coverage(rfc),
        check_7_evidence(rfc, evidence),
        check_8_strictness(rfc),
        check_9_triggers(rfc),
    ]

    # Checks 10-14: configurable hard checks (respect enabled flag)
    configurable_hard = [
        ("check_10_hr_scn_binding", lambda: check_10_hr_scn_binding(rfc)),
        ("check_11_dec_alternatives", lambda: check_11_dec_alternatives(rfc)),
        ("check_12_must_pass_validity", lambda: check_12_must_pass_validity(rfc)),
        ("check_13_coverage_matrix", lambda: check_13_coverage_matrix(rfc)),
        ("check_14_section_non_empty", lambda: check_14_section_non_empty(rfc)),
    ]
    for check_name, check_fn in configurable_hard:
        if hard_checks_cfg.get(check_name, {}).get("enabled", True):
            hard_results.append(check_fn())

    # Checks 15-17: configurable soft checks (respect enabled flag)
    configurable_soft = [
        ("check_15_diagram_text_pairing", lambda: check_15_diagram_text_pairing(rfc)),
        ("check_16_unresolved_format", lambda: check_16_unresolved_format(rfc)),
        ("check_17_orphan_scn", lambda: check_17_orphan_scn(rfc)),
    ]
    soft_results = []
    for check_name, check_fn in configurable_soft:
        if soft_checks_cfg.get(check_name, {}).get("enabled", True):
            soft_results.append(check_fn())

    report = run_gate_a(hard_results, soft_results)

    # Dry-run prefix helper
    dry_run = args.dry_run
    prefix = "[DRY-RUN] " if dry_run else ""

    # Report
    print(f"{prefix}{'=' * 60}")
    print(f"{prefix}GATE-A: Structural Validation Report")
    print(f"{prefix}{'=' * 60}")

    for r in hard_results + soft_results:
        for line in str(r).split('\n'):
            print(f"{prefix}{line}")

    print(f"{prefix}{'=' * 60}")
    overall = report["overall"]

    if dry_run:
        # Dry-run: advisory output, always exit 0
        failed_count = len(report["hard_fail"])
        if overall == "FAIL":
            print(f"{prefix}DRY-RUN RESULT: WOULD_FAIL ({failed_count} HARD failures)")
        else:
            print(f"{prefix}DRY-RUN RESULT: WOULD_PASS")
        sys.exit(0)

    # Normal mode
    if overall == "PASS":
        print(f"RESULT: PASS (all {len(hard_results)} hard checks passed)")
        sys.exit(0)
    elif overall == "WARN":
        warn_count = len(report["soft_warn"])
        print(f"RESULT: WARN (all hard checks passed, {warn_count} soft warning(s))")
        sys.exit(0)
    else:
        failed = len(report["hard_fail"])
        total_issues = sum(len(r.issues) for r in hard_results if not r.passed)
        print(f"RESULT: FAIL ({failed}/{len(hard_results)} hard checks failed, {total_issues} issues)")
        sys.exit(1)


if __name__ == '__main__':
    main()
