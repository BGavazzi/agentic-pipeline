# Core CLI contract benchmark

This benchmark protects the command-line boundary of the core gate scripts on
Windows and Linux. It reads the canonical `GATE_SCRIPTS` allowlist from
`scripts/core_sync.py`, then starts each registered script as a child process.

The bounded corpus currently contains 44 cases across the 23 registered gates:

- 21 `--help` cases, expected to exit `0` for the argparse-based gates.
- 23 missing-input cases, expected to exit `2` for every registered gate.

`validate_task.py` and `validate_closure.py` are legacy validators that print
their usage docstring when no path is supplied; they do not expose argparse
`--help`, so they are covered by the invalid-input case only.

Each child process uses an argv list with `shell=False`, the repository root as
its working directory, and a five-second timeout (configurable up to 30
seconds). The environment is reduced to ordinary process settings and Python
encoding flags; credential-like variables are not forwarded. No test case
supplies a repository path, scanner command, output path, network endpoint, or
credential, so every case exits during argument handling before gate work can
begin.

The benchmark emits a compact summary by default. CI writes the full JSON
metrics report to `.docs/test-reports/cli-contract.json`:

```text
scripts_total, help_cases, invalid_input_cases, cases_total,
cases_passed, cases_failed, timeouts, duration_seconds
```

This is a CLI contract check, not a scanner or end-to-end gate run. Live
scanner behavior remains covered by the existing scanner contract job.
