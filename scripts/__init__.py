"""Importable deterministic harness modules.

The scripts are also executable CLI entry points.  Keeping this directory an
explicit package makes imports behave identically in local checkouts and clean
CI environments, where pytest may not add the repository root to ``sys.path``
in the same way as an interactive run.
"""
