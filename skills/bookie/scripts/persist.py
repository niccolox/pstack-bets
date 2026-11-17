"""Save each stage's prompts to .local and commit each stage to git."""

from __future__ import annotations

import datetime as dt
import re
import subprocess
from pathlib import Path

LOCAL = ".local"
SECRET = re.compile(
    r"(^|/)(\.env(\..*)?|.*\.pem|.*\.key|id_(rsa|ed25519|ecdsa)|credentials(\.json)?|.*secret.*)$",
    re.IGNORECASE,
)
DEFAULT_BRANCHES = ("main", "master", "")


def prompt_folder(root: Path, bet_id: str) -> Path:
    return root / LOCAL / "bookie" / bet_id / "prompts"


def ensure_ignored(root: Path) -> None:
    ignore = root / ".gitignore"
    lines = ignore.read_text(encoding="utf-8").splitlines() if ignore.exists() else []
    if not {f"{LOCAL}/", LOCAL, f"/{LOCAL}/", f"/{LOCAL}"} & {line.strip() for line in lines}:
        ignore.write_text("\n".join([*lines, f"{LOCAL}/"]) + "\n", encoding="utf-8")


def save_prompt(
    root: Path, bet_id: str, stage: str, number: int, text: str, today: dt.date
) -> Path:
    if not text.strip():
        raise SystemExit("the prompt text is empty; pass the filled prompt on stdin")
    if "<placeholder>" in text:
        raise SystemExit("the prompt still has a <placeholder>; fill it first")
    ensure_ignored(root)
    folder = prompt_folder(root, bet_id)
    folder.mkdir(parents=True, exist_ok=True)
    count = len(list(folder.glob(f"{stage}-p{number:02d}-*.md"))) + 1
    path = folder / f"{stage}-p{number:02d}-{count}.md"
    header = f"<!-- {bet_id} stage {stage}, prompt {number}, {today.isoformat()} -->\n\n"
    path.write_text(header + text.rstrip("\n") + "\n", encoding="utf-8")
    return path


def saved_prompts(root: Path, bet_id: str, stage: str) -> list[Path]:
    return sorted(prompt_folder(root, bet_id).glob(f"{stage}-p*.md"))


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=check
    )


def commit(root: Path, branch: str, message: str) -> tuple[str | None, list[str]]:
    """Commit every change under root. Never push.

    On a default branch or in a new repository, switch to `branch` first.

    Returns the short commit id, or None when nothing changed, and the files left out
    because their names look like secrets.
    """
    if git(root, "rev-parse", "--is-inside-work-tree", check=False).returncode:
        git(root, "init", "-q", "-b", "main")
    ensure_ignored(root)
    if git(root, "branch", "--show-current").stdout.strip() in DEFAULT_BRANCHES:
        exists = git(root, "rev-parse", "--verify", "-q", branch, check=False).returncode == 0
        git(root, "checkout", "-q", *([] if exists else ["-b"]), branch)
    git(root, "add", "-A", "--", ".")
    staged = git(root, "diff", "--cached", "--name-only").stdout.split()
    secrets = [name for name in staged if SECRET.search(name)]
    if secrets:
        git(root, "reset", "-q", "--", *secrets)
    if not set(staged) - set(secrets):
        return None, secrets
    git(root, "commit", "-q", "-m", message)
    return git(root, "rev-parse", "--short", "HEAD").stdout.strip(), secrets
