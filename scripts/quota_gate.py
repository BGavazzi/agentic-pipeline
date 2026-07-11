#!/usr/bin/env python3
"""quota_gate.py — deterministic STOP/CONTINUE gate for the dispatcher /loop.

Called by the dispatcher AFTER each task, BEFORE it decides whether to schedule
the next wake-up. Enforcement point for the ceilings the overnight loop respects.

Quota signal comes from <repo>/.claude/quota-state.json, written by the statusline
script from Claude Code's `rate_limits` payload (five_hour / seven_day:
used_percentage + resets_at). Pro/Max only, populated after the 1st API response.

THREE quota ceilings + a task cap (whichever trips first STOPS the loop):

  1. 5h window        — STOP when five_hour.used_percentage >= --threshold-5h (70).
  2. 7d daily budget  — the loop may add at most --daily-7d (10) percentage points
                        to the seven_day window PER LOOP-DAY. Baseline = the 7d%
                        captured when the day's loop began; STOP when
                        (current_7d - day_baseline) >= 10. Since the loop runs
                        overnight (no human usage between records), the delta is
                        the loop's own consumption.
  3. 7d weekly budget — cumulative loop consumption within one rolling 7d window
                        capped at --weekly-7d (50) points (= 5 days x 10). Anchored
                        to seven_day.resets_at; resets when the window rolls over.
  4. task cap         — STOP after --max-tasks (5) tasks in one loop-day. A task
                        may cost more than 1 against the cap via --task-weight
                        (e.g. a visual/browser-driving task is heavier than a
                        tsc+curl one) so the night doesn't overrun on a few
                        expensive tasks.

"Loop-day" is identified by local calendar date; a >--loop-window-hours gap also
forces a fresh day. The day index within the current week is tracked + reported.

Fail-safe: if the quota signal is entirely missing, verdict is STOP, never
CONTINUE. If only the 7d signal is missing (5h present), the 7d-based budgets are
skipped (logged) and 5h + task cap still apply.

Exit codes: 0 = CONTINUE  1 = STOP  2 = usage/internal error.
Deterministic, no LLM/network (sibling of validate_task.py / validate_closure.py).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def _load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError):
        return None


def _window(rate_limits, name):
    """Return (used_percentage|None, resets_at|None) for a window."""
    if isinstance(rate_limits, dict):
        w = rate_limits.get(name)
        if isinstance(w, dict):
            pct = w.get("used_percentage")
            pct = float(pct) if isinstance(pct, (int, float)) else None
            reset = w.get("resets_at")
            return pct, reset
    return None, None


def main() -> int:
    ap = argparse.ArgumentParser(description="Dispatcher quota/task-cap gate.")
    ap.add_argument("--repo", required=True, help="target repo path (cwd of the loop)")
    ap.add_argument("--threshold-5h", type=float, default=70.0,
                    help="STOP when 5h used_percentage >= this (default 70)")
    ap.add_argument("--daily-7d", type=float, default=10.0,
                    help="max 7d points the loop may consume per day (default 10)")
    ap.add_argument("--weekly-7d", type=float, default=50.0,
                    help="max 7d points the loop may consume per window (default 50)")
    ap.add_argument("--max-tasks", type=int, default=5,
                    help="STOP after this many tasks in one loop-day (default 5)")
    ap.add_argument("--loop-window-hours", type=float, default=6.0,
                    help="gap after which a new invocation starts a fresh loop-day")
    ap.add_argument("--record", action="store_true",
                    help="count this invocation as a finished task (increments)")
    ap.add_argument("--task-weight", type=int, default=1,
                    help="points this task costs against --max-tasks when --record "
                         "(default 1; use e.g. 3 for visual/browser-driving tasks)")
    ap.add_argument("--json", action="store_true", help="emit JSON verdict")
    args = ap.parse_args()

    repo = Path(args.repo)
    claude_dir = repo / ".claude"
    quota_file = claude_dir / "quota-state.json"
    loop_file = claude_dir / "dispatcher-loop-state.json"

    now = time.time()
    today = time.strftime("%Y-%m-%d", time.localtime(now))

    # --- read quota signal ----------------------------------------------------
    quota = _load_json(quota_file)
    rate_limits = quota.get("rate_limits") if isinstance(quota, dict) else None
    five_h, _ = _window(rate_limits, "five_hour")
    seven_d, reset_7d = _window(rate_limits, "seven_day")

    # --- load / roll loop-state ----------------------------------------------
    st = _load_json(loop_file)
    if not isinstance(st, dict):
        st = {}

    gap = now - float(st.get("updated_epoch", 0))
    new_week = (st.get("week_anchor") != reset_7d) and reset_7d is not None
    new_day = (
        st.get("day") != today
        or gap > args.loop_window_hours * 3600
        or not st
    )

    if new_week or not st:
        st = {
            "week_anchor": reset_7d,
            "week_loop_consumed": 0.0,
            "week_day_index": 0,
        }
        new_day = True

    if new_day:
        # carry the finished day's consumption into the weekly cumulative
        if seven_d is not None and st.get("day_baseline_7d") is not None \
                and st.get("day_last_7d") is not None:
            st["week_loop_consumed"] = float(st.get("week_loop_consumed", 0.0)) + max(
                0.0, float(st["day_last_7d"]) - float(st["day_baseline_7d"]))
        st["week_day_index"] = int(st.get("week_day_index", 0)) + 1
        st["day"] = today
        st["day_started_epoch"] = now
        st["day_baseline_7d"] = seven_d  # may be None; set lazily below
        st["tasks_done"] = 0

    # lazily set the day baseline once the 7d signal appears
    if st.get("day_baseline_7d") is None and seven_d is not None:
        st["day_baseline_7d"] = seven_d

    if seven_d is not None:
        st["day_last_7d"] = seven_d

    if args.record:
        st["tasks_done"] = int(st.get("tasks_done", 0)) + max(1, args.task_weight)
    st["updated_epoch"] = now

    try:
        claude_dir.mkdir(parents=True, exist_ok=True)
        loop_file.write_text(json.dumps(st, indent=2), encoding="utf-8")
    except OSError as e:
        print(f"STOP quota_gate: cannot write loop-state ({e})", file=sys.stderr)
        return 2

    tasks_done = int(st.get("tasks_done", 0))
    baseline = st.get("day_baseline_7d")
    day_consumed = (seven_d - baseline) if (seven_d is not None and baseline is not None) else None
    week_consumed = float(st.get("week_loop_consumed", 0.0)) + (day_consumed or 0.0)

    # --- verdict --------------------------------------------------------------
    verdict, reason = "CONTINUE", ""
    if five_h is None and seven_d is None:
        verdict, reason = "STOP", (
            "quota signal missing - statusline not configured or rate_limits not "
            "yet populated (Max/Pro, needs >=1 API response) - fail-safe stop")
    elif five_h is not None and five_h >= args.threshold_5h:
        verdict, reason = "STOP", f"5h window at {five_h:.1f}% >= {args.threshold_5h:.0f}%"
    elif day_consumed is not None and day_consumed >= args.daily_7d:
        verdict, reason = "STOP", (
            f"daily 7d budget spent: loop used {day_consumed:.1f} pts today "
            f">= {args.daily_7d:.0f}")
    elif week_consumed >= args.weekly_7d:
        verdict, reason = "STOP", (
            f"weekly 7d budget spent: loop used {week_consumed:.1f} pts this window "
            f">= {args.weekly_7d:.0f}")
    elif tasks_done >= args.max_tasks:
        verdict, reason = "STOP", f"task cap reached ({tasks_done}/{args.max_tasks})"
    else:
        note = "" if seven_d is not None else " [7d signal absent: daily/weekly budget not enforced]"
        reason = f"within all ceilings{note}"

    result = {
        "verdict": verdict,
        "reason": reason,
        "loop_day": today,
        "week_day_index": int(st.get("week_day_index", 0)),
        "tasks_done": tasks_done,
        "max_tasks": args.max_tasks,
        "five_hour_pct": five_h,
        "seven_day_pct": seven_d,
        "day_consumed_7d": round(day_consumed, 1) if day_consumed is not None else None,
        "week_consumed_7d": round(week_consumed, 1),
        "budgets": {"5h": args.threshold_5h, "daily_7d": args.daily_7d, "weekly_7d": args.weekly_7d},
    }

    if args.json:
        print(json.dumps(result))
    else:
        fh = f"{five_h:.0f}%" if five_h is not None else "?"
        sd = f"{seven_d:.0f}%" if seven_d is not None else "?"
        dc = f"{day_consumed:.1f}" if day_consumed is not None else "?"
        print(f"{verdict} - {reason} | day {st.get('week_day_index', 0)} ({today}) "
              f"| 5h:{fh} 7d:{sd} | loop today:{dc}/{args.daily_7d:.0f}pts "
              f"week:{week_consumed:.1f}/{args.weekly_7d:.0f}pts tasks:{tasks_done}/{args.max_tasks}")

    return 0 if verdict == "CONTINUE" else 1


if __name__ == "__main__":
    sys.exit(main())
