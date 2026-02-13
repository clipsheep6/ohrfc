#!/usr/bin/env python3
"""OHRFC INIT phase automation.

Creates workspace, rfc.md skeleton, evidence.json, and state.json.

Usage:
    python3 ohrfc_init.py <rfc_id> <rfc_title> [--strictness standard] [--skill-dir <path>]

Examples:
    python3 scripts/ohrfc_init.py rfc-20260211-auth-model "认证模型重构"
    python3 scripts/ohrfc_init.py rfc-20260211-auth-model "认证模型重构" --strictness full
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


TEMPLATE_ID = "rfc_template_os_service"
TEMPLATE_VERSION = "2026-02-09"

STRICTNESS_GATE_B_MAX = {
    "light": 0,
    "standard": 2,
    "full": 3,
}

STRICTNESS_REVIEWER_COUNT = {
    "light": 0,
    "standard": 3,
    "full": 4,
}

# Template content starts after this marker line (line 25: "---")
TEMPLATE_SKELETON_MARKER = "# RFC-YYYYMMDD"


def find_skill_dir(hint: str | None = None) -> Path:
    """Locate the skill root directory containing references/rfc_template.md."""
    if hint:
        p = Path(hint)
        if (p / "references" / "rfc_template.md").exists():
            return p
        raise FileNotFoundError(f"Skill dir not found at {hint}")

    # Try relative to this script
    script_dir = Path(__file__).resolve().parent
    candidate = script_dir.parent  # scripts/ -> ohrfc/
    if (candidate / "references" / "rfc_template.md").exists():
        return candidate

    raise FileNotFoundError(
        "Cannot locate skill directory. Use --skill-dir to specify."
    )


def load_template_skeleton(skill_dir: Path) -> str:
    """Read rfc_template.md and extract the skeleton portion (from '# RFC-YYYYMMDD...')."""
    template_path = skill_dir / "references" / "rfc_template.md"
    content = template_path.read_text(encoding="utf-8")

    # Find the skeleton start marker
    lines = content.splitlines(keepends=True)
    start_idx = None
    for i, line in enumerate(lines):
        if line.startswith(TEMPLATE_SKELETON_MARKER):
            start_idx = i
            break

    if start_idx is None:
        raise ValueError(
            f"Cannot find '{TEMPLATE_SKELETON_MARKER}' in rfc_template.md"
        )

    return "".join(lines[start_idx:])


def generate_rfc_skeleton(
    skeleton: str, title: str, strictness: str, spec_date: str
) -> str:
    """Generate rfc.md content: YAML meta + template skeleton with title substituted."""
    meta = (
        f"---\n"
        f"template_id: {TEMPLATE_ID}\n"
        f"template_version: {TEMPLATE_VERSION}\n"
        f"strictness: {strictness}\n"
        f"---\n\n"
    )

    # Replace placeholder title
    skeleton = re.sub(
        r"# RFC-YYYYMMDD：<标题>",
        f"# RFC-{spec_date}：{title}",
        skeleton,
        count=1,
    )

    return meta + skeleton


def generate_evidence() -> dict:
    """Generate initial evidence.json content."""
    return {"schema_version": "v1", "items": []}


def generate_state(rfc_id: str, strictness: str) -> dict:
    """Generate initial state.json content per state.schema.json."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "v2",
        "rfc_id": rfc_id,
        "current_phase": "discover",
        "strictness": strictness,
        "template_id": TEMPLATE_ID,
        "template_version": TEMPLATE_VERSION,
        "created_at": now,
        "updated_at": now,
        "gate_a_result": None,
        "gate_b_round": 0,
        "gate_b_max_rounds": STRICTNESS_GATE_B_MAX[strictness],
        "gate_b_result": None,
        "reviewer_count": STRICTNESS_REVIEWER_COUNT[strictness],
        "upgrade_triggers": [],
        "baseline_accepted": False,
        "checkpoint_version": 0,
        "last_checkpoint_phase": None,
        "sub_step_progress": None,
        "detour_count": 0,
        "rejection_count": 0,
        "gate_b_mode": None,
        "reviewer_dispatch": {},
        "web_search_enabled": False,
    }


def validate_state_against_schema(state: dict, skill_dir: Path) -> list[str]:
    """Best-effort validation of state against state.schema.json."""
    schema_path = skill_dir / "assets" / "schemas" / "state.schema.json"
    if not schema_path.exists():
        return []

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = []

    # Check required fields
    for field in schema.get("required", []):
        if field not in state:
            errors.append(f"Missing required field: {field}")

    # Check schema_version const
    props = schema.get("properties", {})
    sv = props.get("schema_version", {})
    if "const" in sv and state.get("schema_version") != sv["const"]:
        errors.append(
            f"schema_version must be '{sv['const']}', got '{state.get('schema_version')}'"
        )

    # Check strictness enum
    sp = props.get("strictness", {})
    if "enum" in sp and state.get("strictness") not in sp["enum"]:
        errors.append(
            f"strictness '{state.get('strictness')}' not in {sp['enum']}"
        )

    # Check current_phase enum
    cp = props.get("current_phase", {})
    if "enum" in cp and state.get("current_phase") not in cp["enum"]:
        errors.append(
            f"current_phase '{state.get('current_phase')}' not in {cp['enum']}"
        )

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="OHRFC INIT phase: create workspace and skeleton files"
    )
    parser.add_argument("rfc_id", help="RFC identifier (e.g. rfc-20260211-auth-model)")
    parser.add_argument("rfc_title", help="RFC title (Chinese or English)")
    parser.add_argument(
        "--strictness",
        choices=["light", "standard", "full"],
        default="standard",
        help="Strictness level (default: standard)",
    )
    parser.add_argument(
        "--skill-dir",
        default=None,
        help="Path to skill root directory (auto-detected if omitted)",
    )
    args = parser.parse_args()

    # Resolve paths
    skill_dir = find_skill_dir(args.skill_dir)
    workspace = Path(f".ohrfc/{args.rfc_id}")

    if workspace.exists():
        print(f"ERROR: Workspace already exists: {workspace}", file=sys.stderr)
        sys.exit(1)

    # Extract date from rfc_id if possible, else use today
    date_match = re.search(r"(\d{8})", args.rfc_id)
    spec_date = date_match.group(1) if date_match else datetime.now().strftime("%Y%m%d")

    # Load template
    skeleton = load_template_skeleton(skill_dir)

    # Generate files
    rfc_content = generate_rfc_skeleton(skeleton, args.rfc_title, args.strictness, spec_date)
    evidence = generate_evidence()
    state = generate_state(args.rfc_id, args.strictness)

    # Validate state against schema
    errors = validate_state_against_schema(state, skill_dir)
    if errors:
        print("WARNING: State validation issues:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)

    # Create workspace
    (workspace / ".debug").mkdir(parents=True, exist_ok=True)
    (workspace / ".reviews").mkdir(parents=True, exist_ok=True)

    # Write files
    (workspace / "rfc.md").write_text(rfc_content, encoding="utf-8")
    (workspace / "evidence.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (workspace / "state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # Report
    print(f"INIT complete: {workspace}/")
    print(f"  strictness: {args.strictness}")
    print(f"  rfc.md: skeleton with {len(rfc_content.splitlines())} lines")
    print(f"  evidence.json: initialized (0 items)")
    print(f"  state.json: current_phase=discover")
    print(f"  Ready for DISCOVER phase")


if __name__ == "__main__":
    main()
