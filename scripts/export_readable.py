#!/usr/bin/env python3
"""
Export a human-readable digest from rfc.md.

Extracts background + design-critical sections, strips mechanical gate/appendix
content, and optionally inlines Mermaid diagrams as-is for rendering.

Usage:
    python3 export_readable.py <rfc.md> [-o output.md] [--no-diagrams] [--include-normative]

Output: A concise document suitable for stakeholder review, covering:
  - §1 背景, §2 用户痛点, §3 目标与非目标, §4 一页结论
  - §5 关键决策与取舍
  - §6 方案概览 (with diagrams)
  - §7 影响分析与兼容性
  Optionally (--include-normative):
  - §8 安全模型, §9 可靠性, §10 可观测性, §11 验收 (summary only)

Strips: §12-§15 (change log, gate declarations, release meta, appendix/self-check)
"""

import argparse
import re
import sys
from pathlib import Path

# Sections to always include (review layer + decisions)
CORE_SECTIONS = {"1", "2", "3", "4", "7", "5", "6"}

# Normative sections (opt-in)
NORMATIVE_SECTIONS = {"8", "9", "10", "11"}

# Sections to always exclude
EXCLUDED_SECTIONS = {"12", "13", "14", "15", "16"}

# Regex: match ## N. or ## N  (top-level section headers)
SECTION_RE = re.compile(r"^##\s+(\d+)\.\s")

# ID noise patterns to clean up for readability
ID_HEAVY_RE = re.compile(r"\((?:EVD|REQ)-\d{3}(?:,\s*(?:EVD|REQ)-\d{3})*\)")


def parse_sections(text: str) -> list[tuple[str, str, str]]:
    """Parse rfc.md into (section_number, header_line, body) tuples."""
    lines = text.split("\n")
    sections: list[tuple[str, str, str]] = []
    current_num = None
    current_header = ""
    current_lines: list[str] = []
    preamble_lines: list[str] = []

    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            if current_num is not None:
                sections.append((current_num, current_header, "\n".join(current_lines)))
            elif preamble_lines:
                # Title block before first section
                sections.append(("0", "", "\n".join(preamble_lines)))
            current_num = m.group(1)
            current_header = line
            current_lines = []
        else:
            if current_num is not None:
                current_lines.append(line)
            else:
                preamble_lines.append(line)

    # Last section
    if current_num is not None:
        sections.append((current_num, current_header, "\n".join(current_lines)))

    return sections
# PLACEHOLDER_EXPORT_READABLE


def strip_diagrams(body: str) -> str:
    """Remove mermaid code blocks."""
    return re.sub(r"```mermaid\n.*?```", "[图表已省略]", body, flags=re.DOTALL)


def lighten_ids(body: str) -> str:
    """Remove dense EVD/REQ inline references for readability."""
    return ID_HEAVY_RE.sub("", body)


def summarize_acceptance(body: str) -> str:
    """For §11, extract must-pass items, category counts, and risk coverage matrix."""
    lines = body.split("\n")
    summary_lines = []
    in_must_pass = False
    in_matrix = False

    for line in lines:
        # Capture risk coverage matrix
        if "风险覆盖矩阵" in line or "coverage matrix" in line.lower():
            in_matrix = True
            in_must_pass = False
            summary_lines.append(line)
            continue
        if in_matrix:
            if line.strip().startswith("|") or line.strip() == "":
                summary_lines.append(line)
                continue
            else:
                in_matrix = False

        # Capture must-pass and risk summary sections
        if "必须通过" in line or "must-pass" in line.lower() or "风险覆盖摘要" in line:
            in_must_pass = True
            summary_lines.append(line)
            continue
        if in_must_pass:
            if line.strip().startswith(("-", "*", "SCN", "|")):
                summary_lines.append(line)
            elif line.strip() == "":
                summary_lines.append(line)
            else:
                in_must_pass = False

    # Count SCN categories
    categories = set()
    for line in lines:
        m = re.match(r"###\s+\d+\.(\d+)", line)
        if m:
            categories.add(m.group(1))

    if categories:
        summary_lines.insert(0, f"> 验收场景覆盖 {len(categories)} 个类别\n")

    return "\n".join(summary_lines) if summary_lines else "> 详见完整 RFC §11"


def export_readable(
    rfc_text: str,
    include_normative: bool = False,
    keep_diagrams: bool = True,
) -> str:
    """Generate human-readable digest from rfc.md content."""
    sections = parse_sections(rfc_text)
    output_parts: list[str] = []

    # Extract title from preamble
    for num, header, body in sections:
        if num == "0":
            # Keep only the RFC title line
            for line in body.split("\n"):
                if line.startswith("# RFC"):
                    output_parts.append(line)
                    output_parts.append("")
                    break
            break

    output_parts.append("> 本文档为 RFC 精华摘要，供评审快速了解背景与设计。完整规范请参阅原始 rfc.md。\n")

    allowed = CORE_SECTIONS.copy()
    if include_normative:
        allowed |= NORMATIVE_SECTIONS

    # Output in reading order: 1, 2, 3, 4, 7, 5, 6, [8, 9, 10, 11]
    reading_order = ["1", "2", "3", "4", "7", "5", "6"]
    if include_normative:
        reading_order += ["8", "9", "10", "11"]

    section_map = {num: (header, body) for num, header, body in sections}

    for sec_num in reading_order:
        if sec_num not in section_map:
            continue
        header, body = section_map[sec_num]

        # Process body
        body = lighten_ids(body)

        if not keep_diagrams:
            body = strip_diagrams(body)

        # Special handling for §11: summary only
        if sec_num == "11" and include_normative:
            body = summarize_acceptance(body)

        # Clean up excessive blank lines
        body = re.sub(r"\n{3,}", "\n\n", body).strip()

        output_parts.append(header)
        output_parts.append(body)
        output_parts.append("")  # separator

    return "\n".join(output_parts).strip() + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Export human-readable digest from rfc.md"
    )
    parser.add_argument("rfc_path", help="Path to rfc.md")
    parser.add_argument("-o", "--output", help="Output file path (default: stdout)")
    parser.add_argument(
        "--no-diagrams", action="store_true", help="Strip Mermaid diagrams"
    )
    parser.add_argument(
        "--include-normative",
        action="store_true",
        help="Include §8-§11 (security, reliability, observability, acceptance summary)",
    )
    args = parser.parse_args()

    rfc_path = Path(args.rfc_path)
    if not rfc_path.exists():
        print(f"Error: {rfc_path} not found", file=sys.stderr)
        sys.exit(1)

    rfc_text = rfc_path.read_text(encoding="utf-8")
    result = export_readable(
        rfc_text,
        include_normative=args.include_normative,
        keep_diagrams=not args.no_diagrams,
    )

    if args.output:
        out_path = Path(args.output)
        out_path.write_text(result, encoding="utf-8")
        print(f"Written to {out_path}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
