# Finishing the branch

Run this after the final review is clean and its fixes are in. Integration is the user's decision: present the choice, wait, and do only what they pick. Under the chief, the chief asks and a tier-1 git steward runs the commands.

## 1. Evidence first

The branch is finished only on a green run of the full suites at the commit being integrated.

- If the ledger's final verification line names the current HEAD, that run is the evidence; cite it.
- If HEAD moved after it (a final fix, a rebase), run the suites now at HEAD, output capped with `| tail -40`.
- Red: report the failures and stop. No menu until the suites pass.

## 2. Know where you are

Capture these now; later steps change directory and still need them.

```bash
git_dir=$(cd "$(git rev-parse --git-dir)" && pwd -P)
common_dir=$(cd "$(git rev-parse --git-common-dir)" && pwd -P)
worktree_path=$(git rev-parse --show-toplevel)
branch=$(git branch --show-current)          # empty on a detached HEAD
main_root=$(git -C "$common_dir/.." rev-parse --show-toplevel)
```

`git_dir` equal to `common_dir` means an ordinary checkout, with no worktree to clean up.

## 3. Confirm the base

The base is the branch this work started from: the plan's header, the ledger, the handoff, or the branch's upstream. If none of them says, ask: "This branch started from `<best guess>`, right?" Merging into the wrong base is costly to undo, so never assume `main`.

## 4. Ask

On a named branch, offer exactly these:

```
The branch is done; <evidence>. How should I finish it?

1. Open a pull request into <base>
2. Merge into <base> here, locally
3. Keep the branch as it is for now
```

On a detached HEAD (a workspace the harness manages), offer only:

```
1. Push it as a new branch and open a pull request into <base>
2. Keep it as it is for now
```

Discarding the work is not on the menu. It happens only when the user asks for it in so many words (see below).

## 5. Do what they chose

**Pull request.** `git push -u origin <branch>` (from a detached HEAD: `git push origin HEAD:refs/heads/<new-branch>`). Open it with `gh pr create` on GitHub or `glab mr create` on GitLab, following the repo's PR template if it has one: the plan's goal, what each task delivered, the verification evidence. Report the URL. Keep the worktree; review feedback gets fixed there.

**Merge locally.**

```bash
cd "$main_root"
git switch <base>
git pull --ff-only
git merge --no-ff <branch>
```

Run the suites on the merged result, output capped. Red: stop and report; nothing has been pushed, so the merge is local and recoverable, and the branch and worktree stay where they are. Green: clean up the workspace (step 6), then `git branch -d <branch>`. Push `<base>` only if the user asks.

**Keep.** Report the branch, and the worktree path if there is one. Change nothing.

**Discard, only on an explicit request.** Show what would be lost and ask for the typed word:

```
This permanently deletes:
- branch <branch>
- these commits: <git log --oneline <base>..<branch>>
- the worktree at <worktree_path>

Type `discard` to confirm.
```

Accept only that word; "sure" or "get rid of it" is not confirmation. Then `cd "$main_root"`, clean up the workspace (step 6), and `git branch -D <branch>`.

## 6. Clean up the workspace

Only after a local merge or a confirmed discard; a pull request and a kept branch keep their worktree.

- Ordinary checkout (`git_dir` equals `common_dir`): nothing to remove.
- A worktree the harness created (for example with `EnterWorktree`): leave it to the harness, using its exit tool if it has one.
- A worktree this skill created, under `.worktrees/` or `worktrees/`: from `$main_root`, run `git worktree remove "$worktree_path"`, then `git worktree prune`.
- Any other worktree belongs to someone else; leave it.

If `git worktree remove` refuses because of modified or untracked files, those files exist nowhere else. Never add `--force` on your own. Show them (`git -C "$worktree_path" status --porcelain -uall`) and ask: commit them to the branch first, move them into the main checkout, or delete them. Do that, then remove the worktree.

## Quick reference

| Choice | Merges | Pushes | Keeps worktree | Deletes branch |
| --- | --- | --- | --- | --- |
| Pull request | no | yes | yes | no |
| Merge locally | yes | no | no | yes (`-d`) |
| Keep | no | no | yes | no |
| Discard (asked for, typed) | no | no | no | yes (`-D`) |

## Excuses that skip a step

| Excuse | What is true |
| --- | --- |
| "The tests passed earlier" | Only a run on the commit being integrated counts. |
| "They obviously want it merged" | The choice is theirs. Ask and wait. |
| "They seem finished with it, I'll offer to delete it" | The menu is complete as written; discard waits for their request. |
| "'Yeah, drop it' is a yes" | Only the typed word `discard` deletes anything. |
| "The PR is open, the worktree is clutter" | Review fixes happen there. It stays until the work lands. |
| "That other worktree looks stale" | Remove only worktrees this skill created. |
| "Removal refused, `--force` finishes the job" | The refusal means those files exist only there. Ask. |
| "The merged result failing is probably flaky" | A red merged result stops everything until it is understood. |
| "The base is obviously main" | Confirm it. A wrong-base merge is costly to undo. |
| "The push was rejected, force will fix it" | The remote moved. Find out why; force-push only when the user asks. |
