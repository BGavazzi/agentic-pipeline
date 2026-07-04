# Changelog

Format: newest entry on top. Never delete or rewrite past entries (typos excepted).

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
