# Implementation Plan: Webapp Critical Memory Overload Investigation & Optimization

## Phase 1: Critical Diagnosis & Fix
- [x] Task: Audit Git Commits from last 72 hours (Jan 18-21, 2026)
    - [x] Use `git log` and `git diff` to identify all changes in `exporter/webapp/` and shared `tools/`.
    - [x] Flags: Look for new global variables, `LRU` caches without limits, or database sessions not being closed.
- [x] Task: Analyze Suspected Code for Resource Leaks
    - [x] Inspect FastAPI dependency injections for session management.
    - [x] Check for heavy file I/O or large JSON/CSV processing introduced recently.
- [x] Task: Create Reproduction/Verification Test
    - [x] Write a script or test case that triggers the suspected code path.
    - [x] Verify failing state (e.g., resource not released or memory spike).
- [x] Task: Implement Fix for Regression
    - [x] Apply the necessary code changes to resolve the identified leak.
    - [x] Verify fix by running the reproduction test.
- [~] Task: Conductor - User Manual Verification 'Critical Diagnosis & Fix' (Protocol in workflow.md)

## Phase 2: General Memory Management Audit
- [ ] Task: Audit Global State and Application Lifecycle
    - [ ] Review all modules loaded at startup in the webapp.
    - [ ] Identify large objects (e.g., dictionary data, frequency maps) and check if they can be loaded on demand or optimized.
- [ ] Task: Evaluate Caching Strategies
    - [ ] Audit `tools/cache_load.py` and other caching mechanisms.
    - [ ] Ensure all caches have appropriate size limits or TTLs.
- [ ] Task: Review Server (Uvicorn) Configuration
    - [ ] Analyze the current startup command for the webapp.
    - [ ] Recommend `uvicorn` flags (e.g., `--limit-max-requests`, `--timeout-keep-alive`) to improve stability.
- [ ] Task: Conductor - User Manual Verification 'General Memory Management Audit' (Protocol in workflow.md)

## Phase 3: Observability & Hardening
- [ ] Task: Instrument Webapp with Prometheus
    - [ ] Add `prometheus-fastapi-instrumentator` to dependencies.
    - [ ] Initialize instrumentation in `exporter/webapp/main.py` (or equivalent entry point).
    - [ ] Verify `/metrics` endpoint exposes GC and process memory stats.
- [ ] Task: Explore Prometheus Integration
    - [ ] Investigate if the AWS Prometheus MCP code can be adapted or if a simple local Prometheus instance is needed for the "other person" to scrape.
- [ ] Task: Final System Verification
    - [ ] Execute all webapp-related tests to ensure no functional regressions.
    - [ ] Verify that memory usage is stable under simulated load.
- [ ] Task: Conductor - User Manual Verification 'Observability & Hardening' (Protocol in workflow.md)
