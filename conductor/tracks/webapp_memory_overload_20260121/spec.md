# Specification: Webapp Critical Memory Overload Investigation & Optimization

## Overview
A critical memory overload issue has emerged in the `dpd-db` webapp within the last 72 hours (approx. Jan 18-21, 2026). The application had been stable for months. The goal is to identify and fix the specific regression, conduct a general memory management audit, and implement observability to prevent future "blind spots."

## Context
- **Status:** Critical Regression.
- **Timeline:** Issue appeared in the last 48 hours.
- **Environment:** Production/Live Server (Linux). Managed by a third party (limited direct access).

## Requirements

### Phase 1: Critical Regression Fix (Priority 1)
1.  **Code Audit:** Analyze `git` commits from the last 48 hours for "suspect" patterns (unclosed sessions, large data loads, loops).
2.  **Remediation:** Isolate the specific commit and implement a patch.

### Phase 2: Memory Management Audit (Priority 2)
1.  **General Audit:** Review global state, `uvicorn` configuration, and caching strategies.
2.  **Optimization:** Implement refactors to reduce baseline memory footprint.

### Phase 3: Observability & Monitoring
1.  **Instrumentation:**
    -   Integrate **Prometheus** metrics into the FastAPI app (e.g., using `prometheus-fastapi-instrumentator`).
    -   Expose a `/metrics` endpoint to allow scraping of memory usage, garbage collection stats, and request counts.
2.  **Visibility:**
    -   Provide a way to query these metrics (exploring the use of a Prometheus MCP server pattern if credentials allow).

## Acceptance Criteria
- [ ] Root cause of the immediate memory spike is identified and fixed.
- [ ] App exposes standard Prometheus metrics at `/metrics`.
- [ ] A report on memory improvements is delivered.
