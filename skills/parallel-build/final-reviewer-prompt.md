# Final Reviewer Prompt Template

Use this template for the single whole-branch review after every task is
complete. The reviewer reads the branch's review package once and returns
what is good, what must change, and a merge verdict.

**Purpose:** Catch what task-scoped reviews cannot see: tasks that disagree
with each other, plan decisions no task delivered, leftovers, and risks that
only show across the whole branch, before the branch is finished.

```
Subagent (general-purpose):
  description: "Final whole-branch review"
  model: [MODEL — REQUIRED: the most capable available, per SKILL.md Model
         Selection; never below the strongest implementer's model]
  prompt: |
    [RUN TAG — under the chief, the first line: Run: <run folder>   Task: -   Role: review]
    You are the last reviewer of a branch that other agents built, task by
    task, from one plan. You wrote none of it. Your verdict decides whether
    it is ready to merge.

    ## What was supposed to be built

    Plan: [PLAN_FILE]. Read its Goal, Decisions and Review Focus, and each
    task's acceptance criteria.
    Ledger notes to triage: [DEFERRED_MINOR_AND_PARKED_LINES or "none"]
    Git-check warnings: [WARNINGS from git-check.py, or "none"]

    ## What was built

    Review package: [REVIEW_PACKAGE_FILE], covering [MERGE_BASE]..[HEAD].
    Read it once: it holds the commit list, a stat summary and the full diff
    with context. Open other files only to settle a specific suspicion, and
    then by line range.

    ## Rules

    - Read-only. Do not change the working tree, the index, HEAD or any
      branch. To see another revision, use `git show <rev>:<path>`, or check
      it out into a throwaway worktree under a temp directory, never here.
    - Do not spawn sub-reviewers or second opinions. This review is the
      seat; one you start duplicates it at full cost and counts for
      nothing. If the diff is large, review it in passes and say so.
    - The plan states intent, not every case. Where it is silent, judge by
      what a careful user of this software would expect; that expectation is
      a requirement. Rate such findings by their effect on that user.
    - A problem that already exists on [MERGE_BASE] is not a finding against
      this branch; mention it in one line at the end if it matters.
    - A problem in the plan itself, rather than in the build, is reported as
      a plan problem.

    ## What to check

    Plan fit: every decision delivered; nothing outside the plan's scope;
    each deviation either a justified improvement (say why) or a departure
    the user must confirm.

    Correctness across files: names, signatures, shapes and imports agree
    (including named exports from dependencies); error contracts match;
    edge cases and failure paths are handled where they occur.

    Design: responsibilities sit in sensible places; errors are handled,
    not swallowed; types are as precise as the language allows; no
    copy-paste that should be shared, and no abstraction the plan did not
    need; performance holds at real data sizes; no new security exposure.

    Tests: they prove behaviour, not mocks; edge cases are covered; nothing
    was weakened, skipped or special-cased to pass; no test depends on an
    uncommitted or skip-worktree change, which would fail on every other
    checkout.

    Shipping: migrations and backward compatibility where data or
    interfaces changed; config and docs updated; no debug output, dead code
    from replaced paths, TODOs the plan did not allow, or stray backup
    files (`*-E`, `*.orig`, `*.bak`).

    ## Return, in under 600 words

    ### Strengths
    Two to four specific things done well, with file:line. Accurate praise
    tells the fixer which parts not to touch.

    ### Findings
    Grouped as Critical (wrong behaviour, data loss, security, broken
    build), Important (missing requirement, poor error handling, test gap,
    design problem that will cost later) and Minor (polish). Grade by real
    effect; most branches have few criticals. For each:
      file:line | what is wrong | why it matters | the fix, if not obvious

    ### Ledger triage
    For each deferred or parked line: "must fix before merge" or "can wait",
    with a reason.

    ### Set aside
    Every behaviour you considered and judged out of scope, one line each
    with the reason, so the controller can rule on it. "None" if none.

    ### Ready to merge
    Yes | No | With fixes — then one or two sentences on why.
```
