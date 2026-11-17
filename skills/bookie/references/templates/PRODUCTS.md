# Products

This file holds the product decisions for {{project}}: what to build, for whom, and how to know that it works. [DESIGN.md](DESIGN.md) says how it works. The core question, the kill criteria, and the decision date are in `{{record}}`; this file does not copy them.

Change a decision by adding a row to the decision log. Do not edit an old row.

## Problem

{{TODO: Who has the problem, what they do about it today, and what it costs them in time, money, or customers. Use roles, not names.}}

## Fit check

A problem fits a fast AI build when each line is true. Write `yes` or `no` and the reason.

| Check | Answer |
| --- | --- |
| A wrong answer is cheap to catch. | {{TODO}} |
| A right answer saves real hours or money. | {{TODO}} |
| The model can see each fact that it needs. | {{TODO}} |
| Exact arithmetic and final decisions stay in code or with a person. | {{TODO}} |

## People

| Role | Who | Notes |
| --- | --- | --- |
| User | {{TODO: the role that does the work}} | |
| Buyer | {{TODO: the role that pays, and from which budget}} | |
| Design partners | 2 or 3, written as "design partner A", "B", "C" | They see the slice by day 5. |

## Success metric

{{TODO: One number with a time and a cost, tied to money. For example: "70% of cases resolved with no human touch, under 10 minutes and $0.50 each."}}

## Scope

**In.** {{TODO: The one workflow that the thin slice runs from end to end.}}

**Out.** Everything else, until the bet gets a go. {{TODO: Name the nearest things that are out.}}

## Human step

A person approves each action that moves money, sends a message outside the team, deletes data, or publishes. {{TODO: Name the other points where a person reviews, or write "none".}}

## Unit cost

The target cost for each finished task is {{TODO: an amount}}. A useful limit is 20% of what the same task costs a person.

## Build, buy, or partner

The scan and its result are in `{{record}}`. The diligence memos are beside the record.

## On a no-go

Record what the next bet can use: signals, contacts, and code.

## Decision log

| Date | Decision | Reason | Evidence |
| --- | --- | --- | --- |
