# CLAUDE.md (WPGen)

## Project Overview

- **Fact:** WPGen is a Python package that generates WordPress themes from natural language prompts, with optional GitHub push and optional WordPress REST API integration. (Primary docs: `README.md`, config: `config.yaml`, package: `wpgen/`)
- **Fact:** WPGen provides multiple user interfaces:
  - CLI via a console script entry point `wpgen` mapped to `wpgen.main:main` (`pyproject.toml`).
  - Gradio GUI via `wpgen gui` (`wpgen/main.py`, `README.md`).
  - Flask web app under `web/` (`web/app.py`).
- **Fact:** CI is designed to run deterministically and offline by forcing a mock provider in tests (`tests/conftest.py`) and setting `WPGEN_PROVIDER=mock` in GitHub Actions (`.github/workflows/ci.yml`).

- **Inference (Confidence: High, would raise it: a short architecture diagram in-repo):** This repo is a theme generator and validation tool first, not a full WordPress site builder or hosting platform.
- **Fact:** There is a GitHub Actions workflow named “Deploy WPGen Theme” that is explicitly labeled as a template workflow (`.github/workflows/deploy.yml`).

## Repo Structure

Top-level (as observed in the zip):

- **Fact:** `wpgen/` is the main Python package.
- **Fact:** `tests/` contains the pytest suite used in CI (`pytest.ini`, `.github/workflows/ci.yml`).
- **Fact:** `web/` contains a Flask web application (`web/app.py`).
- **Fact:** `scripts/` contains utility scripts (examples: `scripts/php_lint_generated.py`, `scripts/smoke_generate_and_scan.py`, `scripts/check_flask_cors_version.py`).
- **Fact:** `config.yaml` is the default configuration file referenced by the CLI and docs.
- **Fact:** `.env.example` documents environment variables and is used by `wpgen init` to create a local `.env` (`wpgen/main.py`, `README.md`).
- **Fact:** Tooling and metadata files include `pyproject.toml`, `setup.py`, `requirements.txt`, `requirements-dev.txt`, `requirements-optional.txt`, `pytest.ini`, `codecov.yml`, and GitHub workflows under `.github/workflows/`.

Key modules and entry points:

- **Fact:** CLI implementation lives in `wpgen/main.py` and defines commands including `generate`, `gui`, `serve`, `validate`, `check-deps`, `init` (decorated with `@cli.command()`).
- **Fact:** Flask app entry is `web/app.py`.
- **Fact:** GitHub integration code exists under `wpgen/github/` (referenced by CLI imports, and covered by tests like `tests/test_github_push_security.py`).
- **Fact:** WordPress REST API integration exists under `wpgen/wordpress/` (imported in CI diagnostics step: `wpgen.wordpress.wordpress_api`).

## Install

### Supported Python versions

- **Fact:** Project requires Python `>=3.10` (`pyproject.toml`).
- **Fact:** CI tests on Python 3.10, 3.11, 3.12 on Ubuntu (`.github/workflows/ci.yml`).

### Editable install

- **Fact (canonical for CI):**
  - `pip install -e .`
  - `pip install -r requirements-dev.txt`
  (`.github/workflows/ci.yml`)

- **Fact (documented in README):**
  - Basic install: `pip install -e .`
  - Full features: `pip install -e .[dev,ui,git,wp]`
  (`README.md`, `pyproject.toml` optional dependency groups)

### Virtualenv activation notes

- **Fact:** README provides venv activation commands for Windows and macOS/Linux (`README.md`).

### OS notes

- **Inference (Confidence: Medium, would raise it: a dedicated “Platform Support” section with tested OS matrix):** Windows, macOS, and Linux are intended to work for local usage because the README includes platform-specific venv activation, and the project does not appear Linux-only.
- **Fact:** CI runs on Ubuntu only (`.github/workflows/ci.yml`).

## Run

Primary CLI commands (from `wpgen/main.py` and `README.md`):

- **Fact:** Initialize local environment file:
  - `wpgen init`
  This creates a `.env` file and prompts you to fill in secrets (`README.md`, `wpgen/main.py`).

- **Fact:** Launch Gradio GUI:
  - `wpgen gui`
  - Alternative: `python -m wpgen gui`
  (`README.md`)

- **Fact:** Run the Flask web service command:
  - `wpgen serve`
  (`wpgen/main.py`)

- **Fact:** Generate a theme (CLI command exists as `generate`):
  - `wpgen generate ...`
  (`wpgen/main.py`)

- **Fact:** Validate a generated theme directory:
  - `wpgen validate <theme_path>`
  (`wpgen/main.py`)

- **Fact:** Dependency check:
  - `wpgen check-deps`
  (`wpgen/main.py`)

Configuration:

- **Fact:** Default config path is `config.yaml`, and many commands accept `--config/-c` to override it (`wpgen/main.py`).
- **Fact:** `config.yaml` contains LLM provider settings and explicitly lists provider options: `"openai"`, `"anthropic"`, `"local-lmstudio"`, `"local-ollama"` (`config.yaml`).

## Test and Lint

### Canonical CI gates

- **Fact:** Lint step:
  - `ruff check .`
  (`.github/workflows/ci.yml`)

- **Fact:** Test step:
  - `pytest`
  (`.github/workflows/ci.yml`)

- **Fact:** Tests are intended to be offline and deterministic:
  - The session fixture forces `WPGEN_PROVIDER=mock` and sets `WPGEN_OFFLINE_TESTS=1` by default (`tests/conftest.py`).
  - CI sets `WPGEN_PROVIDER=mock`, `WPGEN_OFFLINE_TESTS=1` (`.github/workflows/ci.yml`).

### Scoped commands for changed files

- **Fact:** Ruff can be run on specific paths:
  - `ruff check path/to/file.py`
  - `ruff check wpgen/`
  - `ruff check tests/`

- **Fact:** Pytest can be scoped:
  - `pytest tests/test_cli_smoke.py`
  - `pytest -k <pattern>`

### Pytest configuration details

- **Fact:** `pytest.ini` sets `testpaths = tests` and defines a marker:
  - `integration: requires network or external APIs`
  (`pytest.ini`)

- **Fact:** `pyproject.toml` also contains pytest ini options under `[tool.pytest.ini_options]` (including `testpaths` and `addopts = -v`) (`pyproject.toml`).
- **Inference (Confidence: Medium, would raise it: a single source of truth for pytest opts):** Having both `pytest.ini` and `[tool.pytest.ini_options]` is a potential source of confusion. Prefer to keep them consistent.

### Ruff and Black requirements (prominent)

- **Fact:** Ruff is configured in `pyproject.toml` with:
  - Target version: `py310`
  - Line length: `100`
  - Lint selects: `E`, `F`, `W`, `I`
  - Tests per-file ignores for `F401`, `F811`
  (`pyproject.toml`)

- **Fact:** Black is configured in `pyproject.toml` with:
  - Target version: `py310`
  - Line length: `100`
  (`pyproject.toml`)

- **Fact:** `requirements-dev.txt` pins `ruff==0.6.9` but does not pin Black (`requirements-dev.txt`).
- **Inference (Confidence: High, would raise it: CI adding a Black step):** Formatting is not currently enforced in CI, but the repo provides Black configuration, suggesting contributors may be expected to format locally.
- **Hypothesis (Confidence: Medium, would raise it: maintainer confirmation or CI update):** Adding an explicit formatting gate (Black or Ruff format) would reduce style drift. If you add it, document the exact command in this file and enforce it in CI.

### Repo hygiene after running tests

- **Fact:** CI sets `PYTHONDONTWRITEBYTECODE=1` to reduce stray `__pycache__` writes (`.github/workflows/ci.yml`).
- **Inference (Confidence: Medium, would raise it: a test asserting clean `git status`):** The project aims to keep test runs from writing artifacts into the repo.
- **Agent rule (see below):** Keep the working tree clean after tests. If a change causes tests to write files, route output to a temp directory or ignore directory already excluded by Ruff (for example `output/` or `logs/`).

## Security and Secrets

Where secrets live:

- **Fact:** `.env.example` documents these secrets and settings:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GITHUB_TOKEN`
  - WordPress REST creds: `WP_SITE_URL`, `WP_USERNAME`, `WP_PASSWORD`, `WP_APP_PASSWORD`
  - Provider override knobs: `WPGEN_LLM_PROVIDER`, `WPGEN_OPENAI_MODEL`, `WPGEN_ANTHROPIC_MODEL`
  (`.env.example`)

- **Fact:** `wpgen init` creates a `.env` file (`README.md`, `wpgen/main.py`).

Redaction and logging:

- **Fact:** Logging includes automatic secret redaction via regex-based patterns (`wpgen/utils/logger.py`).
- **Fact:** Redaction targets patterns such as API keys, tokens, passwords, Authorization Bearer values, GitHub token formats, OpenAI-like key formats, and secret-like URL query parameters (`wpgen/utils/logger.py`).

Rules:

- **Fact:** Do not print or log real secrets in plaintext. Redaction exists but is not a guarantee against all secret leakage (`wpgen/utils/logger.py`).
- **Agent rule:** Never commit `.env`. Use `.env.example` for documenting new variables.

## CI Rules

- **Fact:** CI runs on pushes to `main` and `claude/**`, and on PRs targeting `main` (`.github/workflows/ci.yml`).
- **Fact:** CI steps include:
  - `pip install -e .`
  - `pip install -r requirements-dev.txt`
  - `ruff check .`
  - `pytest`
  (`.github/workflows/ci.yml`)

Commit and PR title rules:

- **Fact:** No Conventional Commits tooling or PR title linting was found in the repo configuration files present in the zip (no commitlint config, no semantic PR workflow, no conventional commits references).
- **Inference (Confidence: Medium, would raise it: a CONTRIBUTING.md or workflow addition):** Commit message format is not enforced by automation in the current repo state.

## Integration Strategy (only what exists in repo)

LLM providers:

- **Fact:** Config supports providers `"openai"`, `"anthropic"`, `"local-lmstudio"`, `"local-ollama"` (`config.yaml`).
- **Fact:** Environment variables exist for provider selection and model overrides (`.env.example`).
- **Fact:** Tests force a mock provider for offline runs (`tests/conftest.py`).

GitHub integration:

- **Fact:** GitHub integration exists and is covered by security-focused tests such as “secure GitHub push without tokens in URLs” (`tests/test_github_push_security.py`).
- **Fact:** GitHub token is expected via `GITHUB_TOKEN` (`.env.example`).

WordPress REST API integration:

- **Fact:** WordPress credentials are defined in `.env.example` and CLI supports `--site-url`, `--username`, `--password` overrides (`.env.example`, `wpgen/main.py`).
- **Fact:** CI imports `wpgen.wordpress.wordpress_api` as a smoke diagnostic (`.github/workflows/ci.yml`).

Web interfaces:

- **Fact:** Flask app exists in `web/app.py`.
- **Fact:** Gradio GUI is a supported interface and is highlighted in the README (`README.md`).

Deployment:

- **Fact:** `deploy.yml` is explicitly described as a template and supports choices `ftp`, `ssh`, `manual`, using GitHub Secrets like `FTP_HOST`, `SSH_PRIVATE_KEY`, etc. (`.github/workflows/deploy.yml`).

## Docs Consistency Rules

- **Fact:** `README.md` documents install paths using extras (`pip install -e .[dev,ui,git,wp]`) and also mentions `wpgen init` and GUI usage.
- **Agent rule:** If you change any of the following, update `README.md` and this file in the same PR:
  - CLI commands or options in `wpgen/main.py`
  - Default config fields in `config.yaml` or schema validations
  - CI gates in `.github/workflows/ci.yml`
  - Required environment variables in `.env.example`
- **Inference (Confidence: Medium, would raise it: consolidation of test configuration):** Keep `pytest.ini` and `[tool.pytest.ini_options]` consistent to avoid “works locally but not in CI” confusion.

## Agent Working Rules

Read before writing:

- **Fact:** The repo has multiple existing documentation and audit summaries (examples: `ISSUES_FOUND.md`, `HARDENING_SUMMARY.md`, `WPGEN_QA_AUDIT_REPORT.md`). They often reflect historical decisions and constraints.
- **Agent rule:** Before making structural changes, scan:
  - `README.md`
  - `.github/workflows/ci.yml`
  - `config.yaml`
  - `tests/` (especially fixtures in `tests/conftest.py`)

No placeholders or truncated code:

- **Agent rule:** Do not leave TODO stubs, placeholder bodies, or “implementation omitted” sections in production code. If a feature is not implemented, fail clearly with a typed exception and a test that asserts the error message.

Update CLAUDE.md when commands/config/structure changes:

- **Agent rule:** Treat this file as the authoritative institutional memory. Any change to commands, config keys, env vars, CI gates, or top-level layout must update this file.

Offline deterministic tests, no real network calls in CI:

- **Fact:** CI and tests enforce mock provider usage (`WPGEN_PROVIDER=mock`) (`.github/workflows/ci.yml`, `tests/conftest.py`).
- **Agent rule:** New tests must be offline and deterministic by default. If a test truly requires network or external APIs, mark it with `@pytest.mark.integration` and ensure CI does not run it by default (or gate it behind explicit opt-in).

Repo hygiene:

- **Fact:** Ruff excludes `output/`, `logs/`, and `web/static/` among others (`pyproject.toml`).
- **Agent rule:** Keep the working tree clean after running `pytest`. Route generated artifacts to excluded output directories (for example `output/`) or temporary directories under pytest fixtures.
- **Inference (Confidence: Medium, would raise it: a test that asserts clean `git status`):** Tests should not modify tracked files. If a change causes tracked files to be rewritten during tests, treat it as a regression and fix it.

Quality gates discipline:

- **Fact:** CI gates are currently `ruff check .` and `pytest` (`.github/workflows/ci.yml`).
- **Agent rule:** Any new Python module must pass Ruff checks and be covered by tests where practical. If you introduce new dependencies, update `requirements.txt` and/or the appropriate extras in `pyproject.toml`, and ensure CI still installs and imports successfully.
