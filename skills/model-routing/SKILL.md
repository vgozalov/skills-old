---
name: model-routing
description: Use when about to spawn a subagent or Codex job, or when asked how work was routed or what it cost. Picks the model across Claude (Haiku, Sonnet, Opus, Fable) and ChatGPT via Codex (Luna, Sol, Astra), with the conductor's own model as the ceiling, on the account with the most usage left.
---

# Model routing

Choose the cheapest permitted model expected to meet the job's acceptance criteria. Stronger models are for unresolved reasoning, consequential review, or demonstrated failure. Route on the job, not on how important it feels or which model is conducting: a frontier conductor must not make building expensive.

Paths below (`scripts/`, `references/`) are relative to this skill's folder: the base directory shown when the skill loads, typically `.claude/skills/model-routing/` in a project or `~/.claude/skills/model-routing/` when installed globally. Run the scripts from the repo root.

Each spawn is three decisions: the tier (from the job), the ceiling (from your own model), the provider (from usage left).

## Tiers and ceiling

| Tier        | Claude     | ChatGPT (Codex)                                                   | ChatGPT price, $ per M tokens in / out |
| ----------- | ---------- | ----------------------------------------------------------------- | -------------------------------------- |
| 1 Light     | Haiku 5.5  | `gpt-6-luna` (GPT-6 Luna)                                         | 0.10 / 0.50 (matches Haiku 5.5)        |
| 2 Workhorse | Sonnet 5.5 | `gpt-6.1-sol` (GPT-6.1 Sol; `gpt-6-sol` if the account lacks 6.1) | 2.00 / 10.00 (matches Sonnet 5.5)      |
| 3 Frontier  | Opus 5.5   | `gpt-6-astra` (GPT-6 Astra)                                       | frontier                               |
| 4 Top       | Fable      | none                                                              | —                                      |

**Each row is interchangeable.** Astra stands in for Opus, Sol for Sonnet, Luna for Haiku, and the other way round: a job routed to a tier may run on either provider, chosen by the user's stated preference, else by usage (below), and a reviewer on one counts the same as on the other. Terra and older GPT models are not routed; their tier is unverified. If Codex rejects a slug, tell the user.

**Tier 3 on ChatGPT (user's default, 2026-11-10):** run Astra at `--effort medium`; when Astra is rate-limited or the ChatGPT window is too low for it, fall back to Sol at `--effort high` for that job. Evidence, one side-by-side test so far: the same whole-branch review run three ways found the same findings each time, at these costs in the 5-hour window: Astra high +8%, Astra medium +7%, Sol high +3% (Sol took twice the steps). Earlier, three high-effort Astra plan reviews used a whole window. Re-run the comparison on the next large review and record the result here before changing this default.

Your own model is the ceiling on both providers: Sonnet allows tiers 1–2, Opus 1–3, Fable 1–4 (tier 4 only with a stated reason, after tier 3 failed or could not settle a call). Read your model from your own context, not the agent file. Never exceed the ceiling silently; say "needs a higher tier" to the user instead.

## Provider

The user's direction comes first. When the user names a provider for the session or a job ("mostly Claude", "Codex only"), use it at the job's tier; when that provider has no headroom left, ask before switching. Without a direction, the usage check below decides.

Run `python3 <skill folder>/scripts/check-account-usage.py` at intake and at the start of each phase. It reads both accounts without spending a model turn and prints each one's used windows, `headroom` (100 minus the fuller window) and a `pick`: the account with more headroom, Claude when within 10 points, and never an account at 10 or less while the other has room. `"ask"` means one account could not be read: ask the user once.

A job that stops on a usage limit is relaunched at the same tier on the other provider. For Codex jobs, `cat <skill folder>/references/use-codex.md` once per session.

## Review rule

A reviewer is fresh, never the author, never tier 1, and never below the author's tier, whichever provider each runs on. Same tier is fine. Work by several authors is reviewed at or above the highest. A fix check goes back to the reviewer who raised the findings only while its thread is small (under about 200k tokens); otherwise to a fresh reviewer of the same tier with the finding list and `git diff -- <files>`. Why: a weaker reviewer misses what the author got subtly wrong, and its pass is unearned. A reviewer from the other provider is a bonus when usage allows.

## Five questions about any job

1. Is the spec complete: file, signatures, behaviour, nothing left to choose?
2. Does it use an API this repo has never used?
3. Do more than about six rules interact (ordering, fallbacks, edge cases)?
4. Is the blast radius wide: several files, shared state, behaviour others depend on?
5. Would a wrong answer stay invisible until a user hits it?

No flags: tier 1. One or two local flags: tier 2. A flag that is really an unsettled design decision goes back to planning, not to a bigger builder. Small is not easy: a three-line permission change can need more judgement than a hundred lines of repetitive UI.

## Routing by role

"Top" means the highest tier you are permitted, capped at 3.

| Role                                                                                                                                 | Tier                                                                                        |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- |
| Narrow research, git state, running commands, reading logs, environment diagnosis                                                    | 1                                                                                           |
| Web research                                                                                                                         | 2                                                                                           |
| Broad research, root cause, design options (the user decides)                                                                        | top                                                                                         |
| Plan writer, design already settled by the user                                                                                      | 2                                                                                           |
| Plan writer, the plan must decide the design                                                                                         | top                                                                                         |
| Plan reviewer, routine plan                                                                                                          | 2, one agent with both lenses                                                               |
| Plan reviewer, substantial plan                                                                                                      | top, one agent; on a Sonnet ceiling, two tier-2 agents with one lens each, one per provider |
| Implementer, all five questions clean                                                                                                | 1                                                                                           |
| Implementer, local decisions remain                                                                                                  | 2                                                                                           |
| Implementer, flags a tighter spec cannot remove                                                                                      | top, reviewed at top                                                                        |
| Per-task review, only for risky tasks (two or more flags, event handling, shared state); otherwise the whole-branch review covers it | implementer's tier, minimum 2                                                               |
| Whole-branch review                                                                                                                  | top                                                                                         |
| Bug fixer (behaviour, framework, layout, async)                                                                                      | 2                                                                                           |
| Mechanical fixer (exact edit written out)                                                                                            | 1                                                                                           |
| Failing test or build                                                                                                                | 2; top if a design flaw                                                                     |
| Triage of conflicting findings                                                                                                       | top                                                                                         |

A plan is substantial when it decides the design, has more than five tasks, touches auth, permissions, persisted data or shared state, or its tasks carry two or more flags. Otherwise routine.

**Tighten before escalating.** A build job with flags goes back to the plan writer for the missing signatures, API usage and rules first; the plan reviewer should catch these by asking which tasks a tier-1 builder could not finish. Two more plan lines cost less than a frontier build.

## Escalation

- An unsettled design decision during building: stop the job, send the question to the plan writer.
- Fails review on ordinary grounds: one repair, as a fresh job given the findings and `git diff -- <files>` (mechanical findings tier 1, behaviour tier 2). Resume the original worker (SendMessage, or `--resume`) only when its thread is under about 200k tokens: a resumed thread re-sends its whole history on every step.
- Repair fails: the diff and failure evidence go one tier up, within your ceiling. A failure at your ceiling goes to the user, after at most two repair rounds.
- Missing dependency, service down, sandbox, network or auth error: a tier-1 agent diagnoses; the model does not change.
- Each repair is reviewed at the repairer's tier or above.

## Token budget

Every worker step re-sends its whole context, so cost grows with steps × context. The four habits that cost most in the first real run: long test output carried forward, whole large files read, fixes resumed on long threads, and per-task reviews duplicating the whole-branch review. The brief templates prevent the first two; the rules above prevent the last two. Use `medium` effort for routine reviews and builds, `high` only for plan review and the whole-branch review. Start a fresh conductor session per feature: the plan file and git carry the state.

Before writing a brief: `cat <skill folder>/references/write-briefs.md`. Before the final report: `cat <skill folder>/references/report-costs.md`.
