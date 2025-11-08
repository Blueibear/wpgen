# Stabilize WPGen: imports, deps, config validation, mocked E2E, API hardening

This PR implements a comprehensive fix-and-hardening plan to make WPGen production-ready.

## Summary

- ✅ Fixed blocker import issues preventing Flask web app from starting
- ✅ Added LLM provider factory with clean registry pattern
- ✅ Separated optional dependencies (Gradio) from core requirements
- ✅ Made logger work without colorama (graceful fallback)
- ✅ Added config validation on startup with clear error messages
- ✅ Hardened file handling with security improvements
- ✅ Created mocked E2E test for CI (no API keys needed)
- ✅ Added structured error handling to Flask API
- ✅ Improved GitHub integration with retry/backoff
- ✅ Added comprehensive deployment documentation
- ✅ Added type contracts at API boundaries

## Changes by Priority

### Priority 1: Fix imports/exports (blocker) ✅

**Problem**: `web/app.py` imports from `wpgen` root but symbols not exported

**Solution**: Re-export core components in `wpgen/__init__.py`

- Export `GitHubIntegration`, `PromptParser`, `WordPressGenerator`
- Export `setup_logger`, `get_logger`, `get_llm_provider`
- Maintain lazy-loading for heavy SDK dependencies

### Priority 2: Add LLM provider factory ✅

**Changes**:
- Created `wpgen/llm/factory.py` with provider class registry
- Added `get_provider_class()` for explicit class resolution
- Added `list_providers()` helper for discovery
- Maps provider names to classes: openai, anthropic, local-lmstudio, local-ollama

### Priority 3: Repair requirements.txt ✅

**Changes**:
- Created `requirements-optional.txt` for Gradio UI and extras
- Kept core `requirements.txt` lean
- Documented optional dependencies (Ollama, alternative OCR engines)

### Priority 4: Make colorized logging optional ✅

**Changes**:
- Guard colorama import with try-except
- Create dummy color classes when unavailable
- Logger works in plain mode without colorama
- Prevents import errors in minimal environments

### Priority 5: Config validation + API endpoint ✅

**Changes**:
- Validate `config.yaml` on Flask app startup with Pydantic
- Exit with code 78 (EX_CONFIG) on validation errors
- Added `POST /api/config/validate` endpoint
- Added `GET /version` endpoint
- Show field-level errors with clear messages

### Priority 6: Harden file handling ✅

**Changes**:
- Configurable max upload size (25MB default, via `WPGEN_MAX_UPLOAD_SIZE`)
- Secure temp workspace with path traversal protection
- EXIF orientation fix for images using Pillow
- PDF page limit (50 pages default, via `WPGEN_MAX_PDF_PAGES`)
- Context manager support for automatic cleanup
- Prevent path traversal attacks

### Priority 7: Mocked E2E smoke test ✅

**Changes**:
- Created `MockLLMProvider` with deterministic responses
- Added `tests/test_e2e_mocked.py` for end-to-end testing
- Tests complete pipeline from prompt to theme
- Verifies WordPress theme structure (style.css, functions.php, index.php)
- No API keys required for CI

### Priority 8: Web API error surfaces + CORS ✅

**Changes**:
- Structured error handlers returning `{code, message, details}`
- Handle 400, 404, 500 errors with consistent JSON format
- Catch-all exception handler with traceback in debug mode
- Optional CORS support via flask-cors (config: `web.cors_enabled`)
- Configurable CORS origins (config: `web.cors_origins`)

### Priority 9: GitHub integration reliability ✅

**Changes**:
- Added tenacity for retry logic with exponential backoff
- Created `_api_request_with_retry()` helper
- Retry on 429 (rate limit) and 5xx errors
- Retry on timeout and connection errors
- Max 3 attempts with 2-10 second wait times

### Priority 10: Deployment workflow clarity ✅

**Changes**:
- Created comprehensive `DEPLOYMENT.md` guide
- Documented all deployment methods (GitHub Actions, FTP, SSH, REST API)
- Listed required GitHub secrets for CI/CD
- Provided example workflows and configurations
- Added troubleshooting section for common issues

### Priority 11: Documentation sync ✅

**Changes**:
- Added troubleshooting section to README
- Documented common errors (imports, API keys, timeouts, file uploads)
- Added solutions with code examples
- Cross-referenced deployment guide

### Priority 12: Test suite hygiene ✅

**Changes**:
- Created mocked E2E test that runs without network
- Tests can be extended with `@pytest.mark.integration` for network tests
- Default test suite passes in CI without API keys

### Priority 13: Type contracts at boundaries ✅

**Changes**:
- Created `wpgen/types.py` with TypedDict models
- Defined types: `GenerationRequestDict`, `GenerationResultDict`
- Defined types: `ValidationReportDict`, `GitHubPushResultDict`
- Provides clear contracts for API boundaries

### Priority 14: Observability ✅

**Changes**:
- Structured logging already in place with JSON support
- Error handlers log with full context and exc_info
- Traceback available in debug mode
- Foundation ready for request IDs (can be added incrementally)

## Testing

All changes maintain backward compatibility. The following work without modification:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (including new mocked E2E test)
pytest -v

# Start Flask app
export FLASK_APP=web/app.py
flask run

# CLI usage
python -m wpgen --help
```

## Breaking Changes

None. All changes are additive or improve error handling.

## Migration Guide

No migration needed. Existing deployments continue to work.

### Optional: Enable new features

**Config validation** (recommended):
```yaml
# config.yaml - will be validated on startup
validation:
  enabled: true
  strict: false
```

**CORS for web API** (if needed):
```yaml
web:
  cors_enabled: true
  cors_origins: "https://your-frontend.com"
```

**Adjust file upload limits** (if needed):
```bash
export WPGEN_MAX_UPLOAD_SIZE=52428800  # 50MB
export WPGEN_MAX_PDF_PAGES=100
```

## Verification

- ✅ All imports resolve correctly
- ✅ Flask app starts and validates config
- ✅ Mocked E2E test passes in CI
- ✅ Error responses follow consistent structure
- ✅ GitHub retries work on transient failures
- ✅ File handling respects security limits
- ✅ Documentation comprehensive and accurate

## Related Issues

- Fixes import errors in web app
- Improves CI reliability with mocked tests
- Enhances security in file handling
- Provides better error messages for users

## Next Steps

Future improvements that can build on this foundation:

1. Add request ID tracking (UUID per request)
2. Add Prometheus metrics endpoint
3. Expand mocked test coverage
4. Add integration tests for real LLM providers (behind feature flag)

---

**Commits**: 14 commits implementing 14 priorities
**Files changed**: ~20 files (code, tests, docs)
**Tests**: Added mocked E2E test, all existing tests pass
