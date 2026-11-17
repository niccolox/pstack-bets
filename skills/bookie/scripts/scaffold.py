"""Write the project files that a bet needs: AGENTS.md, CLAUDE.md, PRODUCTS.md, DESIGN.md."""

from __future__ import annotations

import os
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parents[1] / "references" / "templates"
FILES = ("AGENTS.md", "CLAUDE.md", "PRODUCTS.md", "DESIGN.md")
TODO = "{{TODO"
ALIASES = {"PRODUCTS.md": "PRODUCT.md"}

STACKS: dict[str, str] = {
    "Python": (
        "| Task | Command |\n| --- | --- |\n"
        "| Install | `uv sync` |\n| Test | `uv run pytest` |\n"
        "| Lint | `uv run ruff check .` |\n| Types | `uv run pyright` |\n"
        "| Run | {{TODO: the command that starts the app}} |"
    ),
    "TypeScript": (
        "| Task | Command |\n| --- | --- |\n"
        "| Install | `pnpm install` |\n| Test | `pnpm test` |\n"
        "| Lint | `pnpm lint` |\n| Types | `pnpm exec tsc --noEmit` |\n"
        "| Run | {{TODO: the command that starts the app}} |"
    ),
    "Other": (
        "| Task | Command |\n| --- | --- |\n"
        "| Install | {{TODO}} |\n| Test | {{TODO}} |\n"
        "| Lint | {{TODO}} |\n| Types | {{TODO}} |\n| Run | {{TODO}} |"
    ),
}

SURFACES: dict[str, str] = {
    "Web UI": (
        "A web UI. Each screen shows the items, the state of each item, and what waits for a "
        "person. An action that a person approves shows the change before it happens. Each "
        "screen has a loading, an empty, and an error state."
    ),
    "API only": (
        "An API with no UI. Each endpoint validates its input at the boundary and returns typed "
        "errors that say what to fix. The API publishes its schema, and clients use types made "
        "from it."
    ),
    "Command line": (
        "A command-line tool. Each command that changes data prints what it will change and has "
        "a dry-run flag. Output for people is plain text; output for scripts is JSON."
    ),
    "Email or chat": (
        "No UI of its own. The agent works in email or chat. Each message that it sends says "
        "what it did, what it did not do, and how to reach a person."
    ),
}

IGNORE_BASE = (
    "# Private notes, saved prompts, and decision trails",
    ".local/",
    ".audit/",
    "# Secrets",
    ".env",
    ".env.*",
    "!.env.example",
    "*.pem",
    "*.key",
    "# Editors and systems",
    ".DS_Store",
    ".idea/",
    ".vscode/",
)
IGNORE_STACK: dict[str, tuple[str, ...]] = {
    "Python": (
        "# Python",
        "__pycache__/",
        "*.pyc",
        ".venv/",
        ".pytest_cache/",
        ".ruff_cache/",
        "dist/",
    ),
    "TypeScript": ("# TypeScript", "node_modules/", "dist/", "coverage/", "*.tsbuildinfo"),
    "Other": (),
}

STACK_HINTS: dict[str, str] = {
    "Python": "uv, pytest, ruff, and pyright.",
    "TypeScript": "pnpm, the test script, the lint script, and tsc.",
    "Other": "Leave the commands for you to fill in.",
}


def setup_questions(prefix: str = "") -> list[dict[str, object]]:
    """The two questions for the question tool that set the stack and the surface."""
    return [
        {
            "question": f"{prefix}which stack fills the commands in AGENTS.md?",
            "header": "Stack",
            "multiSelect": False,
            "options": [{"label": k, "description": v} for k, v in STACK_HINTS.items()],
        },
        {
            "question": f"{prefix}what does a person use to work with the product?",
            "header": "Surface",
            "multiSelect": False,
            "options": [
                {"label": k, "description": v.split(". ")[0] + "."} for k, v in SURFACES.items()
            ],
        },
    ]


CLAUDE_IMPORT = "\n## Shared agent rules\n\n@AGENTS.md\n"
RECORD_LINE = (
    "\n## Bet record\n\nThe bet record is `{record}`. The `bet-record` skill reads and checks "
    "it, and `/bookie BET-NNN` continues a bet at its current stage.\n"
)


def existing(root: Path, name: str) -> Path | None:
    for candidate in (name, ALIASES.get(name)):
        if candidate and (root / candidate).exists():
            return root / candidate
    return None


def write_ignore(root: Path, stack: str) -> str:
    """Create .gitignore, or add the missing default lines to it."""
    path = root / ".gitignore"
    wanted = [*IGNORE_BASE, *IGNORE_STACK[stack]]
    if not path.exists():
        path.write_text("\n".join(wanted) + "\n", encoding="utf-8")
        return "created"
    lines = path.read_text(encoding="utf-8").splitlines()
    have = {line.strip() for line in lines}
    missing = [line for line in wanted if not line.startswith("#") and line not in have]
    if not missing:
        return "kept"
    path.write_text("\n".join([*lines, "", "# Added by bookie", *missing]) + "\n", encoding="utf-8")
    return f"added {len(missing)} lines"


def render(name: str, project: str, record: str, stack: str, surface: str) -> str:
    text = (TEMPLATES / name).read_text(encoding="utf-8")
    return (
        text.replace("{{project}}", project)
        .replace("{{record}}", record)
        .replace("{{commands}}", STACKS[stack])
        .replace("{{surface}}", SURFACES[surface])
    )


def scaffold(root: Path, record: Path, stack: str, surface: str) -> list[tuple[str, str]]:
    """Create each missing file. Add only the missing links to an existing one."""
    if stack not in STACKS:
        raise SystemExit(f"--stack must be one of: {', '.join(STACKS)}")
    if surface not in SURFACES:
        raise SystemExit(f"--surface must be one of: {', '.join(SURFACES)}")
    relative = os.path.relpath(record.resolve(), root.resolve())
    actions = [(".gitignore", write_ignore(root, stack))]
    for name in FILES:
        path = existing(root, name)
        if path is None:
            (root / name).write_text(
                render(name, root.resolve().name, relative, stack, surface), encoding="utf-8"
            )
            actions.append((name, "created"))
            continue
        text = path.read_text(encoding="utf-8")
        if name == "CLAUDE.md" and "AGENTS.md" not in text:
            path.write_text(text.rstrip("\n") + "\n" + CLAUDE_IMPORT, encoding="utf-8")
            actions.append((name, "added the AGENTS.md import"))
        elif name == "AGENTS.md" and relative not in text:
            path.write_text(
                text.rstrip("\n") + "\n" + RECORD_LINE.format(record=relative), encoding="utf-8"
            )
            actions.append((name, "added the bet record line"))
        else:
            actions.append((name, f"kept {path.name}" if path.name != name else "kept"))
    return actions


def check(root: Path, record: Path) -> str | None:
    """Return the first problem with the project files, or None."""
    paths = {name: existing(root, name) for name in FILES}
    missing = [name for name, path in paths.items() if path is None]
    if missing:
        return f"missing in {root}: {', '.join(missing)}"
    relative = os.path.relpath(record.resolve(), root.resolve())
    texts = {path.name: path.read_text(encoding="utf-8") for path in paths.values() if path}
    if not any(relative in texts.get(name, "") for name in FILES[:2]):
        return f"neither AGENTS.md nor CLAUDE.md names the bet record {relative}"
    for name, text in texts.items():
        for number, line in enumerate(text.splitlines(), 1):
            if TODO in line:
                return f"{name}:{number} still has a {TODO} marker"
    return None
