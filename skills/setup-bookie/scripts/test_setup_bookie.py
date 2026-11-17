import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from setup_bookie import main, project, turn_off_setup_pstack

for key in ("GIT_AUTHOR", "GIT_COMMITTER"):
    os.environ[f"{key}_NAME"] = "Setup Test"
    os.environ[f"{key}_EMAIL"] = "setup@example.invalid"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


class SetupBookieTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.record = self.root / "docs" / "bet-process.md"

    def tearDown(self):
        self.folder.cleanup()

    def fill_todos(self):
        for name in ("AGENTS.md", "CLAUDE.md", "PRODUCTS.md", "DESIGN.md"):
            path = self.root / name
            lines = [line for line in path.read_text().splitlines() if "{{TODO" not in line]
            path.write_text("\n".join(lines) + "\n")

    def test_project_writes_the_files_and_turns_off_setup_pstack(self):
        actions = project(self.root, self.record, "Python", "Web UI")
        self.assertEqual(actions["AGENTS.md"], "created")
        self.assertEqual(actions[".gitignore"], "created")
        self.assertEqual(actions[".claude/settings.json"], "turned off setup-pstack")
        settings = json.loads((self.root / ".claude" / "settings.json").read_text())
        self.assertEqual(settings["skillOverrides"]["setup-pstack"], "off")
        self.assertIn("/setup-bookie", (self.root / "CLAUDE.md").read_text())

    def test_the_override_keeps_every_other_setting(self):
        path = self.root / ".claude" / "settings.json"
        path.parent.mkdir()
        path.write_text(json.dumps({"skillOverrides": {"gstack": "off"}, "model": "opus"}))
        self.assertEqual(turn_off_setup_pstack(self.root), "turned off setup-pstack")
        settings = json.loads(path.read_text())
        self.assertEqual(settings["skillOverrides"], {"gstack": "off", "setup-pstack": "off"})
        self.assertEqual(settings["model"], "opus")
        self.assertEqual(turn_off_setup_pstack(self.root), "kept")

    def test_invalid_settings_are_not_replaced(self):
        path = self.root / ".claude" / "settings.json"
        path.parent.mkdir()
        path.write_text("{not json")
        with self.assertRaisesRegex(SystemExit, "not valid JSON"):
            turn_off_setup_pstack(self.root)
        self.assertEqual(path.read_text(), "{not json")

    def test_commit_waits_for_the_todos_then_commits_on_a_setup_branch(self):
        project(self.root, self.record, "TypeScript", "API only")
        with self.assertRaisesRegex(SystemExit, "not committed"):
            main(["commit", "--root", str(self.root)])
        self.fill_todos()
        main(["commit", "--root", str(self.root)])
        self.assertEqual(git(self.root, "branch", "--show-current"), "setup/bookie")
        files = git(self.root, "ls-files").split()
        for name in ("AGENTS.md", "CLAUDE.md", "PRODUCTS.md", "DESIGN.md", ".gitignore"):
            self.assertIn(name, files)
        self.assertIn(".claude/settings.json", files)

    def test_questions_fit_the_question_tool(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            main(["questions"])
        calls = json.loads(out.getvalue())
        headers = [q["header"] for call in calls for q in call["questions"]]
        self.assertEqual(headers, ["Stack", "Surface"])


if __name__ == "__main__":
    unittest.main()
