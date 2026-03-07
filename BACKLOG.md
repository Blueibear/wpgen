# BACKLOG.md

## Purpose

- Fact: This backlog is the single source of truth for planned work in this repo.
- Fact: Work is executed via a strict loop with two roles:
  - Role A: Claude Code (Implementer)
  - Role B: Codex (Verifier/Reviewer)
- Fact: No item is Done unless it exists in the repo at the cited paths and passes the listed validation commands.

## Workflow Loop

1) Codex produces an implementation-ready backlog slice with:
   - exact file paths
   - concrete steps
   - exact validation commands
   - expected outcomes

2) Claude Code implements only the scoped backlog IDs, then runs the validation commands and reports:
   - files changed
   - command outputs or exit codes
   - limitations

3) Codex verifies every claim and re-runs key checks:
   - approves, or
   - produces a smaller follow-up backlog slice

Non negotiables
- Fact: No placeholders in code. No omitted sections, no ellipses, no truncated files.
- Fact: Offline deterministic tests only in default CI runs. No real network calls.
- Fact: Ruff must pass for all changes.
- Fact: Black is configured in repo and should be enforced once wired into CI.
- Rule: Working tree must stay clean after tests.

## Repo Map Summary

- Fact: CLI entry point `wpgen` is `wpgen.main:main`.
- Fact: Confirmed CLI commands are:
  - `check-deps`
  - `generate`
  - `gui`
  - `init`
  - `serve`
  - `validate`
  - `wordpress`
- Fact: `wordpress` subcommands are:
  - `manage`
  - `test`
- Fact: Default generator path is Hybrid structured generation.
- Fact: Current renderer outputs classic PHP themes.
- Fact: CI runs lint, tests, build verification, and security scanning.
- Fact: Tests are intended to run offline with mock provider behavior.

## Status Codes

- TODO
- IN PROGRESS
- VERIFY
- DONE
- BLOCKED

## Phase 0: Docs, quality gates, and current-pipeline correctness

### WPGEN-DOC-000: Align CLAUDE.md and BACKLOG.md to actual repo behavior

- Status: TODO
- Severity: High
- Category: Process

Evidence
- Fact: Docs must reflect the actual command surface, CI jobs, and current classic-theme architecture.
- Fact: Earlier drafts understated CLI and CI behavior.

Implementation steps
1) Update `CLAUDE.md` to include:
   - `wordpress` command group
   - `manage` and `test` subcommands
   - CI build and security jobs
   - current classic-theme reality
   - block-theme target direction
2) Update `BACKLOG.md` to prioritize block-theme architecture and validator alignment.

Validation
- `python -m wpgen --help`
- `python -m wpgen wordpress --help`
- `Get-Content .\.github\workflows\ci.yml`

Expected outcomes
- Docs match actual repo behavior and roadmap direction.

---

### WPGEN-GATE-001: Enforce Black in dev tooling and CI

- Status: DONE
- Severity: High
- Category: Quality gate

Evidence
- Fact: Black is configured in `pyproject.toml`.
- Fact: CI does not run Black.
- Fact: `requirements-dev.txt` does not currently pin Black.

Implementation steps
1) Add a pinned Black version to `requirements-dev.txt`.
2) Add a CI step in `.github/workflows/ci.yml` to run `black --check .`.
3) If needed, format the repo and commit the changes.

Validation commands
- `pip install -e .`
- `pip install -r requirements-dev.txt`
- `ruff check .`
- `black --check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- `black --check .` exits 0 locally and in CI.

---

### WPGEN-VAL-002: Align validator rules with renderer rules for current classic-theme path

- Status: DONE
- Severity: High
- Category: Validation correctness

Evidence
- Fact: `wpgen/templates/renderer.py` enforces a larger required file set than `wpgen/utils/theme_validator.py`.
- Fact: `ThemeValidator` currently requires only `style.css` and `index.php`.
- Inference (Confidence: High, would raise it: a shared policy module elsewhere): A theme can pass validator checks while still violating renderer assumptions.

Implementation steps
1) Define one canonical required-file policy for the current classic-theme architecture.
2) Update `wpgen/utils/theme_validator.py` to match renderer-required outputs, or extract shared constants into a common module.
3) Add or update tests to assert validator and renderer stay aligned.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- Validator and renderer enforce the same required-file expectations for current classic themes.

---

### WPGEN-VAL-003: Deduplicate theme validation logic

- Status: DONE
- Severity: Medium
- Category: Code hygiene and correctness

Evidence
- Fact: `wpgen/utils/theme_validator.py` contains both:
  - `ThemeValidator`
  - standalone validation functions with overlapping logic
- Inference (Confidence: High, would raise it: an explicit backward-compatibility requirement): Duplicate validation logic creates drift risk.

Implementation steps
1) Choose a canonical validation path.
2) Refactor duplicate logic into shared helpers or remove one path.
3) Preserve current external behavior where needed.
4) Update tests accordingly.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- One canonical validation implementation exists, or duplicate logic is minimized enough to prevent policy drift.

---

### WPGEN-ENC-004: Fix encoding corruption in source comments and CLI report strings

- Status: TODO
- Severity: Medium
- Category: Output quality

Evidence
- Fact: Some source files show mojibake such as `â†’`, `âœ…`, and related garbled characters.
- Fact: This appears in docstrings and printed validation report strings.

Implementation steps
1) Identify files with encoding corruption.
2) Re-save or patch affected strings as valid UTF-8 text.
3) Ensure tests and CLI output remain deterministic.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- Human-facing source comments and CLI strings are clean and readable.

## Phase 1: Block Theme MVP architecture

Goal
- Fact: The chosen roadmap target is Block Theme.
- Inference (Confidence: High, would raise it: a contradictory design decision): The first major new capability should be a parallel block-theme output mode, not continued expansion of classic-theme-only rendering.

### WPGEN-BLOCK-101: Add block-theme generation mode

- Status: TODO
- Severity: Critical
- Category: Core capability

Evidence
- Fact: `GeneratorType` currently includes only `hybrid` and `legacy`.
- Fact: `ThemeRenderer` currently outputs only classic PHP theme files.
- Fact: No block-theme output templates are present in current renderer paths.

Implementation steps
1) Extend generator selection to support a block-theme architecture choice.
2) Add a new generator implementation for block-theme output.
3) Add renderer support for block-theme artifacts including:
   - `theme.json`
   - `templates/*.html`
   - `parts/*.html`
4) Keep output deterministic and testable.
5) Do not break current classic-theme behavior.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- Repo can generate a minimal valid block theme in a deterministic offline-tested path.

---

### WPGEN-BLOCK-102: Add block-theme validation mode

- Status: TODO
- Severity: Critical
- Category: Validation

Evidence
- Fact: Current validator is classic-theme oriented and validates PHP theme assumptions.
- Fact: Current validator does not validate `theme.json`, block templates, or template parts.

Implementation steps
1) Define required artifacts for block themes.
2) Add validator support for block-theme outputs.
3) Ensure classic-theme validation continues to work.
4) Add tests covering both architectures.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- Validator can correctly validate both classic-theme and block-theme outputs.

---

### WPGEN-CLI-103: Add user-facing theme architecture selection

- Status: TODO
- Severity: High
- Category: CLI and UX

Evidence
- Fact: Current command surface does not expose a confirmed user-facing block-theme mode selector.

Implementation steps
1) Add CLI option or request field for theme architecture selection.
2) Ensure defaults preserve current behavior.
3) Add tests for CLI selection logic.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- Users can explicitly choose classic or block generation path.

## Phase 2: Kadence-like feature families on top of block themes

Rule
- Fact: No parity claims. Only claim features backed by generator logic, output files, validator rules, and offline tests.

### WPGEN-PAT-201: Patterns and starter layouts

- Status: TODO
- Severity: High
- Category: Starter sites

Implementation steps
1) Add reusable block patterns and starter layout generation.
2) Add deterministic tests asserting pattern outputs exist and remain stable.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

---

### WPGEN-HDR-202: Header and footer variation system for block themes

- Status: TODO
- Severity: High
- Category: UX and layout system

Implementation steps
1) Add template-part variation support for headers and footers.
2) Add support for mobile navigation patterns and structure.
3) Add tests asserting output variants exist and are wired correctly.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

---

### WPGEN-WOO-203: WooCommerce support for block themes

- Status: TODO
- Severity: High
- Category: Ecommerce

Evidence
- Fact: WooCommerce flags already exist in current structured generation flow.
- Fact: Current output does not provide deep block-theme WooCommerce support.

Implementation steps
1) Add WooCommerce-aware block-theme outputs and styling strategy.
2) Add tests asserting WooCommerce-specific outputs appear when enabled.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

## Phase 3: Quality baselines for modern themes

### WPGEN-A11Y-301: Accessibility baseline enforcement

- Status: TODO
- Severity: High
- Category: Accessibility

Implementation steps
1) Define a minimal accessibility checklist for generated themes.
2) Add tests for landmarks, skip links, keyboard-safe nav structure, and focus-visible basics.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

---

### WPGEN-PERF-302: Performance baseline enforcement

- Status: TODO
- Severity: Medium
- Category: Performance

Implementation steps
1) Define a baseline asset strategy for generated themes.
2) Add tests asserting sane asset output and absence of obvious regressions.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

## Phase 4: Kadence-like design system maturity

### WPGEN-DESIGN-401: Theme.json design system and style variations

- Status: TODO
- Severity: High
- Category: Design system

Implementation steps
1) Expand block-theme generation to support a richer `theme.json` design token system.
2) Add style variations where practical.
3) Add tests asserting deterministic generation of design settings.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`
