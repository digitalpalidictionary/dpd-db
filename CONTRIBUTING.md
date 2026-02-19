# Contributing to Digital Pāḷi Dictionary

First off, thank you for considering contributing to Digital Pāḷi Dictionary! ❤️

DPD is a freely available, non-commercial Buddhist dictionary project. Every contribution — whether Pāḷi expertise, code, documentation, or a simple bug report — helps make the Dhamma more accessible to practitioners and scholars worldwide. The community looks forward to your contributions. 🙏

> And if you like the project but just don't have time to contribute, that's fine. There are other easy ways to support the project and show your appreciation:
>
> - ⭐ Star the project on GitHub
> - 📢 Tell fellow Pāḷi students and developers about DPD
> - 📖 Use DPD in your own projects and [let us know](mailto:digitalpalidictionary@gmail.com)

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [Ways to Contribute](#ways-to-contribute)
  - [Help with Pāḷi](#help-with-pāḷi)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Features](#suggesting-features)
  - [Contributing Code](#contributing-code)
  - [Improving Documentation](#improving-documentation)
- [Development Setup](#development-setup)
  - [Prerequisites](#prerequisites)
  - [Clone and Install](#clone-and-install)
  - [About Submodules](#about-submodules)
  - [The Database](#the-database)
  - [Running the Webapp](#running-the-webapp)
  - [Go Modules](#go-modules)
  - [Browser Extension](#browser-extension)
- [Your First Code Contribution](#your-first-code-contribution)
- [Pull Request Process](#pull-request-process)
  - [Branching](#branching)
  - [Commit Messages](#commit-messages)
  - [Testing](#testing)
  - [Submitting Your PR](#submitting-your-pr)
- [Project Structure Overview](#project-structure-overview)
- [License](#license)
- [Attribution](#attribution)

## Code of Conduct

This project is rooted in the Buddhist tradition, you will probably dealing with a monk, and we ask that all participants embody the principles of **Right Speech** (*sammā vācā*) and **Right Action** (*sammā kammanta*) in their interactions.

In practice, this means:

- **Be truthful and helpful** — communicate honestly, constructively, and with the intention to benefit others.
- **Be kind and respectful** — disagreements are natural; personal attacks are not. Treat everyone with the same respect you would offer a teacher or fellow student.
- **Be patient** — this is a solo-maintained project. Responses may take time. Your patience is deeply appreciated.
- **Refrain from harmful speech** — avoid harsh language, gossip, or divisive communication.
- **Act with integrity** — contribute in good faith, give credit where it's due, and respect the non-commercial nature of the project.

*Vācaṃ ce munī bhāseyya — "When a sage speaks..."*  
Let our words and actions reflect the Dhamma we study and practice. 🙏

## I Have a Question

> **Please don't use GitHub Issues to ask general questions.** Issues are reserved for bug reports, feature requests, and maintenance tasks.

If you have a question or need help:

1. Check the [DPD Docs website](https://digitalpalidictionary.github.io) — especially the [Technical Docs](https://digitalpalidictionary.github.io/technical/) and [Quick Start Guide](https://digitalpalidictionary.github.io/technical/quick_start/).
2. Search [existing GitHub Issues](https://github.com/digitalpalidictionary/dpd-db/issues) to see if your question has been answered.
3. If you still need help, [email us](mailto:digitalpalidictionary@gmail.com).

For code-related discussions, use [GitHub Discussions](https://github.com/digitalpalidictionary/dpd-db/discussions) or open an issue if it's a concrete technical topic.

## Ways to Contribute

### Help with Pāḷi

The most impactful way to contribute to DPD is through Pāḷi knowledge. You don't need to be a developer!

1. **Add missing words** — If you come across a Pāḷi word not in DPD, [submit it here](https://docs.google.com/forms/d/e/1FAIpQLSfResxEUiRCyFITWPkzoQ2HhHEvUS5fyg68Rl28hFH6vhHlaA/viewform?usp=pp_url&entry.1433863141=dpd-db).
2. **Correct mistakes** — Spotted an error? [Report it here](https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.1433863141=dpd-db).
3. **Add missing details** — Help fill in gaps in existing entries using the [same feedback form](https://docs.google.com/forms/d/e/1FAIpQLSf9boBe7k5tCwq7LdWgBHHGIPVc4ROO5yjVDo1X5LDAxkmGWQ/viewform?usp=pp_url&entry.1433863141=dpd-db).

These Google Forms generate hundreds of community suggestions each month and are the primary way Pāḷi experts contribute. The easiest access is through the **feedback** button in any DPD interface.

For more substantial Pāḷi involvement, [get in touch by email](mailto:digitalpalidictionary@gmail.com).

### Reporting Bugs

If you find a bug in the software (not a Pāḷi data issue — use the forms above for those):

1. Check [existing issues](https://github.com/digitalpalidictionary/dpd-db/issues) to avoid duplicates.
2. [Open a new Bug Report](https://github.com/digitalpalidictionary/dpd-db/issues/new?template=bug_report.md) using the template provided.
3. Include as much detail as possible: steps to reproduce, expected vs. actual behavior, screenshots, your OS and environment.

### Suggesting Features

Have an idea to improve DPD?

1. Check the [DPD Project Board](https://github.com/orgs/digitalpalidictionary/projects/1/views/2) to see if it's already planned.
2. [Open a Feature Request](https://github.com/digitalpalidictionary/dpd-db/issues/new?template=feature_request.md) using the template provided.
3. Describe the problem it solves, your proposed solution, and how it benefits users.


### Contributing Code

Code contributions are very welcome! DPD is a solo-maintained project, and every helping hand makes a real difference.

Contributions can range from:

- **Bug fixes** — squash a bug you've encountered.
- **New features** — implement something from the [project board](https://github.com/orgs/digitalpalidictionary/projects/1/views/2) or your own idea.
- **Exporters** — improve existing dictionary exporters or create new ones.
- **Webapp / Frontend** — improve the [dpdict.net](https://www.dpdict.net/) web interface.
- **Browser extension** — work on the WXT-based cross-browser extension.
- **Documentation** — improve developer docs, this contributing guide, or the docs site.

The best way to get started is to find something that **you** want DPD to do, and make it happen.

### Improving Documentation

Documentation improvements are always welcome and are a great first contribution:

- Fix typos or unclear explanations in the docs.
- Improve the [DPD Docs website](https://digitalpalidictionary.github.io) (built with MkDocs Material).
- Add examples or tutorials to the [Technical Docs](https://digitalpalidictionary.github.io/technical/).

## Development Setup

### Prerequisites

| Tool | Version | Required For | Install |
|------|---------|-------------|---------|
| **Git** | Latest | All contributions | [git-scm.com](https://git-scm.com/) |
| **uv** | Latest | Python dependency management | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Python** | 3.13.x | Backend (auto-managed by uv) | Handled by `uv sync` |
| **Go** | 1.22+ | Go modules only (Deconstructor, Frequency) | [go.dev/dl](https://go.dev/dl/) |
| **Node.js** | LTS (20+) | Browser extension only | [nodejs.org](https://nodejs.org/) |
| **just** | Latest | Task runner (optional but recommended) | [github.com/casey/just](https://github.com/casey/just#installation) |

> [!NOTE]
> You only need **Git** and **uv** to get started. Go and Node.js are only needed if you're working on the specific components listed above.

### Clone and Install

```bash
# Clone the repository (--depth 1 for faster download)
git clone --depth 1 https://github.com/digitalpalidictionary/dpd-db.git
cd dpd-db

# Install minimal dependencies (database + webapp)
uv sync

# Or install ALL development dependencies
uv sync --all-groups
```

### About Submodules

The repository contains several [Git submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules) in the `resources/` directory. **You do NOT need to initialize submodules for most contributions.** They are only required for specific export operations (e.g., SuttaCentral, TPR, audio).

If you do need them for your specific task:

```bash
# Initialize only the submodule you need
git submodule update --init resources/<submodule-name>

# Or initialize all submodules (large download!)
git submodule update --init --recursive
```

Don't let the submodules intimidate you — most development work doesn't require them.

### The Database

The main database (`dpd.db`, ~2.2 GB) is not stored in the repository. You need it if you're working on:

- Database queries or models
- Exporters
- The webapp
- Any script that reads from the database

**To get the database:**

Download the latest `dpd.db.tar.bz2` from the [releases page](https://github.com/digitalpalidictionary/dpd-db/releases), extract it, and place `dpd.db` in the project root.

```bash
# Or download and extract in one step
wget -qO- https://github.com/digitalpalidictionary/dpd-db/releases/latest/download/dpd.db.tar.bz2 | tar -xj
```

For work that doesn't involve the database (e.g., documentation, browser extension, frontend styling), you can skip this step.

See the [Quick Start Guide](https://digitalpalidictionary.github.io/technical/quick_start/) for detailed database usage instructions.

### Running the Webapp

```bash
# Start the dev server
just webapp
# or manually:
uv run uvicorn exporter.webapp.main:app --host 0.0.0.0 --port 8080 --reload --reload-dir exporter/webapp
```

### Go Modules

If you're working on the Go-based Deconstructor or Frequency modules:

1. Install [Go 1.22+](https://go.dev/dl/).
2. The Go code lives in `go_modules/`.
3. Dependencies are managed via `go.mod` in the project root.

### Browser Extension

If you're working on the WXT cross-browser extension:

1. Install [Node.js LTS](https://nodejs.org/) (20+).
2. Navigate to the extension directory and install dependencies:

```bash
cd exporter/wxt_extension
npm install
```

3. For development:

```bash
npm run dev:chrome    # Chrome dev mode
npm run dev:firefox   # Firefox dev mode
```

4. For building:

```bash
npm run build         # Build all browsers
npm run package       # Build + zip all browsers
```

## Your First Code Contribution

New to the project? Here's how to get started:

1. **Browse the [project board](https://github.com/orgs/digitalpalidictionary/projects/1/views/2)** — look for issues that interest you. Issues labelled `good first issue` are specifically chosen as newcomer-friendly.
2. **Comment on an issue** — let us know you'd like to work on it. This avoids duplicate work and lets us give you guidance.
3. **Read the [Technical Docs](https://digitalpalidictionary.github.io/technical/)** — especially the [Quick Start Guide](https://digitalpalidictionary.github.io/technical/quick_start/) and [Project Folder Structure](https://digitalpalidictionary.github.io/technical/project_folder_structure/).
4. **Use AI tools for navigation** — the codebase is large and complex. AI coding assistants are great for tracing dependencies and understanding the architecture.
5. **Ask for help** — don't struggle in silence! [Email us](mailto:digitalpalidictionary@gmail.com) or open a discussion.

> [!TIP]
> **Don't know where to start?** Pick something that _you_ want DPD to do. The best contributions come from contributors solving their own problems.

## Pull Request Process

### Branching

1. [Fork the repository](https://github.com/digitalpalidictionary/dpd-db/fork).
2. Create a branch from `main`:

```bash
git checkout -b your-branch-name
```

3. Name your branch descriptively (e.g., `fix-goldendict-export`, `add-api-endpoint`).

### Commit Messages

Follow this format:

```
#issue-number area-of-code: quick summary of changes
```

**Examples from the project:**

```
#162 gui2: fix error in sandhi find and replace
#122 chrome ext: fix forums blackout & not respecting off
#207 apple dictionary: simplified github workflow for testing
#193 mako 2 jinja: goldendict update
```

**Rules:**
- Start with the issue number (`#123`).
- Follow with the area of the codebase being changed.
- Use a colon, then a lowercase summary of the changes.
- Keep it concise — the issue has the full context.

If there's no related issue, use a descriptive prefix:

```
docs: update contributing guide
refactor: use functools caching lru_cache, cached_property
chore: update submodules
```

### Testing

- **Run the linter** before submitting:

```bash
just lint
# or: uv run ruff check . --exclude archive --exclude resources
```

- **Run the test suite** if your changes touch data logic:

```bash
just test
# or: uv run pytest tests
```

- Tests are expected for **data logic and backend changes**. They are not expected for UI, GUI, or UX changes.
- If you're unsure whether tests are needed, just ask!

### Submitting Your PR

1. Push your branch to your fork.
2. [Open a Pull Request](https://github.com/digitalpalidictionary/dpd-db/compare) against `main`.
3. Fill in the PR template (if one exists) or describe:
   - What changes you made and why.
   - Which issue it relates to (use `Closes #123` or `Relates to #123`).
   - Any testing you've done.
4. All PRs are reviewed personally by the maintainer. Please be patient — this is a solo-maintained project.

## Project Structure Overview

The DPD codebase is organized into the following main areas:

| Directory | Description | Languages |
|-----------|-------------|-----------|
| `db/` | Database models, migrations, and helpers | Python |
| `exporter/` | Dictionary exporters (GoldenDict, Kindle, Apple, PDF, etc.) | Python, HTML, CSS, JS |
| `exporter/webapp/` | The [dpdict.net](https://www.dpdict.net/) web application | Python (FastAPI), HTML, CSS, JS |
| `exporter/wxt_extension/` | Cross-browser extension | TypeScript, HTML, CSS |
| `go_modules/` | Performance-critical modules (Deconstructor, Frequency) | Go |
| `gui2/` | Desktop GUI application | Python (Flet) |
| `scripts/` | Build scripts, data processing, and utilities | Python |
| `tools/` | Shared helper utilities | Python |
| `docs/` | Documentation source (MkDocs Material) | Markdown |
| `resources/` | External data sources (mostly submodules) | Various |
| `tests/` | Test suite | Python (pytest) |

For the full breakdown, see the [Project Folder Structure](https://digitalpalidictionary.github.io/technical/project_folder_structure/) docs.

## License

Digital Pāḷi Dictionary content (dictionary data, Pāḷi analysis) is licensed under [**CC BY-NC-SA 4.0**](http://creativecommons.org/licenses/by-nc-sa/4.0/):

- **BY** — attribute the source
- **NC** — non-commercial use only
- **SA** — share under the same conditions

By contributing, you agree that your contributions will be made available under the same license terms as the rest of the project.


## Attribution

This guide was inspired by the [contributing.md](https://contributing.md/example/) project.