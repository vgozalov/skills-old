# Reporting costs

Run `check-account-usage.py` once more, then give the user:

1. A table of every worker: provider, model, job, tokens. Claude tokens come from completion notifications; Codex tokens from `run-codex-job.py` (input, cached, output, reasoning).
2. Totals by model, Claude and ChatGPT in separate columns. Never add the two providers into one total or one price, and state any price ratio as an assumption.
3. Each account's 5-hour and weekly use at the start and at the end, and when work switched provider.
4. A comparison with doing the work inline, labelled as an estimate. Delegation saves because each worker starts small, while inline work re-reads one large session on every call; parallelism saves time, not tokens.
5. One line per routing choice that was not obvious, where tier 3 or above was used and what it bought, and what you would route differently next time.
