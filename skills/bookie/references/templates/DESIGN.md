# Design

This file says how {{project}} works. [PRODUCTS.md](PRODUCTS.md) says what it does and why. Change the design when an eval or a real failure shows a reason, and add the reason to the decision log in PRODUCTS.md.

## Workflow

Map the human job end to end before you choose tools. Each step is code, one model call, or a person.

| # | Step | Done by | Check |
| --- | --- | --- | --- |
| 1 | {{TODO: the first step of the job}} | {{TODO: code, model, or person}} | {{TODO: how the step is verified}} |

## Data shape

{{TODO: The core types and their fields, and the states that each item moves through.}}

One typed domain model is the source of truth. Database rows, API payloads, and model output come from it. Make illegal states impossible to represent.

## Agent ladder

The slice starts on rung {{TODO: 1, 2, or 3}}. Move up only when an eval shows that the lower rung fails.

| Rung | Use when |
| --- | --- |
| 1. Single call | The task fits in one step. |
| 2. Chain | The steps are known; code checks run between them. |
| 3. Router | Inputs fall into distinct types; a fallback category catches the rest. |
| 4. Parallel workers | The work splits cleanly, or a vote checks one answer. |
| 5. Orchestrator | The subtasks are not known in advance. |
| 6. Autonomous loop | Open-ended work, with budgets, checkpoints, and human gates. |

Deterministic code wraps every model step. Most of the value is in rungs 1 to 3.

## Integrations

| System | Path | Risk and control |
| --- | --- | --- |
| {{TODO: the system of record}} | {{TODO: API or EDI, email and files, scripted browser, model-driven browser, or human handoff}} | {{TODO}} |

- Keep credentials in a vault, with one scoped account for each customer. Never put a credential in a prompt.
- After each write, read the system again to prove the change.
- Record each run with its actions, and with screenshots for browser work.
- Make each write idempotent, so that a retry never files or books twice.

## Interface

{{surface}}

## Prompts and tools

- Keep each prompt in `prompts/`, with its version in the eval results.
- Put long documents first and the question last. Separate the parts with XML tags.
- Give the reason for each rule, 3 to 5 examples with one edge case, and a way to answer "not in the documents".
- Each tool has a plain name, a description with an example, typed parameters, and errors that say what to fix.
- Read-only tools run freely. A tool that writes has a dry-run mode, and an irreversible one needs approval.

## Evals

- The eval set is in `evals/`. It starts with 20 to 50 cases from real work: about 50% common, 30% edge, and 20% adversarial or out of policy. Each case has an intent tag.
- Each check is yes or no. A code grader comes first. An LLM judge is calibrated on about 30 cases that a person labeled.
- Each case runs 3 times, and the result is the pass rate. The target pass rate is {{TODO: a percentage}}.
- Each production bug becomes an eval case.

## Production

| Control | Default |
| --- | --- |
| Model choice | The smallest model that passes the evals, with hard cases sent to a larger one |
| Budget for each run | 20 steps, 120 seconds, and a spend cap from the unit cost in PRODUCTS.md |
| Reliability | Retries with backoff, timeouts, a fallback model, and schema validation |
| Tracing | Prompt, context, tool calls, output, tokens, cost, and feedback for each request |
| Limits | Rate limits and spend alerts for each user and tenant |
| Release | A feature flag and a rollback plan |

## Safety

- Untrusted input never starts a privileged action without a check.
- Keys are scoped and read-only by default.
- Personal data is removed before logs and before calls to a third party.
- Output is validated before anything runs it.
- An audit trail records who or what did each action.

## Failure modes

| Failure | How it is found | Response |
| --- | --- | --- |
| Malformed model output | Schema validation | Retry once, then send to a person |
| Provider outage | Timeout | Fallback model, then a queue |
| Instructions hidden in input | Injection eval cases | No privileged action; flag the item |
| A write that did not take effect | Read-back check | Retry the idempotent write, then alert |
| {{TODO: a failure that is specific to this workflow}} | | |

## Open questions

- {{TODO: A design question that an eval or a prototype must answer. Delete this line if there is none.}}
