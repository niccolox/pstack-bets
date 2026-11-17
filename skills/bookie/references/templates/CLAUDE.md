# CLAUDE.md

AGENTS.md holds the rules that every agent follows. This file adds what applies only to Claude Code.

@AGENTS.md

## Claude Code

- The pstack skills are in `.claude/skills/`. `skills-lock.json` pins them. Update them with `npx skills update`, then read `git diff`.
- The model for each subagent role is in `.claude/rules/pstack-models.md`. Run `/setup-bookie` to change it. `/setup-pstack` is off in this project.
- Ask each product call through `AskUserQuestion`, not in free chat: criteria, dates, scope, the human step, and the decision.
- The bet skills start only from a slash command: `/bookie`, `/bet-record`, `/bet-diligence`, and `/bet-discovery`.
- Keep long-run decision trails with `/show-me-your-work` in `.audit/`, which git ignores.
