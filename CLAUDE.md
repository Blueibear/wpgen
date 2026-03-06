# CLAUDE.md

## Project Overview

- Fact: WPGen is a Python package that generates WordPress themes from natural language descriptions.
- Fact: WPGen ships three interfaces:
  - CLI via `wpgen` with entry point `wpgen.main:main`
  - Gradio GUI via `wpgen gui`
  - Flask web app under `web/`
- Fact: WPGen supports two generation modes today:
  - Hybrid (default): LLM outputs a structured JSON specification, the JSON is validated against a schema, and Jinja templates render theme files
  - Legacy (deprecated): direct LLM generated PHP path
- Fact: The current production output model is a hardened classic WordPress PHP theme pipeline, not a block theme pipeline.
  Evidence: `wpgen/service.py`, `wpgen/generators/hybrid_generator.py`, `wpgen/templates/renderer.py`

What it is today
- Fact: WPGen is a structured theme generation and validation tool with optional GitHub push and optional WordPress REST API deployment.
- Fact: WPGen already includes more than basic theme scaffolding. The service layer supports:
  - prompt optimization
  - blueprint injection
  - design profiles
  - guided mode
  - optional feature overrides
  - image analysis
  - document text extraction
  - GitHub push
  - WordPress deploy and activate
  Evidence: `wpgen/service.py`

What it is not today
- Fact: WPGen is not yet a Kadence Pro equivalent theme framework.
- Fact: WPGen does not currently generate block theme artifacts such as:
  - `theme.json`
  - `templates/*.html`
  - `parts/*.html`
  - `patterns/`
  Evidence: `wpgen/templates/renderer.py`, `wpgen/templates/`
- Inference (Confidence: High, would raise it: a shipped block generator path and validator): The biggest gap between current repo state and repo goals is output architecture, not basic crash-proofing.

Target vision for the repo
- Fact: The chosen target direction is Block Theme.
- Inference (Confidence: High, would raise it: a contradictory repo product spec): WPGen should evolve into a generator that can output themes with Kadence-like capabilities through a deterministic block-theme architecture, meaning:
  - block theme generation mode
  - `theme.json` based global design system
  - template parts and starter patterns
  - deep WooCommerce support
  - accessibility and performance baselines
  - strong validation and compatibility gates

## Repo Structure

- Fact: `wpgen/` is the main Python package.
- Fact: `wpgen/main.py` contains the CLI command surface.
- Fact: Confirmed top-level CLI commands are:
  - `check-deps`
  - `generate`
  - `gui`
  - `init`
  - `serve`
  - `validate`
  - `wordpress`
  Evidence: `python -m wpgen --help`
- Fact: The `wordpress` command group contains:
  - `manage`
  - `test`
  Evidence: `python -m wpgen wordpress --help`
- Fact: `wpgen/service.py` is the unified service layer used by interfaces.
- Fact: `wpgen/generators/hybrid_generator.py` implements the default structured JSON to Jinja generation path.
- Fact: `wpgen/templates/renderer.py` renders classic theme PHP and JS outputs.
- Fact: `wpgen/schema/` defines the validated theme specification model.
- Fact: `wpgen/utils/theme_validator.py` validates generated theme directories.
- Fact: `tests/` contains a substantial pytest suite focused on generation safety, validation, fallback behavior, preview safety, and deployment-related logic.
- Fact: `web/app.py` exists as the Flask web app entry.
- Fact: `.github/workflows/ci.yml` defines the main CI workflow.

## Install

Python support
- Fact: Requires Python >= 3.10.
  Evidence: `pyproject.toml`

Canonical install commands used by CI
- Fact:
  - `pip install -e .`
  - `pip install -r requirements-dev.txt`

Optional extras
- Fact: Optional extras are defined in `pyproject.toml` under `[project.optional-dependencies]`.

## Run

CLI
- Fact: `wpgen init` initializes WPGen configuration and creates a `.env` file flow.
- Fact: `wpgen gui` launches the graphical user interface.
- Fact: `wpgen serve` starts the web UI server.
- Fact: `wpgen generate` generates a WordPress theme from a description.
- Fact: `wpgen validate <theme_path>` validates a WordPress theme for syntax errors.
- Fact: `wpgen check-deps` checks runtime dependencies.
- Fact: `wpgen wordpress manage` executes WordPress management commands using natural language.
- Fact: `wpgen wordpress test` tests the WordPress REST API connection.
  Evidence: CLI help output from `python -m wpgen --help` and `python -m wpgen wordpress --help`

Config
- Fact: Default config file is `config.yaml`.
- Fact: CLI accepts `--config/-c` to override config path.

## Current Generation Architecture

- Fact: The current main pipeline is:

  prompt
  → optional image analysis
  → optional document text extraction
  → prompt optimization
  → prompt parsing into requirements
  → Hybrid generator
  → JSON theme specification from LLM
  → schema validation and parsing
  → requirement overrides
  → Jinja rendering
  → classic PHP theme output
  → post-generation validation
  → optional GitHub push
  → optional WordPress deployment

  Evidence: `wpgen/service.py`, `wpgen/generators/hybrid_generator.py`

- Fact: `GeneratorType` currently supports only:
  - `hybrid`
  - `legacy`
  Evidence: `wpgen/service.py`
- Fact: There is no block theme generator type yet.

## Current Renderer and Validator Reality

Renderer
- Fact: `wpgen/templates/renderer.py` is currently hard-wired to classic theme output files such as:
  - `style.css`
  - `functions.php`
  - `header.php`
  - `footer.php`
  - `index.php`
  - `front-page.php`
  - `single.php`
  - `page.php`
  - `archive.php`
  - `search.php`
  - `404.php`
  - `sidebar.php`
  - `comments.php`
- Fact: The renderer includes strong hardening rules:
  - hard-locked fallback rendering for `header.php`
  - PHP lint validation via `php -l` when available
  - fallback templates when rendering fails validation
  - required template enforcement
  - stub detection
  Evidence: `wpgen/templates/renderer.py`

Validator
- Fact: `wpgen/utils/theme_validator.py` validates theme directories and runs PHP syntax checks when PHP is available.
- Fact: `wpgen/utils/theme_constants.py` is the single source of truth for required and recommended classic-theme files. Both the renderer and the validator import from this module.
- Fact: Required classic-theme files (shared): `style.css`, `functions.php`, `header.php`, `footer.php`, `index.php`, `front-page.php`, `single.php`, `page.php`, `archive.php`, `search.php`, `404.php`.
- Fact: Recommended classic-theme files (shared): `sidebar.php`, `comments.php`.
- Fact: Validator and renderer are aligned on required-file expectations.
  Evidence: `wpgen/utils/theme_constants.py`, `wpgen/templates/renderer.py`, `wpgen/utils/theme_validator.py`, `tests/test_theme_validator.py::TestRendererValidatorAlignment`

## Test and Lint

CI enforced commands
- Fact: Main CI currently runs:
  - `ruff check .`
  - `black --check .`
  - `pytest -q -m "not integration" --disable-warnings`
  Evidence: `.github/workflows/ci.yml`

Additional CI behavior
- Fact: CI also performs:
  - import diagnostics for key modules
  - package build using `python -m build`
  - import verification of built package
  - Trivy filesystem security scanning
- Fact: CI runs on Python 3.10, 3.11, and 3.12 on Ubuntu.
  Evidence: `.github/workflows/ci.yml`

Offline deterministic tests
- Fact: CI sets `WPGEN_PROVIDER=mock`.
- Fact: CI sets `WPGEN_OFFLINE_TESTS=1` in test-related steps.
- Fact: CI sets `PYTHONDONTWRITEBYTECODE=1`.
- Fact: Tests include fixtures supporting offline behavior.
  Evidence: `.github/workflows/ci.yml`, `tests/conftest.py`
- Rule: New tests must be offline and deterministic by default.
- Rule: Any test requiring network or external APIs must be marked `integration` and excluded from default CI.

Ruff requirements
- Fact: Ruff is configured in `pyproject.toml`.
- Rule: All changes must pass `ruff check .`.

Black requirements
- Fact: Black is configured in `pyproject.toml`.
- Fact: Black is enforced in CI via `black --check .`.
- Fact: Black is pinned in `requirements-dev.txt` at `black==24.8.0`.
  Evidence: `.github/workflows/ci.yml`, `requirements-dev.txt`
- Rule: All changes must pass `black --check .`.

Scoped commands for changed files
- Fact:
  - `ruff check path/to/file.py`
  - `pytest tests/test_some_file.py`
  - `pytest -k pattern`

Repo hygiene
- Rule: Working tree must stay clean after tests.
- Rule: Tests must not modify tracked files.
- Inference (Confidence: Medium, would raise it: an explicit CI git status gate): This is expected behavior but not fully enforced by CI today.

## Security and Secrets

Secrets model
- Fact: `.env.example` documents keys and credentials such as:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GITHUB_TOKEN`
  - WordPress credentials and site settings
- Fact: `wpgen init` participates in local configuration setup that results in `.env` usage.
- Rule: Never commit `.env`.
- Rule: Update `.env.example` when new variables are introduced.

Redaction
- Fact: Logger includes secret redaction patterns in `wpgen/utils/logger.py`.
- Rule: Do not log secrets. Redaction is defense in depth, not permission to expose credentials.

## CI Rules

- Fact: Main CI workflow is `.github/workflows/ci.yml`.
- Fact: It runs on:
  - pushes to `main`
  - pushes to `claude/**`
  - pull requests targeting `main`
  - manual dispatch
- Fact: CI currently has three main jobs:
  - test
  - build
  - security
  Evidence: `.github/workflows/ci.yml`

Commit and PR title rules
- Fact: No Conventional Commits enforcement or PR title lint tooling was identified in the current repo state.
- Rule: If commit or PR title rules are introduced later, update this file with the exact enforced format and examples.

## Integration Strategy

LLM providers
- Fact: Supported providers include:
  - `openai`
  - `anthropic`
  - `local-lmstudio`
  - `local-ollama`
  Evidence: `wpgen/service.py`, `config.yaml`
- Rule: CI and default tests must use mock provider behavior and must not call real external services.

GitHub integration
- Fact: GitHub integration exists under `wpgen/github/`.
- Rule: Do not embed tokens in git remotes or URLs.
- Rule: Follow existing GitHub security tests when changing push behavior.

WordPress integration
- Fact: WordPress REST API integration exists under `wpgen/wordpress/`.
- Fact: CLI exposes WordPress site management and API connectivity testing.
- Rule: Default CI tests must not hit real WordPress endpoints.

## Kadence-like Capability Roadmap Constraints

Current reality
- Fact: Current generated theme output is a hardened classic PHP theme, not a block theme.
- Fact: Current validator logic is also classic-theme oriented.
- Fact: Current repo does not yet generate block theme artifacts.

Roadmap rule
- Inference (Confidence: High, would raise it: shipped block-theme modules and tests): To approach Kadence-like capabilities, WPGen needs a new block-theme output architecture rather than indefinite expansion of the current classic-only renderer.
- Rule: Do not claim Kadence-like feature support unless it is backed by:
  - generator logic
  - rendered output files
  - validator rules
  - offline tests asserting presence and behavior

## Agent Working Rules

Read before writing
- Rule: Before editing generation logic or validation logic, read:
  - `README.md`
  - `.github/workflows/ci.yml`
  - `config.yaml`
  - `wpgen/main.py`
  - `wpgen/service.py`
  - `wpgen/generators/hybrid_generator.py`
  - `wpgen/templates/renderer.py`
  - `wpgen/utils/theme_validator.py`
  - `wpgen/schema/`
  - `tests/conftest.py`

Implementation discipline
- Rule: No placeholders, no truncated code, no omitted sections.
- Rule: Prefer minimal, testable changes.
- Rule: Keep tests offline and deterministic.

Docs updates
- Rule: Update `CLAUDE.md` and `BACKLOG.md` whenever commands, config keys, CI gates, repo structure, or roadmap priorities change.
