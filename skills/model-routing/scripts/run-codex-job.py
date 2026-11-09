#!/usr/bin/env python3
"""Run one Codex job and print a compact JSON summary instead of its transcript.

The brief is read from stdin. The full event log is kept on disk; its path is printed
only when the job did not complete.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

EFFORTS = ["low", "medium", "high", "xhigh", "max", "ultra"]
SANDBOXES = ["read-only", "workspace-write"]
USAGE_KEYS = {
    "input_tokens": "input",
    "cached_input_tokens": "cached",
    "output_tokens": "output",
    "reasoning_output_tokens": "reasoning",
}
USAGE_LIMIT_MARKERS = ["usage limit", "rate limit", "rate_limit"]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True, help="Codex model slug, e.g. gpt-6-luna")
    parser.add_argument("--effort", default="medium", choices=EFFORTS)
    parser.add_argument("--sandbox", default="read-only", choices=SANDBOXES)
    parser.add_argument("--cd", default=os.getcwd(), help="working root for the job")
    parser.add_argument("--resume", metavar="THREAD_ID", help="continue an earlier job's thread")
    parser.add_argument("--label", default="job", help="short name used in the log folder")
    return parser.parse_args()


def build_command(args, last_message_path):
    common = [
        "-m", args.model,
        "-c", f'model_reasoning_effort="{args.effort}"',
        "--disable", "multi_agent",
        "--json",
        "-o", last_message_path,
    ]
    if args.resume:
        return ["codex", "exec", "resume", *common, "-c", f'sandbox_mode="{args.sandbox}"', args.resume, "-"]
    return ["codex", "exec", *common, "-s", args.sandbox, "-C", args.cd, "-"]


def error_text(event):
    error = event.get("error")
    if isinstance(error, dict):
        return error.get("message") or json.dumps(error)
    return event.get("message") or (error if isinstance(error, str) else None)


def summarise_events(log_path):
    thread_id, error = None, None
    usage = {short: 0 for short in USAGE_KEYS.values()}
    steps, largest_item_chars = 0, 0
    with open(log_path, encoding="utf-8") as log:
        for line in log:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            event_type = event.get("type", "")
            if event_type == "thread.started":
                thread_id = event.get("thread_id")
            elif event_type == "item.completed":
                steps += 1
                largest_item_chars = max(largest_item_chars, len(line))
            elif event_type == "turn.completed":
                for key, short in USAGE_KEYS.items():
                    usage[short] += (event.get("usage") or {}).get(key, 0)
            elif event_type == "error" or event_type.endswith(".failed"):
                error = error_text(event) or event_type
    return thread_id, usage, steps, largest_item_chars, error


def read_text(path):
    if not os.path.exists(path):
        return ""
    with open(path, encoding="utf-8") as handle:
        return handle.read().strip()


def classify(exit_code, error):
    if error and any(marker in error.lower() for marker in USAGE_LIMIT_MARKERS):
        return "rate_limited"
    if exit_code != 0 or error:
        return "failed"
    return "completed"


def main():
    args = parse_args()
    brief = sys.stdin.read()
    if not brief.strip():
        print(json.dumps({"status": "failed", "error": "empty brief on stdin"}))
        return 2

    run_dir = os.path.join(tempfile.gettempdir(), "codex-runs", f"{time.strftime('%Y%m%d-%H%M%S')}-{args.label}")
    os.makedirs(run_dir, exist_ok=True)
    log_path = os.path.join(run_dir, "events.jsonl")
    last_message_path = os.path.join(run_dir, "last-message.txt")

    with open(log_path, "w", encoding="utf-8") as log:
        process = subprocess.run(
            build_command(args, last_message_path),
            input=brief,
            stdout=log,
            stderr=subprocess.PIPE,
            text=True,
            cwd=args.cd,
        )

    thread_id, usage, steps, largest_item_chars, error = summarise_events(log_path)
    if process.returncode != 0 and not error:
        error = "\n".join(process.stderr.strip().splitlines()[-15:]) or f"codex exited with {process.returncode}"
    status = classify(process.returncode, error)

    summary = {
        "status": status,
        "thread_id": thread_id or args.resume,
        "usage": usage,
        "steps": steps,
        "largest_item_chars": largest_item_chars,
    }
    if args.resume:
        summary["usage_scope"] = "thread total so far"
    summary["last_message"] = read_text(last_message_path)
    if status != "completed":
        summary.update({"exit_code": process.returncode, "error": error, "log": log_path})
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
