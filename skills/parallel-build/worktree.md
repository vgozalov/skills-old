# Isolated workspace

Set this up before the first task when the user wants the build kept away from their checkout, or the plan asks for it. Never implement on `main` or `master` without the user's explicit consent.

## 1. Check whether you are already isolated

```bash
git_dir=$(cd "$(git rev-parse --git-dir)" && pwd -P)
common_dir=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
superproject=$(git rev-parse --show-superproject-working-tree 2>/dev/null)
branch=$(git branch --show-current)
```

- `git_dir` differs from `common_dir` and `superproject` is empty: you are in a linked worktree already. Use it; do not nest another. Report the path and the branch, or that HEAD is detached (then the branch is created when finishing).
- Otherwise (an ordinary checkout, or a submodule, which also shows differing dirs): you are in the user's checkout. Go on.

## 2. Ask, unless the answer is already given

If the user's instructions (`AGENTS.md`, `CLAUDE.md`, the plan, the run's brief) already say whether to use a worktree, follow them without asking. Otherwise ask once: "Build in a separate worktree, so your current branch stays untouched?" A no means work in place on a feature branch, and go to step 4.

## 3. Create it

**Use the harness's own tool first.** If you have one (Claude Code's `EnterWorktree`, a `/worktree` command, a `--worktree` flag), use it: it chooses the folder, creates the branch and cleans up, and a worktree made behind its back is state it cannot see.

**Otherwise use git:**

1. Choose the folder: one the user's instructions name; else an existing `.worktrees/`; else an existing `worktrees/` (`.worktrees/` wins when both exist); else create `.worktrees/`.
2. Confirm git ignores it: `git check-ignore -q <folder>`. If not, add the folder to `.gitignore` and commit that one change by path before going on; an unignored worktree folder gets committed with everything in it.
3. Create the worktree on a new branch from the plan's base:
   ```bash
   git worktree add "<folder>/<branch>" -b "<branch>" "<base>"
   cd "<folder>/<branch>"
   ```
4. If the sandbox refuses (`Operation not permitted`, permission denied), say so and work in place on a feature branch instead.

## 4. Prepare the project

Install what the project declares, using the tool its lockfile names: `package-lock.json` → `npm ci`, `pnpm-lock.yaml` → `pnpm install --frozen-lockfile`, `yarn.lock` → `yarn install --frozen-lockfile`, `uv.lock` → `uv sync`, `poetry.lock` → `poetry install`, `requirements.txt` → `pip install -r requirements.txt`, `go.mod` → `go mod download`, `Cargo.toml` → `cargo fetch`. Copy local env files the project's docs name (for example `.env.local`) from the main checkout; never commit them.

## 5. Take a clean baseline

Run the test suite once, output capped: `<test command> 2>&1 | tail -40`.

- Green: go on.
- Red: report the failures and ask whether to start anyway or investigate first. A red baseline makes every later failure ambiguous; starting past it is the user's call, not yours.

## 6. Report

```
Worktree ready: <full path> on <branch> (from <base>)
Baseline: <N> passing, <M> failing
```

Record the path and branch in the ledger, so finishing and a resumed session find them.

## Excuses that skip a step

| Excuse | What is true |
| --- | --- |
| "Clearly not a worktree, no need to check" | Harness-made worktrees and submodules both fool a glance; the two `rev-parse` lines settle it. |
| "`git worktree add` is quicker than looking for a tool" | The harness tool owns placement and cleanup; bypassing it leaves state it cannot manage. |
| "The folder is surely ignored" | Run `git check-ignore`. An unignored folder commits the whole worktree. |
| "Fresh checkout, the baseline can wait" | Without a baseline, no later failure can be blamed on the build or ruled out. |
