# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-07-09

### Added
- Created a shared `utils.py` module to consolidate common functions.
- Externalized all AI prompts into a `prompts.json` file for easier management and customization.
- Added a `sanitizeHTML` function to the frontend to mitigate XSS vulnerabilities.
- Added `requests-mock` to the test dependencies to enable network-independent testing.
- Added this `CHANGELOG.md` file to track project changes.

### Changed
- Refactored `main.py` and `analyze_company.py` to import shared functions from `utils.py`, reducing code duplication.
- Updated AI prompts in `prompts.json` to be more explicit and include detailed JSON schemas, improving the reliability of model responses.
- Replaced fragile regex-based JSON parsing with direct `json.loads()` calls for more robust error handling.
- Standardized the default `GEMINI_MODEL` to `gemini-2.5-pro` across all configuration files (`.env.example`, `main.py`, `deploy.sh`).
- Refactored the frontend by moving all embedded JavaScript from `templates/index.html` to a separate `static/js/main.js` file.
- Updated the test suite in `test_local.py` to patch `google.generativeai` instead of the outdated `vertexai`.
- Made the URL extraction test independent of the network by using `requests-mock`.
- Updated all repository URLs in `README.md` from `hr-agent` to `candidate-scorer`.

### Fixed
- Resolved inconsistent scoring for the same resume by setting the Gemini API `temperature` to `0.0` for deterministic outputs.
- Corrected an issue where the company analysis was failing silently due to an overly generic prompt.
- Fixed a bug where the score breakdown and assessment sections would display "undefined/10" or "None specified" due to incomplete JSON responses from the AI.
- Addressed a potential Server-Side Request Forgery (SSRF) vulnerability by adding validation to the `extract_text_from_url` function.

### Removed
- Deleted the `ANALYSIS.md` file, as all its findings have been addressed.
- Removed duplicated functions from `main.py` and `analyze_company.py`.
