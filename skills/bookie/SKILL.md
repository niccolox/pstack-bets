---
name: bookie
description: "Run a product bet from the first question to the go, no-go, or pivot memo in one guided session: setup, frame, build-or-buy, scope, evals, build, harden, users, iterate, score, memo. Ask the operator each product call through the question tool, and keep progress so a later call continues where the last one stopped. Write the project's AGENTS.md, CLAUDE.md, PRODUCTS.md, and DESIGN.md first. Use for /bookie, 'run the whole bet', 'set up a new bet project', 'walk me through the bet', 'start a new bet end to end', or 'where is this bet'."
disable-model-invocation: true
---

# Bookie

This skill runs one bet through eleven stages in a fixed order. Each stage does its work, asks the operator its questions, and passes a gate before the next stage starts. The other bet skills own the record and its format. This skill decides the order and holds the progress.

The operator started this skill to run the whole bet. So at each stage, read the SKILL.md that the stage names in `follow` and do its steps. Do not call those skills through the skill tool, because they start only from a slash command.

## Start

1. Find the bet record from the project `CLAUDE.md` or `AGENTS.md`, as **bet-record** says. Call its folder the record folder.
   In a new project, use `docs/bet-process.md`. Use `.local/bet-process.md` instead when the operator wants the record out of git.
2. Take the bet id from the invocation. With no id, and no bet that is not `Decided`, start a new bet. Ask the operator in chat for one paragraph: the problem, who has it, what they do about it today, and who pays. Use the next free `BET-NNN` id.
3. Run the stage loop.

## Stage loop

```sh
python3 .claude/skills/bookie/scripts/bookie.py <record> BET-NNN next
```

The script prints the current stage as JSON: its goal, the skill to follow, the prompt numbers in [`references/prompts.md`](references/prompts.md), the sections of [`references/practices.md`](references/practices.md) to read, the gate result, and the question calls. Then do these steps:

1. Tell the operator the stage number, its goal, and what you will ask, in at most three sentences.
2. Do the stage's work from the table below. Read the named practices and use the named prompts on yourself or in subagent briefs. Save each prompt after you fill it and before you use it:

   ```sh
   python3 .claude/skills/bookie/scripts/bookie.py <record> BET-NNN prompt --number <n> < <filled prompt file>
   ```

   The script writes it to `.local/bookie/BET-NNN/prompts/<stage>-p<n>-<count>.md` and keeps `.local/` in `.gitignore`. A stage that lists prompts cannot finish until at least one is saved.
3. Send each item of `calls` to the question tool (`AskUserQuestion` in Claude Code) in order, with the questions unchanged. The operator can pick an option or write free text. Apply each answer to the work.
4. Mark the stage done with its evidence and answers:

   ```sh
   python3 .claude/skills/bookie/scripts/bookie.py <record> BET-NNN done <stage> \
     --evidence <path from the record folder> --answer "<label>=<value>" --note "<text>"
   ```

   A passed `done` makes a local git commit, `bookie(BET-NNN): <stage> done`. See **Commits**.
5. If the gate fails, the script prints the reason and keeps the answers. Fix the cause and run `done` again. Ask the operator only when the fix is a product call.
6. Run `next` again. Continue until `stage` is `null`.

A stage that does not apply can be skipped with `skip <stage> --note "<reason>"` after the operator agrees. The frame, score, and memo stages cannot be skipped. A skip also makes a commit. `status` prints every stage with its state.

## Stages

| # | Stage | Work | Gate |
| --- | --- | --- | --- |
| 1 | setup | Ask the `calls` questions. Run `scaffold --stack <answer> --surface <answer>` from the project root. Then fill each `{{TODO}}` as **Project files** says. | The four files exist, AGENTS.md or CLAUDE.md names the record, and no `{{TODO}}` is left. |
| 2 | frame | Follow **bet-record** `frame`. Its operator dialog comes back in `calls` while the criteria are open. | The record passes its checker, and the criteria and decision date are confirmed. |
| 3 | build-or-buy | Spend at most one hour on prompt 2. Run **bet-diligence** on each serious candidate. Write the result in the record's Build-or-buy scan. | The scan section has real text. |
| 4 | scope | Map the job with prompt 3. Save 20 to 50 real examples and the success metric to one folder. | `--evidence` points at that folder. |
| 5 | evals | Build the eval set with prompt 7 and a judge rubric with prompt 8. Use the pass rate and the run count from the answers. | `--evidence` points at the eval set. |
| 6 | build | Follow the **poteto-mode** Feature playbook on the thin slice. Run the eval set. Log the unit with **bet-record** `log`. | The build log has a row. |
| 7 | harden | Do the pre-launch items. The operator marks the done items in `calls`. Do each item that is not done, or get the reason to skip it. | Each item has an answer, `done` or `skip: <reason>`. |
| 8 | users | Follow **bet-discovery**. Use prompt 15 for the questions. | The Customer evidence table has a row. |
| 9 | iterate | Each week, review real traces, add each failure to the evals, fix the top failure, and log it. Ask the `calls` question at the end of each week. | The decision date is today or past, or `--note` gives the reason to score early. |
| 10 | score | Follow **bet-record** `score`, with prompt 13. | Each criterion is `met` or `not met`. |
| 11 | memo | Follow **bet-record** `memo`, with prompt 14 and the memo items in the practices. On a go, do the handoff items that the operator did not mark. | The status is `Decided`. |

## Project files

The setup stage writes four files at the project root from [`references/templates/`](references/templates/). Each one takes the parts of the practices that belong to it:

| File | Holds | Defaults |
| --- | --- | --- |
| `AGENTS.md` | The rules for every agent: how to start a task, the commands, the bet rules, the code rules, the model rules, and what needs the operator | Start with `/poteto-mode`, name the data shape first, prove it on the real artifact, and work with no credentials |
| `CLAUDE.md` | An `@AGENTS.md` import and the rules for Claude Code only | Product calls go through `AskUserQuestion` |
| `PRODUCTS.md` | The problem, the fit check, the people, the success metric, the scope, the human step, the unit cost, and the decision log | A person approves money, outside messages, deletes, and publishes |
| `.gitignore` | `.local/`, `.audit/`, secrets, editor files, and the files that the stack builds | Missing lines are added; existing lines stay |
| `DESIGN.md` | The workflow, the data shape, the agent ladder rung, the integrations, the interface, prompts, evals, production, safety, and failure modes | Rungs 1 to 3, an eval mix of 50/30/20, 3 runs for each case, and 20 steps and 120 seconds for each run |

The script never replaces a file. A file that exists keeps its text: `CLAUDE.md` gets only the `@AGENTS.md` import, and `AGENTS.md` gets only the bet record line. `PRODUCT.md` counts as `PRODUCTS.md`.

Fill each `{{TODO}}` from the operator's paragraph and the setup answers:

- Write facts only. When a fact is not known yet, write `Open:` and the question that will answer it. Later stages fill those lines.
- Keep the files anonymous. Write people as roles and letters, and customers as kinds of company. Never write a name, an email, a company name, or a price from a private source.
- Keep a default unless the operator gives a reason to change it. Add that reason to the decision log in `PRODUCTS.md`.
- Do not copy the kill criteria into these files. The record holds them.

## Pauses

The users and iterate stages wait for people and for days. When a stage waits for something outside the session, end the turn. Say what the stage waits for, the date to come back, and the command to continue: `/bookie BET-NNN`. The progress file is `<record folder>/bookie/BET-NNN.json`, so the next call starts at the same stage with the answers that are already saved.

## A bet that started before this skill

Run `next` for each stage. When the gate already passes, mark the stage `done` with the evidence that exists. When the work happened in another form, ask the operator, then `skip` it with the reason. Do not repeat finished work. For setup, run `scaffold` anyway: it only adds what is missing.

## Commits

Each `done` and each `skip` commits every change under the project root, so each stage is one commit that you can review or revert:

- In a folder with no git repository, the script runs `git init` first.
- On `main`, `master`, or a new repository, it switches to the branch `bet/bet-nnn` first. On any other branch, it commits there.
- Files named like secrets (`.env`, `*.pem`, `*.key`, `credentials.json`, or a name with `secret`) stay out of the commit. The result lists them in `left_out`. Tell the operator about each one.
- It never pushes. A push, a PR, and a merge need the operator's words.

## Rules

- The operator makes every product call: criteria, decision date, path, human step, pass rate, first users, and the decision. Under a full-autonomy grant, still ask these questions.
- Do not move to the next stage before its gate passes.
- Do not change a criterion, a threshold, or the decision date in any stage after frame.
- Log each verified unit to the build log, and each act of a real person to the Customer evidence table.
