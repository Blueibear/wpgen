# BACKLOG.md

## Purpose

- Fact: This backlog is the single source of truth for planned work in this repo.
- Fact: Work is executed via a strict loop with two roles:
  - Role A: Claude Code (Implementer)
  - Role B: Codex (Verifier/Reviewer)
- Fact: No item is “Done” unless it exists in the repo at the cited paths and passes the listed validation commands.

## Workflow Loop

1) Codex produces an implementation-ready backlog slice with:
   - Exact file paths
   - Concrete steps
   - Exact validation commands
   - Expected outcomes

2) Claude Code implements only the scoped backlog IDs, then runs the validation commands and reports:
   - Files changed
   - Command outputs or exit codes
   - Limitations

3) Codex verifies every claim and re-runs checks:
   - Approves, or
   - Produces a smaller follow-up backlog slice

Non negotiables
- Fact: No placeholders in code. No “omitted”, no “…”, no truncated files.
- Fact: Offline deterministic tests only in CI. No real network calls in default test runs.
- Fact: Ruff must pass for all changes.
- Fact: Black is configured in repo. Enforce it when wired into CI.
- Rule: Working tree must stay clean after tests.

## Repo map summary

- Fact: CLI entry point `wpgen` is `wpgen.main:main` (`pyproject.toml`).
- Fact: Default generator is Hybrid JSON to Jinja (`wpgen/service.py`, `wpgen/generators/hybrid_generator.py`).
- Fact: Templates used for output are under `wpgen/templates/`.
- Fact: CI runs `ruff check .` and `pytest -q -m "not integration" --disable-warnings` (`.github/workflows/ci.yml`).
- Fact: Tests are intended to be offline and use mock provider (`tests/conftest.py`, CI env vars).

## Status codes

- TODO: Not started
- IN PROGRESS: Being implemented
- VERIFY: Implemented, awaiting Codex verification
- DONE: Verified by Codex with commands listed
- BLOCKED: Cannot proceed due to missing prerequisite

## Phase 0: Foundation docs and gates

### WPGEN-DOC-000: Add CLAUDE.md and BACKLOG.md at repo root

- Status: TODO
- Severity: High
- Category: Process

Evidence
- Fact: These files do not exist at repo root in the current repo state.

Implementation steps
1) Add `CLAUDE.md` and `BACKLOG.md` using the authoritative contents in this backlog cycle.

Validation
- `git status --porcelain` should show only the intended new files.

---

### WPGEN-GATE-001: Enforce Black in dev tooling and CI

- Status: TODO
- Severity: High
- Category: Quality gate

Evidence
- Fact: Black is configured in `pyproject.toml`.
- Fact: CI does not run Black.
- Fact: `requirements-dev.txt` does not pin Black.

Root cause
- Inference (Confidence: High, would raise it: CI showing Black already enforced): Black was not wired into dev install or CI.

Implementation steps
1) Add a pinned Black version to `requirements-dev.txt`.
2) Add a CI step in `.github/workflows/ci.yml` to run `black --check .`.
3) If required, format the repo with Black and commit the changes.

Validation commands
- `pip install -e .`
- `pip install -r requirements-dev.txt`
- `ruff check .`
- `black --check .`
- `pytest -q -m "not integration" --disable-warnings`

Expected outcomes
- `black --check .` exits 0 locally and in CI.

---

### WPGEN-TEST-002: Single source of truth for pytest configuration

- Status: TODO
- Severity: Medium
- Category: Test determinism

Evidence
- Fact: `pytest.ini` exists and defines test settings.
- Fact: `pyproject.toml` also defines `[tool.pytest.ini_options]`.

Root cause
- Inference (Confidence: High, would raise it: a note explaining intentional duplication): Duplicate configuration can drift.

Implementation steps
1) Choose one authoritative config location.
2) Remove or minimize duplication so only one source defines core pytest settings.
3) Confirm CI behavior remains unchanged.

Validation commands
- `pytest -q -m "not integration" --disable-warnings`

---

## Phase 1: Expand the safe Hybrid theme framework

Goal
- Inference (Confidence: High, would raise it: acceptance tests added): To approach Kadence-like capability, WPGen needs a much richer theme framework output by templates, not just better prompting.

### WPGEN-TPL-101: Expand template coverage to modern classic theme completeness

- Status: TODO
- Severity: High
- Category: Theme output completeness

Evidence
- Fact: Current Jinja templates cover a limited set of classic theme templates under `wpgen/templates/php/`.

Implementation steps
1) Add missing common templates to `wpgen/templates/php/` and ensure renderer includes them.
2) Add schema fields only if needed and validated.
3) Add offline tests that assert the expected files are generated for a theme.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

Notes
- Rule: Do not claim parity with any premium theme. Only claim concrete features backed by generated output and tests.

---

### WPGEN-OPT-102: Add a first-class theme options system architecture

- Status: TODO
- Severity: High
- Category: Kadence-like capability foundation

Evidence
- Fact: Current output is driven by a JSON spec and static templates. There is no dedicated theme options framework module or customizer specific implementation in templates.

Hypothesis (Confidence: Medium, would raise it: a clear decision between classic theme Customizer vs block theme approach)
- A sustainable path is either:
  - Classic theme with Customizer controls and dynamic CSS output, or
  - Block theme approach using `theme.json` and patterns

Implementation steps
1) Pick target: classic theme options via Customizer or block theme via `theme.json`.
2) Implement minimal viable global controls (colors, typography, container width) with tests asserting output.
3) Ensure no network calls are added and output is deterministic.

Validation commands
- `ruff check .`
- `pytest -q -m "not integration" --disable-warnings`

---

## Phase 2: Kadence-like feature families (only when backed by output + tests)

### WPGEN-HDR-201: Modular header and mobile navigation system

- Status: TODO
- Severity: High
- Category: Kadence-like UX

Scope examples (not exhaustive)
- Sticky header option
- Mobile off-canvas navigation
- Optional cart icon when WooCommerce enabled (schema already has flags)

Validation
- Offline tests that assert generated header structure and enqueue behavior.

---

### WPGEN-WOO-202: Deep WooCommerce template overrides and styling

- Status: TODO
- Severity: High
- Category: Ecommerce completeness

Evidence
- Fact: WooCommerce config exists in schema.
- Fact: Only limited WooCommerce mentions exist in current templates, and there are no dedicated WooCommerce template override files in `wpgen/templates/php/`.

Implementation steps
1) Add WooCommerce template overrides via Jinja templates.
2) Add hooks and styling consistent with schema options.
3) Add tests asserting those files are generated when WooCommerce is enabled.

Validation
- `pytest -q -m "not integration" --disable-warnings`

---

### WPGEN-PAT-203: Patterns and starter templates system

- Status: TODO
- Severity: Medium
- Category: Kadence-like starter sites

Implementation steps
1) Add a system to generate block patterns and reusable sections.
2) Add tests asserting deterministic outputs.

Validation
- `pytest -q -m "not integration" --disable-warnings`

---

## Phase 3: Quality, performance, and accessibility baselines

### WPGEN-A11Y-301: Accessibility baseline enforcement

- Status: TODO
- Severity: High
- Category: Accessibility

Implementation steps
1) Define a minimal a11y checklist for generated output.
2) Add offline tests that validate presence of skip link, focus styles, keyboard nav safe menu behavior.

Validation
- `pytest -q -m "not integration" --disable-warnings`

---

### WPGEN-PERF-302: Performance baseline enforcement

- Status: TODO
- Severity: Medium
- Category: Performance

Implementation steps
1) Define a baseline asset strategy in templates (defer, preload where appropriate, minimal blocking).
2) Add tests asserting enqueue output and absence of obvious performance regressions.

Validation
- `pytest -q -m "not integration" --disable-warnings`
