import datetime as dt
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from bookie import (
    BY_NAME,
    HANDOFF,
    PRELAUNCH,
    STAGES,
    find_bet,
    finish,
    next_stage,
    run_prompt,
    run_scaffold,
    save_progress,
    status,
)
from scaffold import FILES, TEMPLATES

TODAY = dt.date(2026, 11, 17)

for key in ("GIT_AUTHOR", "GIT_COMMITTER"):
    os.environ[f"{key}_NAME"] = "Bookie Test"
    os.environ[f"{key}_EMAIL"] = "bookie@example.invalid"


def git(root, *args):
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def save_any_prompt(record, root, stage):
    numbers = BY_NAME[stage].prompts
    if numbers:
        run_prompt(record, "BET-001", root, numbers[0], f"Filled prompt for {stage}.", TODAY)


RECORD = """## BET-001: Monitor

**Core question.** Is it accurate?

**Status.** {status}

**Criteria confirmed.** {confirmed}

**Decision date.** {decision}

### Kill criteria

| # | Criterion | Threshold | Evidence that counts | Result |
| --- | --- | --- | --- | --- |
| 1 | Pull | 3 users | logs | {result} |

### Build-or-buy scan

{scan}

### Build log

| Date | Unit | Evidence |
| --- | --- | --- |
{log}

### Customer evidence

| Date | Who | Kind | What they did | Evidence | Criterion |
| --- | --- | --- | --- | --- | --- |
{evidence}

### Decision memo

Not written.
"""

FRAMED = {
    "status": "Building",
    "confirmed": "2026-11-16",
    "decision": "2026-12-14",
    "result": "open",
    "scan": "Pingdom costs money; build.",
    "log": "",
    "evidence": "",
}


class BookieTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.record = self.root / "bets.md"
        save_progress(self.record, "BET-001", {"setup": {"status": "done"}})

    def tearDown(self):
        self.folder.cleanup()

    def write(self, **values):
        self.record.write_text(RECORD.format(**{**FRAMED, **values}), encoding="utf-8")

    def advance(self, *names, **kwargs):
        for name in names:
            save_any_prompt(self.record, self.root, name)
            finish(self.record, "BET-001", name, TODAY, root=self.root, **kwargs)

    def test_a_missing_bet_starts_at_frame_with_a_failed_gate(self):
        result = next_stage(self.record, "BET-001", TODAY, self.root)
        self.assertEqual(result["stage"], "frame")
        self.assertIn("no section", result["gate"])
        self.assertEqual(result["calls"], [])

    def test_frame_with_open_criteria_asks_the_bet_record_questions(self):
        self.write(status="Framing", confirmed="Open", decision="Open")
        result = next_stage(self.record, "BET-001", TODAY, self.root)
        headers = [q["header"] for call in result["calls"] for q in call["questions"]]
        self.assertEqual(headers, ["Criterion 1", "Decision"])
        with self.assertRaisesRegex(SystemExit, "frame gate"):
            self.advance("frame")

    def test_confirmed_frame_passes_and_moves_to_build_or_buy(self):
        self.write()
        self.advance("frame")
        self.assertEqual(
            next_stage(self.record, "BET-001", TODAY, self.root)["stage"], "build-or-buy"
        )

    def test_a_stage_cannot_finish_out_of_order(self):
        self.write()
        with self.assertRaisesRegex(SystemExit, "not the current stage"):
            self.advance("scope")

    def test_frame_score_and_memo_cannot_be_skipped(self):
        self.write()
        with self.assertRaisesRegex(SystemExit, "cannot be skipped"):
            finish(
                self.record, "BET-001", "frame", TODAY, note="no time", skip=True, root=self.root
            )

    def test_a_skip_needs_a_reason_and_is_recorded(self):
        self.write()
        self.advance("frame")
        with self.assertRaisesRegex(SystemExit, "reason"):
            finish(self.record, "BET-001", "build-or-buy", TODAY, skip=True, root=self.root)
        finish(
            self.record,
            "BET-001",
            "build-or-buy",
            TODAY,
            note="internal tool",
            skip=True,
            root=self.root,
        )
        self.assertEqual(status(self.record, "BET-001")[2]["status"], "skipped")

    def test_an_empty_scan_fails_its_gate(self):
        self.write(scan="<Existing products>")
        self.advance("frame")
        with self.assertRaisesRegex(SystemExit, "Build-or-buy scan"):
            self.advance("build-or-buy")

    def test_evidence_must_exist_beside_the_record(self):
        self.write()
        self.advance("frame", "build-or-buy")
        with self.assertRaisesRegex(SystemExit, "does not exist"):
            self.advance("scope", evidence="examples/")
        (Path(self.folder.name) / "examples").mkdir()
        self.advance("scope", evidence="examples/")
        self.assertEqual(next_stage(self.record, "BET-001", TODAY, self.root)["stage"], "evals")

    def test_harden_needs_every_item_and_keeps_partial_answers(self):
        self.write(log="| 2026-11-17 | slice | abc1234 |")
        (Path(self.folder.name) / "e").mkdir()
        self.advance("frame", "build-or-buy")
        self.advance("scope", "evals", evidence="e")
        self.advance("build")
        with self.assertRaisesRegex(SystemExit, "Rollback"):
            self.advance("harden", answers={"Tracing": "done"})
        rest = {label: "done" for label, _ in PRELAUNCH if label != "Tracing"}
        self.advance("harden", answers=rest)
        self.assertEqual(next_stage(self.record, "BET-001", TODAY, self.root)["stage"], "users")

    def test_iterate_waits_for_the_decision_date_unless_given_a_reason(self):
        self.write(
            log="| 2026-11-17 | slice | abc |",
            evidence="| 2026-11-17 | owner A | usage | Added 4 sites | rows.txt | 1 |",
        )
        progress = {s.name: {"status": "done"} for s in STAGES[:8]}
        save_progress(self.record, "BET-001", progress)
        with self.assertRaisesRegex(SystemExit, "in the future"):
            self.advance("iterate")
        self.advance("iterate", note="every criterion has its evidence")
        self.assertEqual(next_stage(self.record, "BET-001", TODAY, self.root)["stage"], "score")

    def test_score_needs_binary_results_and_memo_needs_a_decision(self):
        self.write()
        save_progress(self.record, "BET-001", {s.name: {"status": "done"} for s in STAGES[:9]})
        with self.assertRaisesRegex(SystemExit, "still open: 1"):
            self.advance("score")
        self.write(result="met")
        self.advance("score")
        with self.assertRaisesRegex(SystemExit, "not Decided"):
            self.advance("memo")
        self.write(result="met", status="Decided: go")
        self.advance("memo")
        self.assertIsNone(next_stage(self.record, "BET-001", TODAY, self.root)["stage"])

    def test_every_question_fits_the_question_tool(self):
        self.write(status="Framing", confirmed="Open", decision="Open")
        bet = find_bet(self.record, "BET-001")
        assert bet is not None
        asked = []
        for stage in STAGES:
            for question in stage.questions(bet, TODAY):
                asked.append(question["header"])
                self.assertLessEqual(len(question["header"]), 12, question["header"])
                self.assertTrue(2 <= len(question["options"]) <= 4, question["question"])
                for option in question["options"]:
                    self.assertLessEqual(len(option["label"].split()), 5, option["label"])
        self.assertEqual(asked.count("Pre-launch"), len(PRELAUNCH) // 4)
        self.assertEqual(asked.count("Handoff"), len(HANDOFF) // 4)


class SetupTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        (self.root / "docs").mkdir()
        self.record = self.root / "docs" / "bet-process.md"

    def tearDown(self):
        self.folder.cleanup()

    def scaffold(self, stack="Python", surface="Web UI"):
        return dict(run_scaffold(self.record, "BET-001", self.root, stack, surface))

    def test_a_new_bet_starts_at_setup_with_its_questions(self):
        result = next_stage(self.record, "BET-001", TODAY, self.root)
        self.assertEqual(result["stage"], "setup")
        self.assertIn("missing", result["gate"])
        headers = [q["header"] for call in result["calls"] for q in call["questions"]]
        self.assertEqual(headers, ["Stack", "Surface"])

    def test_scaffold_writes_four_files_that_name_the_record(self):
        self.assertEqual(set(self.scaffold().values()), {"created"})
        agents = (self.root / "AGENTS.md").read_text()
        self.assertIn("`docs/bet-process.md`", agents)
        self.assertIn("`uv run pytest`", agents)
        self.assertIn("@AGENTS.md", (self.root / "CLAUDE.md").read_text())
        self.assertIn("A web UI.", (self.root / "DESIGN.md").read_text())
        self.assertNotIn("{{project}}", agents)

    def test_the_gate_fails_until_every_todo_is_filled(self):
        self.scaffold()
        save_any_prompt(self.record, self.root, "setup")
        with self.assertRaisesRegex(SystemExit, "TODO marker"):
            finish(self.record, "BET-001", "setup", TODAY, root=self.root)
        for name in FILES:
            path = self.root / name
            lines = [line for line in path.read_text().splitlines() if "{{TODO" not in line]
            path.write_text("\n".join(lines) + "\n")
        finish(self.record, "BET-001", "setup", TODAY, root=self.root)
        self.assertEqual(next_stage(self.record, "BET-001", TODAY, self.root)["stage"], "frame")

    def test_existing_files_keep_their_text_and_get_only_the_missing_links(self):
        (self.root / "CLAUDE.md").write_text("# Mine\n\nKeep this.\n")
        (self.root / "PRODUCTS.md").write_text("# Products\n\nKeep this too.\n")
        actions = self.scaffold(stack="Other", surface="Command line")
        self.assertEqual(actions["CLAUDE.md"], "added the AGENTS.md import")
        self.assertEqual(actions["PRODUCTS.md"], "kept")
        claude = (self.root / "CLAUDE.md").read_text()
        self.assertTrue(claude.startswith("# Mine\n\nKeep this.\n"))
        self.assertEqual(
            set(self.scaffold(stack="Other", surface="Command line").values()), {"kept"}
        )

    def test_setup_writes_a_gitignore_for_the_stack(self):
        self.assertEqual(self.scaffold(stack="TypeScript")[".gitignore"], "created")
        lines = (self.root / ".gitignore").read_text().splitlines()
        for line in (".local/", ".env", "node_modules/"):
            self.assertIn(line, lines)

    def test_an_existing_gitignore_gets_only_the_missing_lines(self):
        (self.root / ".gitignore").write_text("# mine\n.env\n")
        self.assertEqual(self.scaffold(stack="Other")[".gitignore"], "added 9 lines")
        text = (self.root / ".gitignore").read_text()
        self.assertTrue(text.startswith("# mine\n.env\n"))
        self.assertEqual(text.count("\n.env\n"), 1)
        self.assertEqual(self.scaffold(stack="Other")[".gitignore"], "kept")

    def test_a_singular_product_file_counts_as_the_products_file(self):
        (self.root / "PRODUCT.md").write_text("# Product\n")
        self.assertEqual(self.scaffold()["PRODUCTS.md"], "kept PRODUCT.md")
        self.assertFalse((self.root / "PRODUCTS.md").exists())

    def test_an_agents_file_with_no_record_gets_the_record_line(self):
        (self.root / "AGENTS.md").write_text("# Rules\n")
        self.assertEqual(self.scaffold()["AGENTS.md"], "added the bet record line")
        self.assertIn("docs/bet-process.md", (self.root / "AGENTS.md").read_text())

    def test_templates_name_no_company_and_no_person(self):
        for path in TEMPLATES.iterdir():
            text = path.read_text()
            for word in ("BackOps", "Relay", "saasx2x", "@devekko", "niccolox"):
                self.assertNotIn(word, text, f"{path.name} names {word}")


class PersistTest(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.record = self.root / "docs" / "bets.md"
        self.record.parent.mkdir()
        self.record.write_text(RECORD.format(**FRAMED), encoding="utf-8")
        save_progress(self.record, "BET-001", {"setup": {"status": "done"}})

    def tearDown(self):
        self.folder.cleanup()

    def done(self, stage):
        return finish(self.record, "BET-001", stage, TODAY, root=self.root)

    def test_a_stage_with_prompts_needs_a_saved_prompt(self):
        with self.assertRaisesRegex(SystemExit, "no prompt saved"):
            self.done("frame")

    def test_prompts_go_to_local_and_stay_out_of_git(self):
        path = run_prompt(self.record, "BET-001", self.root, 1, "Frame BET-001.", TODAY)
        self.assertEqual(
            path.relative_to(self.root).parts[:4], (".local", "bookie", "BET-001", "prompts")
        )
        self.assertIn(".local/", (self.root / ".gitignore").read_text())
        result = self.done("frame")
        self.assertEqual(git(self.root, "branch", "--show-current"), "bet/bet-001")
        self.assertEqual(git(self.root, "log", "-1", "--format=%s"), "bookie(BET-001): frame done")
        committed = git(self.root, "ls-files")
        self.assertIn("docs/bets.md", committed)
        self.assertIn("docs/bookie/BET-001.json", committed)
        self.assertNotIn(".local", committed)
        self.assertEqual(result["commit"], git(self.root, "rev-parse", "--short", "HEAD"))

    def test_a_prompt_with_a_placeholder_is_refused(self):
        with self.assertRaisesRegex(SystemExit, "placeholder"):
            run_prompt(self.record, "BET-001", self.root, 1, "About <placeholder>.", TODAY)

    def test_files_named_like_secrets_are_left_out_of_the_commit(self):
        (self.root / ".env").write_text("TOKEN=x\n")
        run_prompt(self.record, "BET-001", self.root, 1, "Frame BET-001.", TODAY)
        result = self.done("frame")
        self.assertEqual(result["left_out"], [".env"])
        self.assertNotIn(".env", git(self.root, "ls-files").split())

    def test_a_skip_also_commits(self):
        run_prompt(self.record, "BET-001", self.root, 1, "Frame BET-001.", TODAY)
        self.done("frame")
        result = finish(
            self.record,
            "BET-001",
            "build-or-buy",
            TODAY,
            note="internal",
            skip=True,
            root=self.root,
        )
        self.assertEqual(
            git(self.root, "log", "-1", "--format=%s"), "bookie(BET-001): build-or-buy skipped"
        )
        self.assertIsNotNone(result["commit"])


if __name__ == "__main__":
    unittest.main()
