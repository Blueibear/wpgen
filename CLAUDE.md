# CLAUDE.md

## Project Overview

- Fact: WPGen is a Python package that generates WordPress themes from natural language descriptions.
- Fact: WPGen ships three interfaces:
  - CLI via `wpgen` (entry point `wpgen.main:main`)
  - Gradio GUI (invoked via `wpgen gui`)
  - Flask web app under `web/`
- Fact: WPGen supports two generation modes:
  - Hybrid (default): JSON specification from LLM, validated against a schema, rendered to theme files via Jinja templates
  - Legacy (deprecated): direct LLM generated PHP, then repaired and validated

What it is today
- Fact: WPGen is primarily a theme scaffolding and generation tool with validation and optional integrations (GitHub push and WordPress REST API support).

What it is not today
- Fact: WPGen is not yet a “Kadence Pro equivalent” theme framework.
- Inference (Confidence: High, would raise it: a builder and options architecture landing in repo): Current theme output is based on a small set of static Jinja templates and does not implement a full theme options system, header builder, or deep WooCommerce template overrides.

Target vision for the repo
- Hypothesis (Confidence: Medium, would raise it: a written product spec and acceptance tests): WPGen should evolve into a generator that can output themes with “Kadence-like capabilities,” meaning:
  - A robust theme options system (Customizer or block theme configuration) for global design settings
  - Modular header and footer builder behavior (desktop and mobile)
  - Starter templates and reusable patterns
  - Deep WooCommerce integration and styling
  - Performance and accessibility baselines
  - Strong compatibility and validation gates

## Repo Structure

- Fact: `wpgen/` main Python package.
- Fact: `wpgen/main.py` Click CLI commands: `generate`, `gui`, `serve`, `validate`, `check-deps`, `init`.
- Fact: `wpgen/service.py` unified service layer used by interfaces, default generator is Hybrid.
- Fact: `wpgen/generators/hybrid_generator.py` JSON to Jinja pipeline.
- Fact: `wpgen/templates/` Jinja templates for PHP, CSS, JS outputs.
- Fact: `wpgen/schema/` and `wpgen/schema/theme_schema.py` define the validated JSON theme specification.
- Fact: `tests/` pytest suite.
- Fact: `web/app.py` Flask app.
- Fact: `scripts/` maintenance scripts and checks.

## Install

Python support
- Fact: Requires Python >= 3.10 (`pyproject.toml`).

Canonical install commands used by CI
- Fact:
  - `pip install -e .`
  - `pip install -r requirements-dev.txt`

Optional extras
- Fact: Optional extras are defined in `pyproject.toml` under `[project.optional-dependencies]` (ui, wp, git, dev).

## Run

CLI
- Fact: `wpgen init` creates a `.env` file from `.env.example` style guidance.
- Fact: `wpgen gui` launches the Gradio UI.
- Fact: `wpgen serve` launches the service mode exposed by CLI.
- Fact: `wpgen generate` generates a theme from a prompt.
- Fact: `wpgen validate <theme_path>` validates a generated theme directory.
- Fact: `wpgen check-deps` runs dependency checks.

Config
- Fact: Default config is `config.yaml`.
- Fact: CLI accepts `--config/-c` to override config path.

## Test and Lint

CI enforced commands
- Fact: CI runs:
  - `ruff check .`
  - `pytest -q -m "not integration" --disable-warnings`
  Evidence: `.github/workflows/ci.yml`

Offline deterministic tests
- Fact: CI sets `WPGEN_PROVIDER=mock` and `WPGEN_OFFLINE_TESTS=1`.
- Fact: Tests include a fixture that defaults to offline testing behavior.
  Evidence: `.github/workflows/ci.yml`, `tests/conftest.py`
- Rule: New tests must be offline and deterministic by default.
- Rule: Any test requiring network or external APIs must be marked `integration` and excluded from default CI.

Ruff requirements
- Fact: Ruff configuration exists in `pyproject.toml` under `[tool.ruff]`.
- Rule: All code changes must pass `ruff check .`.

Black requirements
- Fact: Black configuration exists in `pyproject.toml` under `[tool.black]`.
- Inference (Confidence: High, would raise it: CI step added): Black is not currently enforced in CI.
- Rule: The repo target state is to enforce Black for formatting consistency. If Black enforcement is added to CI, this file must be updated to reflect the exact CI commands.

Scoped commands for changed files
- Fact:
  - `ruff check path/to/file.py`
  - `pytest tests/test_some_file.py`
  - `pytest -k pattern`

Repo hygiene
- Rule: Working tree must stay clean after tests.
- Rule: Tests must not modify tracked files. If a test writes artifacts, it must use temporary directories or paths excluded from the repo.
- Inference (Confidence: Medium, would raise it: a CI step verifying clean git status): This is an expectation and should be enforced.

## Security and Secrets

Secrets model
- Fact: `.env.example` documents keys and credentials such as `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GITHUB_TOKEN`, and WordPress credentials.
- Fact: `wpgen init` creates `.env`.
- Rule: Never commit `.env`. Update `.env.example` when new variables are added.

Redaction
- Fact: Logger includes secret redaction patterns (`wpgen/utils/logger.py`).
- Rule: Do not log secrets. Redaction is defense in depth, not a license to print secrets.

## CI Rules

- Fact: CI workflow is `.github/workflows/ci.yml`.
- Fact: It runs on pushes to `main` and `claude/**`, and on PRs targeting `main`.

Commit and PR title rules
- Fact: No Conventional Commits or PR title lint tooling is present in this repo state.
- Rule: If commit rules are introduced, update this file with exact required formats and examples.

## Integration Strategy

LLM providers
- Fact: Supported providers are `openai`, `anthropic`, `local-lmstudio`, `local-ollama` (`config.yaml`).
- Rule: CI and unit tests must use mock provider and must not call real external services.

GitHub integration
- Fact: GitHub integration exists under `wpgen/github/`.
- Rule: Do not embed tokens in URLs or git remotes. Follow existing security tests.

WordPress integration
- Fact: WordPress REST API integration exists under `wpgen/wordpress/`.
- Rule: No real WordPress network calls in default CI tests.

## Kadence-like capability roadmap constraints

- Fact: Current generated theme templates are limited to baseline classic theme templates under `wpgen/templates/`.
- Inference (Confidence: High, would raise it: additional templates and builder modules): To approach Kadence-like capabilities, WPGen needs a larger theme framework and additional generation templates, not just better prompting.
- Rule: The generator should only claim Kadence-like feature support when it is backed by:
  - Template outputs
  - Theme self-tests and validators
  - Offline unit tests asserting the presence and behavior of the feature

## Agent Working Rules

Read before writing
- Rule: Before editing generator logic or templates, read:
  - `README.md`
  - `.github/workflows/ci.yml`
  - `config.yaml`
  - `wpgen/service.py`
  - `wpgen/generators/hybrid_generator.py`
  - `wpgen/schema/theme_schema.py`
  - `wpgen/templates/`
  - `tests/conftest.py`

Implementation discipline
- Rule: No placeholders, no truncated code, no “omitted” sections.
- Rule: Prefer minimal, testable changes.
- Rule: Keep tests offline and deterministic.

Update docs
- Rule: Update `CLAUDE.md` and `BACKLOG.md` when commands, config keys, CI gates, or repo structure change.
