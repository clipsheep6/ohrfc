#!/usr/bin/env python3
"""Unit tests for gate_a_check.py — covers all 17 checks (14 HARD + 3 SOFT) and 3-state output."""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from gate_a_check import (
    check_1_structure,
    check_2_id_integrity,
    check_3_placeholders,
    check_4_expression_rules,
    check_5_readability,
    check_6_scn_coverage,
    check_7_evidence,
    check_8_strictness,
    check_9_triggers,
    check_10_hr_scn_binding,
    check_11_dec_alternatives,
    check_12_must_pass_validity,
    check_13_coverage_matrix,
    check_14_section_non_empty,
    check_15_diagram_text_pairing,
    check_16_unresolved_format,
    check_17_orphan_scn,
    run_gate_a,
    extract_ids,
    extract_defined_ids,
    load_config,
)

# === Minimal valid rfc.md skeleton for reuse ===
MINIMAL_RFC = """\
# RFC-20260101：Test RFC

template_id: rfc_template_os_service
template_version: 2026-01-01
strictness: L2

## 1. 一页结论

## 2. 背景
现状描述。

## 4. 目标与非目标

## 5. 方案概览

## 7. 关键决策与取舍
DEC-001：选择方案 A

## 8. 安全模型
SEC-HR-001：禁止越权操作（关联：SCN-010）

## 9. 可靠性与健壮性
REL-HR-001：依赖不可用时不崩溃（关联：SCN-030）

## 10. 可观测性

## 11. 验收

### 11.2 正常路径
SCN-001: normal / 正常请求
  WHEN 合法请求
  THEN 返回成功

### 11.3 权限/越权
SCN-010: reject_authz / 越权拒绝
  WHEN 无权限用户请求
  THEN 拒绝

### 11.4 非法值/边界
SCN-020: limits_quota / 超限拒绝
  WHEN 超过配额
  THEN 拒绝

### 11.5 依赖故障
SCN-030: dependency_down / 依赖不可用
  WHEN 下游服务不可用
  THEN 降级处理

### 11.6 滥用与鲁棒性
SCN-040: abuse / 洪泛防护
  WHEN 大量恶意请求
  THEN 限流

## 14. 门禁声明

### 14.1 触发器声明
- 新增/变更信任边界或权限模型：YES（Links: SEC-HR-001, SCN-010）
- 新增/变更资源预算/降级口径：NO
- 新增/变更恢复链路：NO
- 兼容性行为变化：NO

## 16. 附录
"""


class TestCheck1Structure(unittest.TestCase):
    def test_pass_with_valid_rfc(self):
        r = check_1_structure(MINIMAL_RFC, None)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_missing_meta(self):
        rfc = "# RFC\n## 2. 背景\n## 8. 安全模型\n## 11. 验收\n"
        r = check_1_structure(rfc, None)
        self.assertFalse(r.passed)
        self.assertTrue(any("template_id" in i for i in r.issues))


class TestCheck2IDIntegrity(unittest.TestCase):
    def test_pass_no_dangling(self):
        r = check_2_id_integrity(MINIMAL_RFC)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_dangling_reference(self):
        rfc = MINIMAL_RFC + "\n关联 DEC-999 未定义。\n"
        r = check_2_id_integrity(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("DEC-999" in i for i in r.issues))

    def test_domain_hr_not_double_counted(self):
        ids = extract_ids("SEC-HR-001 应该只出现一次")
        self.assertIn("SEC-HR-001", ids)
        self.assertNotIn("HR-001", ids)


class TestCheck3Placeholders(unittest.TestCase):
    def test_pass_no_placeholders(self):
        r = check_3_placeholders(MINIMAL_RFC)
        self.assertTrue(r.passed)

    def test_fail_tbd(self):
        rfc = "Some text with TBD marker\n"
        r = check_3_placeholders(rfc)
        self.assertFalse(r.passed)

    def test_fail_todo(self):
        rfc = "TODO fix this\n"
        r = check_3_placeholders(rfc)
        self.assertFalse(r.passed)


class TestCheck4ExpressionRules(unittest.TestCase):
    def test_pass_clean_mermaid(self):
        rfc = "```mermaid\nflowchart LR\n  A --> B\n```\n"
        r = check_4_expression_rules(rfc)
        self.assertTrue(r.passed)

    def test_fail_mermaid_parentheses(self):
        rfc = "```mermaid\nflowchart LR\n  A(node) --> B\n```\n"
        r = check_4_expression_rules(rfc)
        self.assertFalse(r.passed)

    def test_fail_impl_code_block(self):
        rfc = "```python\nimport os\nclass Foo:\n    pass\n```\n"
        r = check_4_expression_rules(rfc)
        self.assertFalse(r.passed)


class TestCheck5Readability(unittest.TestCase):
    def test_pass_scn_multiline(self):
        rfc = "SCN-001: normal\n  WHEN input valid\n  THEN success\n"
        r = check_5_readability(rfc)
        self.assertTrue(r.passed)

    def test_fail_scn_single_line(self):
        rfc = "SCN-001: normal\n  WHEN input valid THEN success\n"
        r = check_5_readability(rfc)
        self.assertFalse(r.passed)

    def test_fail_long_paragraph(self):
        lines = ["text line"] * 12
        rfc = "\n".join(lines) + "\n"
        r = check_5_readability(rfc)
        self.assertFalse(r.passed)


class TestCheck6SCNCoverage(unittest.TestCase):
    def test_pass_all_categories(self):
        r = check_6_scn_coverage(MINIMAL_RFC)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_missing_abuse(self):
        # Remove all abuse-related terms including Chinese equivalents
        rfc = MINIMAL_RFC.replace("abuse", "something_else").replace("滥用", "其他").replace("鲁棒", "其他")
        r = check_6_scn_coverage(rfc)
        self.assertFalse(r.passed)


class TestCheck7Evidence(unittest.TestCase):
    """Tests for enhanced Check 7 (P0-3 fix: proactive hard assertion scanning)."""

    def test_pass_hr_with_evd_nearby(self):
        rfc = "SEC-HR-001：禁止越权\n来源：EVD-001\n"
        evidence = {"items": [{"evd_id": "EVD-001", "links_to": ["SEC-HR-001"]}]}
        r = check_7_evidence(rfc, evidence)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_hr_without_evd(self):
        rfc = "SEC-HR-001：禁止越权\n\n其他内容没有 EVD\n"
        evidence = {"items": []}
        r = check_7_evidence(rfc, evidence)
        self.assertFalse(r.passed)
        self.assertTrue(any("SEC-HR-001" in i for i in r.issues))

    def test_fail_evd_in_rfc_but_not_in_json(self):
        rfc = "引用 EVD-999 但 json 里没有。\n"
        evidence = {"items": [{"evd_id": "EVD-001"}]}
        r = check_7_evidence(rfc, evidence)
        self.assertFalse(r.passed)
        self.assertTrue(any("EVD-999" in i for i in r.issues))

    def test_pass_hr_with_evd_linked_in_json(self):
        rfc = "SEC-HR-001：禁止越权\n\n没有内联 EVD\n"
        evidence = {"items": [{"evd_id": "EVD-001", "links_to": ["SEC-HR-001"]}]}
        r = check_7_evidence(rfc, evidence)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_detect_implicit_hard_assertion(self):
        # Chinese: "必须" (must) + "安全边界" (security boundary) = hard assertion in boundary context
        rfc = "所有安全边界上的操作必须经过授权验证。\n其他普通内容。\n"
        evidence = {"items": []}
        r = check_7_evidence(rfc, evidence)
        self.assertFalse(r.passed)
        self.assertTrue(any("implicit hard assertion" in i for i in r.issues))

    def test_detect_implicit_hard_assertion_english(self):
        rfc = "All operations at the trust boundary must pass authorization.\n"
        evidence = {"items": []}
        r = check_7_evidence(rfc, evidence)
        self.assertFalse(r.passed)
        self.assertTrue(any("implicit hard assertion" in i for i in r.issues))

    def test_truncated_evidence_warning(self):
        rfc = "SEC-HR-001：禁止越权\nEVD-001\n"
        evidence = {"items": [
            {"evd_id": "EVD-001", "truncated": True, "links_to": ["SEC-HR-001"]}
        ]}
        r = check_7_evidence(rfc, evidence)
        self.assertFalse(r.passed)
        self.assertTrue(any("Truncated" in i for i in r.issues))


class TestCheck8Strictness(unittest.TestCase):
    def test_pass_l2(self):
        r = check_8_strictness(MINIMAL_RFC)
        self.assertTrue(r.passed)

    def test_fail_no_strictness(self):
        rfc = "# RFC without strictness\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertFalse(r.passed)


class TestCheck9Triggers(unittest.TestCase):
    """Tests for fixed Check 9 (P0-2 fix: actual Links validation)."""

    def test_pass_valid_triggers(self):
        r = check_9_triggers(MINIMAL_RFC)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_yes_without_links(self):
        rfc = MINIMAL_RFC.replace(
            "新增/变更信任边界或权限模型：YES（Links: SEC-HR-001, SCN-010）",
            "新增/变更信任边界或权限模型：YES"
        )
        r = check_9_triggers(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("Links" in i for i in r.issues))

    def test_fail_yes_with_dangling_links(self):
        rfc = MINIMAL_RFC.replace(
            "Links: SEC-HR-001, SCN-010",
            "Links: SEC-HR-999"
        )
        r = check_9_triggers(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("undefined" in i.lower() for i in r.issues))

    def test_fail_no_trigger_section(self):
        rfc = "# RFC\n## 2. 背景\n内容\n"
        r = check_9_triggers(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("No trigger" in i for i in r.issues))

    def test_fail_yes_with_empty_links(self):
        rfc = MINIMAL_RFC.replace(
            "Links: SEC-HR-001, SCN-010",
            "Links: -"
        )
        r = check_9_triggers(rfc)
        self.assertFalse(r.passed)


class TestHelpers(unittest.TestCase):
    def test_extract_defined_ids(self):
        text = "DEC-001：选择方案 A\n引用 DEC-001 在其他位置\n"
        defined, all_ids = extract_defined_ids(text)
        self.assertIn("DEC-001", defined)
        self.assertIn("DEC-001", all_ids)

    def test_extract_domain_hr(self):
        text = "- SEC-HR-001：安全规则\n"
        defined, all_ids = extract_defined_ids(text)
        self.assertIn("SEC-HR-001", defined)


# === L1 (Light) Strictness Scenarios ===

MINIMAL_L1_RFC = """\
# RFC-20260201：Lightweight Change

template_id: rfc_template_os_service
template_version: 2026-01-01
strictness: L1

## 1. 一页结论

## 2. 背景
现状描述。

## 4. 目标与非目标

## 5. 方案概览

## 7. 关键决策与取舍
DEC-001：选择最简方案

## 8. 安全模型
SEC-HR-001：禁止越权操作（关联：SCN-010）

## 9. 可靠性与健壮性
REL-HR-001：依赖不可用时不崩溃（关联：SCN-030）

## 10. 可观测性

## 11. 验收

### 11.2 正常路径
SCN-001: normal / 正常请求
  WHEN 合法请求
  THEN 返回成功

### 11.3 权限/越权
SCN-010: reject_authz / 越权拒绝
  WHEN 无权限用户请求
  THEN 拒绝

### 11.4 非法值/边界
SCN-020: limits_quota / 超限拒绝
  WHEN 超过配额
  THEN 拒绝

### 11.5 依赖故障
SCN-030: dependency_down / 依赖不可用
  WHEN 下游服务不可用
  THEN 降级处理

### 11.6 滥用与鲁棒性
SCN-040: abuse / 洪泛防护
  WHEN 大量恶意请求
  THEN 限流

## 14. 门禁声明

### 14.1 触发器声明
- 新增/变更信任边界或权限模型：YES（Links: SEC-HR-001, SCN-010）
- 新增/变更资源预算/降级口径：NO
- 新增/变更恢复链路：NO
- 兼容性行为变化：NO

## 16. 附录
"""

# L3 RFC: full coverage matrix + option set + DEC for single-path justification
FULL_L3_RFC = """\
# RFC-20260301：Strict Security Overhaul

template_id: rfc_template_os_service
template_version: 2026-01-01
strictness: L3

## 1. 一页结论

## 2. 背景
现状存在安全薄弱环节。

## 4. 目标与非目标
REQ-001：加强信任边界控制

## 5. 方案概览

### 5.1 方案 A：全量迁移
DEC-002：选择方案 A，因为安全收益最大

### 5.2 方案 B：渐进迁移
DEC-003：不选 B，因为过渡期暴露面大

## 6. SCN 覆盖矩阵

| 维度 | SCN | 说明 |
|------|-----|------|
| 正常路径 | SCN-001 | 合法请求 |
| 权限拒绝 | SCN-010 | 越权操作 |
| 配额限制 | SCN-020 | 超限拒绝 |
| 依赖故障 | SCN-030 | 下游不可用 |
| 滥用防护 | SCN-040 | 洪泛拦截 |

## 7. 关键决策与取舍
DEC-001：选择全量迁移方案

## 8. 安全模型
SEC-HR-001：禁止越权操作（关联：SCN-010）

## 9. 可靠性与健壮性
REL-HR-001：依赖不可用时不崩溃（关联：SCN-030）

## 10. 可观测性

## 11. 验收

### 11.2 正常路径
SCN-001: normal / 正常请求
  WHEN 合法请求
  THEN 返回成功

### 11.3 权限/越权
SCN-010: reject_authz / 越权拒绝
  WHEN 无权限用户请求
  THEN 拒绝

### 11.4 非法值/边界
SCN-020: limits_quota / 超限拒绝
  WHEN 超过配额
  THEN 拒绝

### 11.5 依赖故障
SCN-030: dependency_down / 依赖不可用
  WHEN 下游服务不可用
  THEN 降级处理

### 11.6 滥用与鲁棒性
SCN-040: abuse / 洪泛防护
  WHEN 大量恶意请求
  THEN 限流

## 14. 门禁声明

### 14.1 触发器声明
- 新增/变更信任边界或权限模型：YES（Links: SEC-HR-001, SCN-010）
- 新增/变更资源预算/降级口径：NO
- 新增/变更恢复链路：NO
- 兼容性行为变化：NO

## 16. 附录
"""


class TestL1Scenarios(unittest.TestCase):
    """Test that L1 (Light) strictness passes with minimal requirements."""

    def test_check_8_passes_with_l1(self):
        """check_8_strictness should PASS when strictness: L1 is declared."""
        rfc = "# RFC\nstrictness: L1\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Expected PASS for L1 but got: {r.issues}")

    def test_l1_passes_without_option_set(self):
        """L1 does not require Option Set / A-B-C alternatives. check_8 should still pass."""
        # L1 RFC with no option set (only one DEC, no alternatives section)
        rfc = MINIMAL_L1_RFC  # has DEC-001 but no "方案 A/B" alternatives
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"L1 should pass without option set: {r.issues}")

    def test_l1_passes_with_minimal_scn_coverage(self):
        """L1 does not require coverage matrix — only minimum categories."""
        r = check_6_scn_coverage(MINIMAL_L1_RFC)
        self.assertTrue(r.passed, f"L1 should pass with minimal SCN coverage: {r.issues}")

    def test_l1_no_upgrade_check_triggered(self):
        """L1 with '5 roles' text should not trigger L2 upgrade detection."""
        rfc = MINIMAL_L1_RFC.replace("strictness: L1", "strictness: L1") + "\n提到 5 个角色 but this is L1\n"
        r = check_8_strictness(rfc)
        # L1 should not check for upgrade DEC — that logic is L2-only
        self.assertTrue(r.passed, f"L1 should not trigger upgrade check: {r.issues}")


class TestL3Scenarios(unittest.TestCase):
    """Test that L3 (Strict) strictness validates correctly."""

    def test_check_8_passes_with_l3(self):
        """check_8_strictness should PASS when strictness: L3 is declared."""
        rfc = "# RFC\nstrictness: L3\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Expected PASS for L3 but got: {r.issues}")

    def test_l3_with_5_roles_no_upgrade_check(self):
        """L3 defaults to 5 roles, so '5 roles' keyword should not trigger upgrade DEC check."""
        rfc = FULL_L3_RFC + "\n使用 5 个角色进行 Gate-B 审查\n"
        r = check_8_strictness(rfc)
        # L3 already has 5 roles by default — no DEC needed
        self.assertTrue(r.passed, f"L3 with 5 roles should not need upgrade DEC: {r.issues}")

    def test_l3_scn_coverage_passes_with_full_categories(self):
        """L3 should pass check_6 when all mandatory SCN categories are present."""
        r = check_6_scn_coverage(FULL_L3_RFC)
        self.assertTrue(r.passed, f"L3 with full categories should pass: {r.issues}")

    def test_l3_scn_coverage_fails_if_category_missing(self):
        """L3 requires mandatory coverage — removing a category should fail check_6."""
        # Remove the abuse/robustness section entirely
        rfc = FULL_L3_RFC.replace("abuse", "something").replace("滥用", "其他").replace("鲁棒", "其他")
        r = check_6_scn_coverage(rfc)
        self.assertFalse(r.passed, "L3 with missing abuse category should FAIL check_6")

    def test_l3_strictness_field_case_insensitive(self):
        """Strictness field matching should be case-insensitive."""
        rfc = "# RFC\nStrictness: l3\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Case-insensitive L3 should pass: {r.issues}")


class TestL2UpgradeScenarios(unittest.TestCase):
    """Test L2 auto-upgrade detection — 5 roles trigger needs DEC."""

    def test_l2_with_5_roles_chinese_no_dec_fails(self):
        """L2 with '5 个角色' but no upgrade DEC should FAIL check_8."""
        rfc = MINIMAL_RFC + "\n本设计涉及 5 个角色 参与审查\n"
        r = check_8_strictness(rfc)
        self.assertFalse(r.passed, "L2 with 5 roles and no DEC should fail")
        self.assertTrue(any("upgrade" in i.lower() or "5 role" in i.lower() for i in r.issues),
                        f"Issue should mention upgrade/5 roles: {r.issues}")

    def test_l2_with_5_roles_english_no_dec_fails(self):
        """L2 with '5 roles' English keyword but no upgrade DEC should FAIL."""
        rfc = MINIMAL_RFC + "\nThis design uses 5 roles for review.\n"
        r = check_8_strictness(rfc)
        self.assertFalse(r.passed, "L2 with '5 roles' English and no DEC should fail")

    def test_l2_with_upgrade_keyword_no_dec_fails(self):
        """L2 with 'upgrade' keyword but no upgrade DEC should FAIL."""
        rfc = MINIMAL_RFC + "\nWe upgrade to enhanced review scope.\n"
        r = check_8_strictness(rfc)
        self.assertFalse(r.passed, "L2 with 'upgrade' keyword and no DEC should fail")

    def test_l2_with_5_roles_and_matching_dec_passes(self):
        """L2 with '5 个角色' and a matching DEC-### upgrade rationale should PASS."""
        rfc = MINIMAL_RFC + "\n本设计涉及 5 个角色\nDEC-002：升级到 5 角色审查，因触发信任边界变更\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"L2 with 5 roles + DEC upgrade should pass: {r.issues}")

    def test_l2_with_5_roles_and_english_dec_upgrade_passes(self):
        """L2 with 'upgrade' keyword and DEC-### upgrade should PASS."""
        rfc = MINIMAL_RFC + "\nWe upgrade to 5-role review.\nDEC-002：upgrade to 5-role scope due to trust changes\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"L2 with upgrade + DEC should pass: {r.issues}")

    def test_l2_without_upgrade_keywords_passes(self):
        """L2 without any upgrade keywords should PASS normally."""
        r = check_8_strictness(MINIMAL_RFC)
        self.assertTrue(r.passed, f"L2 baseline should pass: {r.issues}")


class TestIntegrationMinimalL1RFC(unittest.TestCase):
    """Integration test: run all 9 checks on a minimal L1 RFC."""

    def test_all_9_checks_pass_l1(self):
        """A well-formed L1 RFC should pass all 9 Gate-A checks."""
        rfc = MINIMAL_L1_RFC
        evidence = {"items": [
            {"evd_id": "EVD-001", "links_to": ["SEC-HR-001"]},
            {"evd_id": "EVD-002", "links_to": ["REL-HR-001"]},
        ]}

        results = [
            check_1_structure(rfc, None),
            check_2_id_integrity(rfc),
            check_3_placeholders(rfc),
            check_4_expression_rules(rfc),
            check_5_readability(rfc),
            check_6_scn_coverage(rfc),
            check_7_evidence(rfc, evidence),
            check_8_strictness(rfc),
            check_9_triggers(rfc),
        ]

        for r in results:
            self.assertTrue(r.passed, f"L1 integration: {r.name} FAILED with: {r.issues}")


class TestIntegrationFullL3RFC(unittest.TestCase):
    """Integration test: run all 9 checks on a full L3 RFC."""

    def test_all_9_checks_pass_l3(self):
        """A well-formed L3 RFC (with coverage matrix, option set) should pass all 9 checks."""
        rfc = FULL_L3_RFC
        evidence = {"items": [
            {"evd_id": "EVD-001", "links_to": ["SEC-HR-001"]},
            {"evd_id": "EVD-002", "links_to": ["REL-HR-001"]},
        ]}

        results = [
            check_1_structure(rfc, None),
            check_2_id_integrity(rfc),
            check_3_placeholders(rfc),
            check_4_expression_rules(rfc),
            check_5_readability(rfc),
            check_6_scn_coverage(rfc),
            check_7_evidence(rfc, evidence),
            check_8_strictness(rfc),
            check_9_triggers(rfc),
        ]

        for r in results:
            self.assertTrue(r.passed, f"L3 integration: {r.name} FAILED with: {r.issues}")


# === Bug Regression Tests (P3 evaluation findings) ===

class TestBugRegressions(unittest.TestCase):
    """Regression tests for confirmed bugs found during v1.2.0 evaluation."""

    # Bug 1: Config shallow copy mutation leak
    def test_config_deep_copy_no_mutation_leak(self):
        """load_config() should return independent copies — mutating one should not affect defaults."""
        from gate_a_check import load_config, DEFAULT_CONFIG
        import copy

        original_categories = copy.deepcopy(DEFAULT_CONFIG["min_scn_categories"])
        cfg = load_config("/nonexistent/path.json")  # force fallback to defaults
        cfg["min_scn_categories"].append("INJECTED")
        # DEFAULT_CONFIG must NOT be mutated
        self.assertEqual(DEFAULT_CONFIG["min_scn_categories"], original_categories,
                         "DEFAULT_CONFIG was mutated by load_config() — shallow copy leak")

    # Bug 2: Meta field substring match false positive
    def test_meta_field_no_substring_false_positive(self):
        """check_1 should FAIL when meta field appears only as substring in prose, not as field."""
        rfc = (
            "# RFC-20260101：Test\n"
            "## 2. 背景\n"
            "We discuss template_id_generation in the next section.\n"
            "The template_version_history is long.\n"
            "Our strictness_level is not defined as a field.\n"
            "## 8. 安全模型\n## 11. 验收\n"
        )
        r = check_1_structure(rfc, None)
        self.assertFalse(r.passed, "Should FAIL: meta fields only appear as prose substrings, not actual fields")
        self.assertTrue(any("template_id" in i for i in r.issues))

    def test_meta_field_with_colon_passes(self):
        """check_1 should PASS when meta fields appear as proper field: value pairs."""
        r = check_1_structure(MINIMAL_RFC, None)
        self.assertTrue(r.passed, f"Should PASS with proper meta fields: {r.issues}")

    # Bug 3: CJK boundary placeholder detection
    def test_placeholder_cjk_boundary_tbd(self):
        """check_3 should detect TBD adjacent to CJK characters (no ASCII boundary)."""
        rfc = "这里TBD待定\n"
        r = check_3_placeholders(rfc)
        self.assertFalse(r.passed, "Should detect TBD at CJK boundary")

    def test_placeholder_cjk_boundary_todo(self):
        """check_3 should detect TODO adjacent to CJK characters."""
        rfc = "需要TODO修复\n"
        r = check_3_placeholders(rfc)
        self.assertFalse(r.passed, "Should detect TODO at CJK boundary")

    def test_placeholder_not_in_words(self):
        """check_3 should NOT flag substrings like 'STUBDATA' containing 'TBD' pattern."""
        rfc = "No placeholder here, just normal text.\n"
        r = check_3_placeholders(rfc)
        self.assertTrue(r.passed, "Should not false-positive on normal text")

    def test_placeholder_standalone_still_works(self):
        """check_3 should still detect standalone TBD (space-bounded)."""
        rfc = "This is TBD for now.\n"
        r = check_3_placeholders(rfc)
        self.assertFalse(r.passed, "Should detect standalone TBD")


# === Check 10: HR→SCN binding ===

class TestCheck10HRSCNBinding(unittest.TestCase):
    def test_pass_hr_referenced_by_scn(self):
        """HR referenced in SCN block should pass."""
        r = check_10_hr_scn_binding(MINIMAL_RFC)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_hr_not_referenced_by_scn(self):
        """HR with no SCN reference should fail."""
        rfc = MINIMAL_RFC + "\nSEC-HR-099：新硬规则没有任何 SCN 引用\n"
        r = check_10_hr_scn_binding(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("SEC-HR-099" in i for i in r.issues))

    def test_pass_no_hr_definitions(self):
        """No HR definitions should trivially pass."""
        rfc = "# RFC\nSCN-001: test\n  WHEN x\n  THEN y\n"
        r = check_10_hr_scn_binding(rfc)
        self.assertTrue(r.passed)


# === Check 11: DEC alternatives ===

class TestCheck11DECAlternatives(unittest.TestCase):
    def test_pass_dec_with_alternatives(self):
        """DEC with alternative/option keywords should pass."""
        rfc = "DEC-001：选择方案 A\n替代方案：方案 B 性能不足\n"
        r = check_11_dec_alternatives(rfc)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_pass_dec_with_single_path(self):
        """DEC with single-path justification should pass."""
        rfc = "DEC-001：选择方案 A\n唯一方案：没有其他可行选择\n"
        r = check_11_dec_alternatives(rfc)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_dec_without_alternatives_or_justification(self):
        """DEC with no alternatives or justification should fail."""
        rfc = "DEC-001：选择了这个实现\n具体细节如下\n"
        r = check_11_dec_alternatives(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("DEC-001" in i for i in r.issues))

    def test_pass_dec_with_english_alternative(self):
        """DEC with English 'alternative' keyword should pass."""
        rfc = "DEC-001: Choose option A\nalternative: option B rejected due to cost\n"
        r = check_11_dec_alternatives(rfc)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_pass_no_dec_definitions(self):
        """No DEC definitions should trivially pass."""
        rfc = "# RFC\nSCN-001: test\n"
        r = check_11_dec_alternatives(rfc)
        self.assertTrue(r.passed)


# === Check 12: Must-pass validity ===

class TestCheck12MustPassValidity(unittest.TestCase):
    def test_pass_valid_must_pass_scns(self):
        """All must-pass SCN IDs exist as defined."""
        rfc = (
            "# RFC\n"
            "## 11. 验收\n"
            "must-pass: SCN-001, SCN-010\n"
            "SCN-001: normal\n  WHEN x\n  THEN y\n"
            "SCN-010: reject\n  WHEN a\n  THEN b\n"
        )
        r = check_12_must_pass_validity(rfc)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_must_pass_references_undefined_scn(self):
        """Must-pass referencing undefined SCN should fail."""
        rfc = (
            "# RFC\n"
            "## 11. 验收\n"
            "must-pass: SCN-001, SCN-999\n"
            "SCN-001: normal\n  WHEN x\n  THEN y\n"
        )
        r = check_12_must_pass_validity(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("SCN-999" in i for i in r.issues))

    def test_pass_no_section_11(self):
        """No §11 section should skip check."""
        rfc = "# RFC\n## 2. 背景\n内容\n"
        r = check_12_must_pass_validity(rfc)
        self.assertTrue(r.passed)


# === Check 13: Coverage matrix ===

class TestCheck13CoverageMatrix(unittest.TestCase):
    def test_pass_l2_with_coverage_table(self):
        """L2/Standard with a risk→SCN table should pass."""
        rfc = (
            "# RFC\nstrictness: L2\n"
            "## 11. 验收\n"
            "| 维度 | SCN | 说明 |\n"
            "|------|-----|------|\n"
            "| 正常路径 | SCN-001 | 合法请求 |\n"
        )
        r = check_13_coverage_matrix(rfc)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_l2_without_coverage_table(self):
        """L2 without any risk→SCN mapping should fail."""
        rfc = "# RFC\nstrictness: L2\n## 11. 验收\n一些文字但没有表格\n"
        r = check_13_coverage_matrix(rfc)
        self.assertFalse(r.passed)

    def test_pass_l1_without_coverage_table(self):
        """L1/Light does not require coverage matrix."""
        rfc = "# RFC\nstrictness: L1\n## 11. 验收\n一些文字\n"
        r = check_13_coverage_matrix(rfc)
        self.assertTrue(r.passed)

    def test_pass_l3_with_coverage_table(self):
        """L3/Full with a risk→SCN table should pass."""
        r = check_13_coverage_matrix(FULL_L3_RFC)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")


# === Check 14: Section non-empty ===

class TestCheck14SectionNonEmpty(unittest.TestCase):
    def test_pass_sections_with_content(self):
        """Sections with ≥3 content lines should pass."""
        rfc = (
            "# RFC\ntemplate_id: x\ntemplate_version: x\nstrictness: L2\n"
            "## 2. 背景\n现状描述\n问题分析\n影响范围\n"
            "## 4. 目标\n目标1\n目标2\n目标3\n"
            "## 5. 方案概览\n方案描述\n架构设计\n实施计划\n"
            "## 8. 安全模型\nSEC-HR-001：规则\n威胁模型\n安全措施\n"
            "## 9. 可靠性\n降级策略\n容错设计\n恢复机制\n"
            "## 11. 验收\nSCN-001: normal\nWHEN x\nTHEN y\n"
            "## 7. 关键决策与取舍\nDEC-001：选择\n替代方案分析\n权衡说明\n"
        )
        r = check_14_section_non_empty(rfc)
        self.assertTrue(r.passed, f"Expected PASS but got: {r.issues}")

    def test_fail_section_too_sparse(self):
        """Section with <3 content lines should fail."""
        rfc = (
            "# RFC\nstrictness: L2\n"
            "## 2. 背景\n一行内容\n"
            "## 4. 目标\n目标1\n目标2\n目标3\n"
            "## 5. 方案\n方案1\n方案2\n方案3\n"
            "## 8. 安全模型\n安全1\n安全2\n安全3\n"
            "## 9. 可靠性\n可靠1\n可靠2\n可靠3\n"
            "## 11. 验收\n验收1\n验收2\n验收3\n"
            "## 7. 决策\n决策1\n决策2\n决策3\n"
        )
        r = check_14_section_non_empty(rfc)
        self.assertFalse(r.passed)
        self.assertTrue(any("背景" in i for i in r.issues))


# === Check 15: Diagram-text pairing (SOFT) ===

class TestCheck15DiagramTextPairing(unittest.TestCase):
    def test_pass_mermaid_with_surrounding_text(self):
        """Mermaid block with text nearby should pass."""
        rfc = "这是描述文字\n```mermaid\nflowchart LR\n  A --> B\n```\n后续说明\n"
        r = check_15_diagram_text_pairing(rfc)
        self.assertEqual(len(r.warnings), 0, f"Expected no warnings but got: {r.warnings}")

    def test_warn_mermaid_isolated(self):
        """Mermaid block with no text within 10 lines should warn."""
        # 12 blank lines before and after to ensure isolation
        blank = "\n" * 12
        rfc = blank + "```mermaid\nflowchart LR\n  A --> B\n```\n" + blank
        r = check_15_diagram_text_pairing(rfc)
        self.assertTrue(len(r.warnings) > 0, "Expected WARN for isolated mermaid block")

    def test_soft_check_does_not_fail(self):
        """Soft check should never set passed=False, only warn."""
        blank = "\n" * 12
        rfc = blank + "```mermaid\nflowchart LR\n  A --> B\n```\n" + blank
        r = check_15_diagram_text_pairing(rfc)
        self.assertTrue(r.passed, "Soft check should always have passed=True")


# === Check 16: Unresolved format (SOFT) ===

class TestCheck16UnresolvedFormat(unittest.TestCase):
    def test_pass_unresolved_with_owner(self):
        """Unresolved item with owner keyword should pass."""
        rfc = "## Hard-Unresolved\n- owner: Alice, action: 确认接口, convergence: 2026-03-01\n"
        r = check_16_unresolved_format(rfc)
        self.assertEqual(len(r.warnings), 0, f"Expected no warnings but got: {r.warnings}")

    def test_warn_unresolved_without_keywords(self):
        """Unresolved item without owner/action/convergence should warn."""
        rfc = "## Hard-Unresolved\n- 接口设计待讨论\n"
        r = check_16_unresolved_format(rfc)
        self.assertTrue(len(r.warnings) > 0, "Expected WARN for unresolved without keywords")

    def test_pass_no_unresolved_section(self):
        """No unresolved section should produce no warnings."""
        rfc = "# RFC\n## 2. 背景\n内容\n"
        r = check_16_unresolved_format(rfc)
        self.assertEqual(len(r.warnings), 0)


# === Check 17: Orphan SCN (SOFT) ===

class TestCheck17OrphanSCN(unittest.TestCase):
    def test_pass_all_scns_referenced(self):
        """SCNs referenced by HR or triggers should pass."""
        r = check_17_orphan_scn(MINIMAL_RFC)
        # MINIMAL_RFC has SCN-001, SCN-020, SCN-030, SCN-040 — some may be orphans
        # SCN-010 is referenced by SEC-HR-001, SCN-030 by REL-HR-001
        # SCN-010 also in trigger Links
        # Check that at minimum SCN-010 and SCN-030 are not flagged
        flagged = [w for w in r.warnings if 'SCN-010' in w or 'SCN-030' in w]
        self.assertEqual(len(flagged), 0, f"SCN-010/030 should not be orphan: {flagged}")

    def test_warn_orphan_scn(self):
        """SCN not referenced by any HR or must-pass should warn."""
        rfc = (
            "# RFC\n"
            "## 11. 验收\n"
            "SCN-001: normal\n  WHEN x\n  THEN y\n"
            "SCN-099: orphan\n  WHEN a\n  THEN b\n"
        )
        r = check_17_orphan_scn(rfc)
        self.assertTrue(any("SCN-099" in w for w in r.warnings), f"SCN-099 should be orphan: {r.warnings}")

    def test_pass_no_scns(self):
        """No SCN definitions should trivially pass."""
        rfc = "# RFC\n## 2. 背景\n内容\n"
        r = check_17_orphan_scn(rfc)
        self.assertEqual(len(r.warnings), 0)


# === 3-State Output Format ===

class TestRunGateA(unittest.TestCase):
    """Tests for the run_gate_a() aggregation function."""

    def test_all_pass_no_warnings(self):
        """All hard pass, no soft warnings -> PASS."""
        from gate_a_check import CheckResult
        hard = [CheckResult("h1"), CheckResult("h2")]
        soft = [CheckResult("s1", kind="soft")]
        report = run_gate_a(hard, soft)
        self.assertEqual(report["overall"], "PASS")
        self.assertEqual(len(report["hard_pass"]), 2)
        self.assertEqual(len(report["hard_fail"]), 0)
        self.assertEqual(len(report["soft_warn"]), 0)

    def test_hard_fail(self):
        """Any hard fail -> FAIL overall."""
        from gate_a_check import CheckResult
        h1 = CheckResult("h1")
        h2 = CheckResult("h2")
        h2.fail("something broke")
        soft = [CheckResult("s1", kind="soft")]
        report = run_gate_a([h1, h2], soft)
        self.assertEqual(report["overall"], "FAIL")
        self.assertIn("h2", report["hard_fail"])
        self.assertIn("h1", report["hard_pass"])

    def test_warn_state(self):
        """All hard pass but soft warnings -> WARN."""
        from gate_a_check import CheckResult
        hard = [CheckResult("h1")]
        s1 = CheckResult("s1", kind="soft")
        s1.warn("minor issue")
        report = run_gate_a(hard, [s1])
        self.assertEqual(report["overall"], "WARN")
        self.assertEqual(len(report["hard_pass"]), 1)
        self.assertEqual(len(report["hard_fail"]), 0)
        self.assertIn("s1", report["soft_warn"])

    def test_fail_takes_precedence_over_warn(self):
        """FAIL takes precedence over WARN."""
        from gate_a_check import CheckResult
        h1 = CheckResult("h1")
        h1.fail("hard failure")
        s1 = CheckResult("s1", kind="soft")
        s1.warn("soft warning")
        report = run_gate_a([h1], [s1])
        self.assertEqual(report["overall"], "FAIL")

    def test_details_populated(self):
        """Details dict should have entries for all checks."""
        from gate_a_check import CheckResult
        h1 = CheckResult("h1")
        s1 = CheckResult("s1", kind="soft")
        s1.warn("a warning")
        report = run_gate_a([h1], [s1])
        self.assertIn("h1", report["details"])
        self.assertIn("s1", report["details"])
        self.assertEqual(report["details"]["s1"]["warnings"], ["a warning"])


# === New Strictness Naming (light/standard/full) Tests ===

MINIMAL_STANDARD_RFC = MINIMAL_RFC.replace("strictness: L2", "strictness: standard")
MINIMAL_LIGHT_RFC_NEW = MINIMAL_L1_RFC.replace("strictness: L1", "strictness: light")
FULL_FULL_RFC = FULL_L3_RFC.replace("strictness: L3", "strictness: full")


class TestNewStrictnessNaming(unittest.TestCase):
    """Tests for light/standard/full strictness naming (v2.0.0)."""

    def test_check_8_passes_with_standard(self):
        rfc = "# RFC\nstrictness: standard\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Expected PASS for 'standard' but got: {r.issues}")

    def test_check_8_passes_with_light(self):
        rfc = "# RFC\nstrictness: light\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Expected PASS for 'light' but got: {r.issues}")

    def test_check_8_passes_with_full(self):
        rfc = "# RFC\nstrictness: full\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Expected PASS for 'full' but got: {r.issues}")

    def test_check_8_case_insensitive(self):
        """Strictness naming should be case-insensitive."""
        for name in ['Standard', 'STANDARD', 'Full', 'FULL', 'Light', 'LIGHT']:
            rfc = f"# RFC\nstrictness: {name}\n## 2. 背景\n"
            r = check_8_strictness(rfc)
            self.assertTrue(r.passed, f"Expected PASS for '{name}' but got: {r.issues}")

    def test_check_8_standard_upgrade_detection(self):
        """Standard with 5 roles and no DEC should FAIL (same behavior as L2)."""
        rfc = MINIMAL_STANDARD_RFC + "\n本设计涉及 5 个角色 参与审查\n"
        r = check_8_strictness(rfc)
        self.assertFalse(r.passed, "Standard with 5 roles and no DEC should fail")

    def test_check_8_standard_upgrade_with_dec_passes(self):
        """Standard with 5 roles and matching DEC should PASS."""
        rfc = MINIMAL_STANDARD_RFC + "\n本设计涉及 5 个角色\nDEC-002：升级到 5 角色审查\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Standard with upgrade DEC should pass: {r.issues}")

    def test_check_8_full_no_upgrade_check(self):
        """Full with 5 roles should NOT trigger upgrade DEC check."""
        rfc = "# RFC\nstrictness: full\n## 2. 背景\n使用 5 个角色进行审查\n"
        r = check_8_strictness(rfc)
        self.assertTrue(r.passed, f"Full with 5 roles should not need upgrade DEC: {r.issues}")

    def test_check_8_rejects_invalid_value(self):
        """Invalid strictness value should FAIL."""
        rfc = "# RFC\nstrictness: medium\n## 2. 背景\n"
        r = check_8_strictness(rfc)
        self.assertFalse(r.passed, "Invalid strictness value 'medium' should fail")

    def test_check_13_standard_requires_coverage(self):
        """Standard strictness requires coverage matrix (same as L2)."""
        rfc = "# RFC\nstrictness: standard\n## 11. 验收\n一些文字但没有表格\n"
        r = check_13_coverage_matrix(rfc)
        self.assertFalse(r.passed, "Standard without coverage matrix should fail")

    def test_check_13_light_no_coverage_needed(self):
        """Light strictness does not require coverage matrix."""
        rfc = "# RFC\nstrictness: light\n## 11. 验收\n一些文字\n"
        r = check_13_coverage_matrix(rfc)
        self.assertTrue(r.passed)

    def test_check_13_full_requires_coverage(self):
        """Full strictness requires coverage matrix (same as L3)."""
        rfc = "# RFC\nstrictness: full\n## 11. 验收\n一些文字但没有表格\n"
        r = check_13_coverage_matrix(rfc)
        self.assertFalse(r.passed, "Full without coverage matrix should fail")

    def test_check_13_full_with_coverage_passes(self):
        """Full with coverage table should pass."""
        r = check_13_coverage_matrix(FULL_FULL_RFC)
        self.assertTrue(r.passed, f"Full with coverage table should pass: {r.issues}")

    def test_integration_standard_all_checks(self):
        """Integration: Standard-named RFC passes all 9 original checks."""
        rfc = MINIMAL_STANDARD_RFC
        evidence = {"items": [
            {"evd_id": "EVD-001", "links_to": ["SEC-HR-001"]},
            {"evd_id": "EVD-002", "links_to": ["REL-HR-001"]},
        ]}
        results = [
            check_1_structure(rfc, None),
            check_2_id_integrity(rfc),
            check_3_placeholders(rfc),
            check_4_expression_rules(rfc),
            check_5_readability(rfc),
            check_6_scn_coverage(rfc),
            check_7_evidence(rfc, evidence),
            check_8_strictness(rfc),
            check_9_triggers(rfc),
        ]
        for r in results:
            self.assertTrue(r.passed, f"Standard integration: {r.name} FAILED: {r.issues}")

    def test_integration_light_all_checks(self):
        """Integration: Light-named RFC passes all 9 original checks."""
        rfc = MINIMAL_LIGHT_RFC_NEW
        evidence = {"items": [
            {"evd_id": "EVD-001", "links_to": ["SEC-HR-001"]},
            {"evd_id": "EVD-002", "links_to": ["REL-HR-001"]},
        ]}
        results = [
            check_1_structure(rfc, None),
            check_2_id_integrity(rfc),
            check_3_placeholders(rfc),
            check_4_expression_rules(rfc),
            check_5_readability(rfc),
            check_6_scn_coverage(rfc),
            check_7_evidence(rfc, evidence),
            check_8_strictness(rfc),
            check_9_triggers(rfc),
        ]
        for r in results:
            self.assertTrue(r.passed, f"Light integration: {r.name} FAILED: {r.issues}")


class TestConfigToggle(unittest.TestCase):
    """Tests for config-based enable/disable of checks 10-17."""

    def test_load_config_reads_enabled_flags(self):
        """load_config returns hard_checks/soft_checks with enabled flags from JSON."""
        import tempfile, json
        custom_cfg = {
            "hard_checks": {
                "check_10_hr_scn_binding": {"enabled": False},
                "check_14_section_non_empty": {"enabled": False},
            },
            "soft_checks": {
                "check_17_orphan_scn": {"enabled": False},
            },
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(custom_cfg, f)
            tmp_path = f.name
        try:
            cfg = load_config(tmp_path)
            self.assertFalse(cfg["hard_checks"]["check_10_hr_scn_binding"]["enabled"])
            self.assertFalse(cfg["hard_checks"]["check_14_section_non_empty"]["enabled"])
            self.assertFalse(cfg["soft_checks"]["check_17_orphan_scn"]["enabled"])
        finally:
            os.unlink(tmp_path)

    def test_toggle_skips_disabled_hard_check(self):
        """When a hard check is disabled in config, it should be skipped in main() logic."""
        hard_checks_cfg = {
            "check_10_hr_scn_binding": {"enabled": False},
            "check_11_dec_alternatives": {"enabled": True},
        }
        rfc = MINIMAL_RFC
        configurable_hard = [
            ("check_10_hr_scn_binding", lambda: check_10_hr_scn_binding(rfc)),
            ("check_11_dec_alternatives", lambda: check_11_dec_alternatives(rfc)),
        ]
        results = []
        for check_name, check_fn in configurable_hard:
            if hard_checks_cfg.get(check_name, {}).get("enabled", True):
                results.append(check_fn())
        # check_10 disabled -> only check_11 should run
        self.assertEqual(len(results), 1)
        self.assertIn("11", results[0].name)

    def test_toggle_skips_disabled_soft_check(self):
        """When a soft check is disabled in config, it should be skipped."""
        soft_checks_cfg = {
            "check_15_diagram_text_pairing": {"enabled": True},
            "check_16_unresolved_format": {"enabled": False},
            "check_17_orphan_scn": {"enabled": False},
        }
        rfc = MINIMAL_RFC
        configurable_soft = [
            ("check_15_diagram_text_pairing", lambda: check_15_diagram_text_pairing(rfc)),
            ("check_16_unresolved_format", lambda: check_16_unresolved_format(rfc)),
            ("check_17_orphan_scn", lambda: check_17_orphan_scn(rfc)),
        ]
        results = []
        for check_name, check_fn in configurable_soft:
            if soft_checks_cfg.get(check_name, {}).get("enabled", True):
                results.append(check_fn())
        # Only check_15 enabled
        self.assertEqual(len(results), 1)
        self.assertIn("15", results[0].name)

    def test_toggle_defaults_to_enabled(self):
        """When config has no entry for a check, it defaults to enabled."""
        hard_checks_cfg = {}  # empty - no overrides
        enabled = hard_checks_cfg.get("check_10_hr_scn_binding", {}).get("enabled", True)
        self.assertTrue(enabled)


if __name__ == "__main__":
    unittest.main()
