#!/usr/bin/env python3
"""Set up a project for bookie: project files, .gitignore, the setup-pstack override, a commit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "bookie" / "scripts"))

from persist import commit
from scaffold import STACKS, SURFACES, check, scaffold, setup_questions

SETTINGS = Path(".claude") / "settings.json"
OVERRIDDEN = "setup-pstack"
BRANCH = "setup/bookie"
MESSAGE = "chore: set up pstack models and bookie project files"


def turn_off_setup_pstack(root: Path) -> str:
    """Add "setup-pstack": "off" to the project's skillOverrides. Keep every other key."""
    path = root / SETTINGS
    try:
        settings = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except json.JSONDecodeError as error:
        raise SystemExit(f"{path} is not valid JSON ({error}); fix it first") from error
    if not isinstance(settings, dict):
        raise SystemExit(f"{path} does not hold a JSON object; fix it first")
    overrides = settings.setdefault("skillOverrides", {})
    if overrides.get(OVERRIDDEN) == "off":
        return "kept"
    overrides[OVERRIDDEN] = "off"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    return "turned off setup-pstack"


def project(root: Path, record: Path, stack: str, surface: str) -> dict[str, str]:
    actions = dict(scaffold(root, record, stack, surface))
    actions[str(SETTINGS)] = turn_off_setup_pstack(root)
    return actions


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("questions", "project", "check", "commit"))
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--record", type=Path, default=Path("docs/bet-process.md"))
    parser.add_argument("--stack", choices=sorted(STACKS))
    parser.add_argument("--surface", choices=sorted(SURFACES))
    args = parser.parse_args(argv)
    record = args.record if args.record.is_absolute() else args.root / args.record
    if args.command == "questions":
        print(json.dumps([{"questions": setup_questions()}], indent=1))
    elif args.command == "project":
        if not (args.stack and args.surface):
            parser.error("project needs --stack and --surface")
        print(json.dumps(project(args.root, record, args.stack, args.surface), indent=1))
    elif args.command == "check":
        problem = check(args.root, record)
        print(problem or "ok")
        return 1 if problem else 0
    else:
        problem = check(args.root, record)
        if problem:
            raise SystemExit(f"not committed: {problem}")
        sha, left_out = commit(args.root, BRANCH, MESSAGE)
        print(json.dumps({"commit": sha, "left_out": left_out}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
