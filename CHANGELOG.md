# Changelog

Format: newest entry on top. Never delete or rewrite past entries (typos excepted).

## [2026-07-04] - Tighten blast_radius.py import/grep signal (found via dogfooding)
### Fixed
- `import_grep_signal` matched on generic filename stems (e.g. `SKILL`, from
  every `.claude/skills/*/SKILL.md`) as plain substrings — caught by running
  the classifier against this very PR's own diff, which flagged ~15 files as
  "affected" mostly through that one over-broad match. Added a stoplist of
  generic stems (`skill`, `index`, `readme`, `template`, `config`, `test`,
  etc.), raised the minimum stem length to 4, and switched to word-boundary
  matching (`\bstem\b`) instead of a bare substring search.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-04] - Implement blast-radius + risk-tier classifier (task 0002)
### Added
- `scripts/blast_radius.py` — deterministic diff-scoped blast-radius +
  risk-tier classifier, run between `builder` and `tester`/`ultrareview`.
  Unions three cheap heuristics (ownership map, import/grep, historical
  co-change) into `affected_modules`; classifies `risk_level` (low/medium/
  high) from path/diff triggers (auth/RBAC, migrations, payments, Ansible/
  Helm/Fleet/Terraform/Rancher/Nexus paths, or unusually wide blast radius);
  emits `.docs/blast-reports/<NNNN>.json` with `required_gates`.
- `.docs/module-owners.md` — this repo's own (illustrative) ownership map,
  the hand-maintained input to signal 1.
- `tests/test_blast_radius.py` — 6 unit tests against a throwaway git
  sandbox (plain pytest, not a `meta-test` fixture — see task 0002's Exit
  Conditions for why).
### Changed
- `dispatcher` SKILL.md §4 gains step 5b invoking `blast_radius.py`;
  `risk_level` for `ultrareview` is no longer assigned inline by dispatcher's
  own prose judgment — both `tester` and `ultrareview` SKILL.md now read
  `risk_level`/`required_gates` from the artifact as the single source of
  truth.
### Fixed (found while implementing, not pre-existing repo bugs)
- `detect_base()` no longer crashes when a repo has no `origin` remote
  (e.g. a fresh local sandbox) — falls through to local branches, then
  `master`.
- Co-change mining (signal 3) originally used `git log -- <path>
  --name-only`, which silently restricts the file list to that same
  pathspec and can never surface a co-changed file. Rewritten as: collect
  commit SHAs touching the file, then `git diff-tree --no-commit-id
  --name-only -r <sha>` per commit (no pathspec) for the full file list.
- git's `--format=<literal>` treats a literal string with no `%` codes as a
  named pretty-format alias lookup and errors ("invalid --pretty format")
  unless prefixed `format:` — affected the co-change commit-boundary
  delimiter; fixed to `--format=format:<delimiter>`.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi

## [2026-07-04] - Backlog: OSS scanning gate + blast-radius/risk-tier classifier; fix validator language drift
### Added
- `.docs/tasks/0001-feat-oss-static-analysis-gate.md` — backlog task for a
  deterministic SAST/SCA/secret-scan gate (Semgrep + Trivy + OWASP
  Dependency-Check + gitleaks → SARIF), the free/OSS half of what
  SonarQube/CodeRabbit provide.
- `.docs/tasks/0002-feat-blast-radius-risk-classifier.md` — backlog task for
  a diff-scoped blast-radius + risk-tier classifier gate feeding `tester`
  and `ultrareview`, extending risk triggers to infra (Ansible/Rancher/Nexus)
  changes.
- `.docs/tasks/000-template.md` — was referenced by README's quick-start but
  never actually existed in the repo (see Fixed, below).
### Fixed
- `scripts/validate_task.py` and `scripts/validate_closure.py` still checked
  Portuguese section titles (`Contexto`, `O Que Fazer`, `Condições de
  Saída`, `Pendências Honestas`, `Lei de Fechamento`) after the prior
  "translate all content to English" commit updated every doc to English
  headers (`Context`, `What To Do`, `Exit Conditions`, `Honest Backlog`,
  `Closure Law`). Any task written per current docs would have failed
  validation. See `.docs/tasks/0003-fix-validator-english-section-titles.md`.
- `.gitignore`'s `.docs/tasks/[0-9]*.md` rule also matched `000-template.md`
  (leading digit), silently preventing this repo from ever committing its
  own template or dogfood backlog. Removed the blanket ignore.
**Author**: Claude (agent), reviewed by Bernardo Gavazzi
