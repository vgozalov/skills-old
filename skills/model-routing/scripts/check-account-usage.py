#!/usr/bin/env python3
"""Print how much usage is left on the Claude and ChatGPT accounts, and which one to use next.

Neither check spends a model turn: Claude is read from `claude -p /usage`, ChatGPT from the
Codex app-server.
"""
import json
import queue
import re
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor

TIMEOUT_SECONDS = 60
CLOSE_CALL_POINTS = 10
NEAR_LIMIT_HEADROOM = 10
CLAUDE_WINDOW_LINE = re.compile(r"^Current (.+?): (\d+(?:\.\d+)?)% used", re.MULTILINE)
CLAUDE_WINDOW_NAMES = {"session": "5h", "week (all models)": "week"}


def headroom(used_values):
    return None if not used_values else round(100 - max(used_values), 1)


def read_claude():
    try:
        completed = subprocess.run(
            ["claude", "-p", "/usage", "--model", "haiku", "--output-format", "json"],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=tempfile.gettempdir(),
        )
        report = json.loads(completed.stdout).get("result") or ""
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as error:
        return {"headroom": None, "reason": f"claude /usage unreadable: {error}"}

    windows = {
        CLAUDE_WINDOW_NAMES.get(label.strip(), label.strip()): float(used)
        for label, used in CLAUDE_WINDOW_LINE.findall(report)
    }
    if not windows:
        return {"headroom": None, "reason": "claude /usage reported no subscription windows"}
    return {**windows, "headroom": headroom(list(windows.values()))}


def request_codex_rate_limits():
    process = subprocess.Popen(
        ["codex", "app-server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    )
    lines = queue.Queue()
    threading.Thread(target=lambda: [lines.put(line) for line in process.stdout], daemon=True).start()

    def send(message):
        process.stdin.write(json.dumps(message) + "\n")
        process.stdin.flush()

    def wait_for(request_id, deadline):
        while time.time() < deadline:
            try:
                message = json.loads(lines.get(timeout=max(0.1, deadline - time.time())))
            except (queue.Empty, json.JSONDecodeError):
                continue
            if message.get("id") == request_id:
                return message
        return None

    try:
        deadline = time.time() + TIMEOUT_SECONDS
        send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "model-routing", "version": "1"}}})
        wait_for(1, deadline)
        send({"method": "initialized"})
        send({"id": 2, "method": "account/rateLimits/read", "params": {"excludeResetCreditDetails": True}})
        return wait_for(2, deadline)
    finally:
        process.terminate()


def read_chatgpt():
    try:
        response = request_codex_rate_limits()
    except OSError as error:
        return {"headroom": None, "reason": f"codex not runnable: {error}"}
    result = (response or {}).get("result")
    if not result:
        return {"headroom": None, "reason": "no answer from codex app-server"}

    limits = result.get("rateLimits") or {}
    now = time.time()
    windows = {}
    for name, window in (("5h", limits.get("primary")), ("week", limits.get("secondary"))):
        if window and window.get("usedPercent") is not None:
            reset_passed = window.get("resetsAt") and window["resetsAt"] <= now
            windows[name] = 0.0 if reset_passed else float(window["usedPercent"])
    blocked = result.get("ordinaryUsageAllowed") is False or bool(limits.get("rateLimitReachedType"))
    return {**windows, "headroom": 0.0 if blocked else headroom(list(windows.values()))}


def pick_account(claude_headroom, chatgpt_headroom):
    if claude_headroom is None:
        return "ask" if chatgpt_headroom is not None else "claude"
    if chatgpt_headroom is None:
        return "claude"
    if chatgpt_headroom <= NEAR_LIMIT_HEADROOM < claude_headroom:
        return "claude"
    if claude_headroom <= NEAR_LIMIT_HEADROOM < chatgpt_headroom:
        return "chatgpt"
    if abs(claude_headroom - chatgpt_headroom) < CLOSE_CALL_POINTS:
        return "claude"
    return "claude" if claude_headroom > chatgpt_headroom else "chatgpt"


def main():
    with ThreadPoolExecutor(max_workers=2) as pool:
        claude_future, chatgpt_future = pool.submit(read_claude), pool.submit(read_chatgpt)
        claude, chatgpt = claude_future.result(), chatgpt_future.result()
    print(json.dumps({
        "claude": claude,
        "chatgpt": chatgpt,
        "pick": pick_account(claude["headroom"], chatgpt["headroom"]),
    }))


if __name__ == "__main__":
    main()
