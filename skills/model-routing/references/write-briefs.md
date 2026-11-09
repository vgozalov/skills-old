# Writing briefs

Every brief is self-contained: the worker has not seen this conversation. Paste what it needs, point at files for the rest, delete lines that do not apply.

## Rules that came from real runs

- **Contract, not mechanics.** Give the exact names and signatures other workers export, what must be true, and what is forbidden. Do not suggest techniques: a hint to "use the functional form of setState" produced a side effect inside an updater.
- **Name what not to run.** Workers run linters and builds out of habit.
- **Name the files each worker owns and must not touch.** Disjoint ownership is what makes parallel work safe, across providers too, since Claude and Codex workers share one working tree. At most four jobs at once, both providers counted.
- **Give a packet, so the worker does not explore.** Files, one existing example to copy, settled interfaces, the check to run. Repeated exploration is where most tokens go.
- **Cap test output.** Workers run `npx vitest run <file> --reporter=dot 2>&1 | tail -40`, adding `-t "<test name>"` while iterating. Full test output re-sent on every later step was the single biggest waste in the first run (one fix job: 1.98M input tokens).
- **Anchor with line ranges.** Give `file:line` ranges and short excerpts; workers read `sed -n <a>,<b>p <file>` instead of whole large files.
- **Reviewers get the distilled spec**, such as an earlier audit's numbered list, not raw prototypes or long documents.
- **Batch related mechanical changes into one job.** Each job has a fixed start-up cost (a trivial Codex run measured about 17k input tokens, three quarters cached).
- **Compact returns.** Status, changed files, checks, blockers, what it was unsure about. Code stays in files.
- **Reviewers are read-only** and return ranked findings with file:line, a reason and a failure scenario, plus one line on the checks that passed.
- **Fix checks say** "an issue that already exists in the original code does not count as a failure".

## Common block

```
Repo: <absolute path>   Branch: <branch>   (uncommitted working tree)
Other agents are editing other files at the same time. Touch only the files under "Your files".
Read first: <plan/spec path, sections>. <Ignore / Follow> its test steps.
Do NOT run: <npm run build, npm run lint, eslint, the full test suite, git add, git commit, git push>.
Tests: `npx vitest run <file> --reporter=dot 2>&1 | tail -40`. Read large files by line range.
Report in under <N> words.
```

Keep project rules in the repo's `AGENTS.md` (with `CLAUDE.md` symlinked to it) so Claude and Codex both load them automatically, and do not repeat them in briefs. Without that file, add the few rules the job needs. For Codex, add: "Do not commit, push or create branches."

## Researcher

```
Question: <one question>
Where to look: <dirs or files; what is out of scope>
Return a direct answer, then up to <5> file:line references. Say "not found" plainly. Read-only; propose nothing.
```

## Plan writer

```
Use the parallel-plans skill. Goal: <one sentence>. User decisions, verbatim: <list>. Research: <summaries or paths>.
Save to <the repo's plans folder>/<date>-<name>.md, following the repo's rule on whether plans are committed.
Each task states files, exact signatures, interfaces consumed and produced, the user's exact values, one example to copy, and its verification command.
Return the path and a five-line summary.
```

## Plan reviewer

```
Read <plan path> and <decisions>. Read-only.
Lens A, coverage and consistency: is every decision in a task; do names and signatures match across tasks?
Lens B, buildability and risk: which tasks could a tier-1 builder not finish from the plan alone, and what is missing; what will bite a user that no task tests?
Return at most 10 items, most severe first: severity | task | problem | fix. One line on what is solid.
```

## Implementer: task packet

```
Objective: <one sentence>
Acceptance criteria: <numbered, checkable>
Your files: <list>   Do not touch: <everything else, including tests unless told>
Example to copy: <file:lines that already does the same kind of thing>
Contract (others write these in parallel; they will exist): <module: exported names, signatures, one line of behaviour each>
Constraints and forbidden: <rules from the plan>
Verify with: <command and the output that means pass, or "re-read your files for syntax" when tests are waived>
Stop and report BLOCKED, without guessing, if: <a design choice the plan does not settle, a file outside your list must change, the contract does not fit>
You may read other files when this is not enough; keep it targeted.
Return in under <N> words: DONE / BLOCKED / FAILED, changed files, checks and results, blockers, what you were unsure about. No code in the reply.
```

For tier 1, also list every function with its exact behaviour.

## Whole-branch reviewer

```
Review the uncommitted tree on <branch> against <plan path> (Decisions, Review Focus). Read-only.
Check: (1) every import resolves, including named exports in node_modules; (2) files agree on names and shapes; (3) leftovers from removed code; (4) behaviour against each decision; (5) React correctness, polling loops, StrictMode hazards; (6) styling and overflow.
At most 12 real problems, most severe first: severity | file:line | problem | how it fails. Then one line of checks that passed, and one on whether the page renders without a runtime error.
```

## Fixer

```
Your files: <list>. Fix exactly these findings, nothing else:
<number | file:line | what to change>
Return status per finding, changed files, checks run, uncertainty.
```

## Fix check (to the reviewer who raised the findings)

```
These findings from your review were fixed: <number | file:line | what changed>
Read-only. PASS or FAIL per finding with file:line; say if a fix broke anything next to it or left an unresolved import.
An issue that already exists in the original code (`git show HEAD:<file>`) does not count as a failure.
```

## Git steward

```
Read-only. Report branch, `git status --short`, last 5 commit subjects, whether it is pushed, diffstat against <base>.
```
