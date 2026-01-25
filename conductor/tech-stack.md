# Technology Stack

## Core Technologies
- **Python (3.12+):** Primary language for database management, data processing, exporters, and the modern GUI.
- **Go (1.22+):** Used for performance-critical modules where Python execution is a bottleneck.
- **SQLite:** The primary relational database for storing dictionary data.
- **Web Extensions (Manifest V3):** Built using the **WXT** framework and **Vite** for cross-browser compatibility (Chrome & Firefox) and security.
- **TypeScript:** Primary language for the browser extension, ensuring type safety and maintainability.

## System Dependencies
- **FFmpeg:** Used for audio processing tasks such as trimming and silence detection.

## Libraries and Frameworks
- **SQLAlchemy:** SQL Toolkit and Object-Relational Mapper (ORM) for Python.
- **GORM:** Object-Relational Mapper (ORM) for Go.
- **FastAPI & Uvicorn:** Modern, high-performance web framework and server for building the Webapp API.
- **Prometheus FastAPI Instrumentator:** Exposes performance and memory metrics for real-time monitoring.
- **Flet:** Framework to build interactive multi-platform apps in Python (replaces legacy PySimpleGUI).
- **MCP Python SDK & FastMCP:** Official SDK for implementing Model Context Protocol servers.

## Tooling and Infrastructure
- **Astral uv:** Fast Python package manager and resolver.
- **Ruff:** Extremely fast Python linter and code formatter.
- **CSS Management:** `identity/css/` is the **Single Source of Truth** for all project styles. CSS files are distributed to the Webapp, exporters, and documentation via `tools/css_manager.py`.
- **MkDocs & MkDocs Material:** Documentation generator and theme for project docs.
- **Pytest:** Testing framework for Python.
- **Typst:** New markup-based typesetting system for PDF generation.
