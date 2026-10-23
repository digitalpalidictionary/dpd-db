# scripts/

## Purpose & Rationale
The `scripts/` directory is the automation engine of the project. It exists to provide a clear, standardized set of entry points for common developer tasks, build processes, and maintenance routines. It encapsulates the operational workflows of the project.

## Architectural Logic
Scripts are organized by their **intent** (Action-Oriented):
- **build/:** To create or rebuild project artifacts.
- **export/:** To output the database in specific intermediate formats.
- **fix/:** To perform batch corrections on the database.
- **add/:** To find new data to add.
- **find/:** To search the database and report problems. Read-only.
- **extractor/:** To extract data from source texts, such as the cone and abbreviations.
- **bash/:** The orchestration scripts behind the `just` recipes and the CI workflows.
- **suttas/:** To extract sutta data from the BJT, CST, SC and DPD sources. See [suttas/README.md](suttas/README.md).
- **info/:** To query or report on the project state.
- **tutorial/:** Short examples of how to query the database.
- **patch/:** A stand-alone tool for users who keep an offline copy of Buddha's Words.
- **project_management/:** The GitHub project health check.
- **repo_maintenance/:** Repo upkeep tools.
- **server_contrib/** and **server_dpdict/:** Scripts that run on the servers.
- **onboarding/:** Contributor setup, GUI launch, data submission, and update scripts. See [onboarding/README.md](onboarding/README.md). The web server for contributors is replacing these.

## Relationships & Data Flow
- **Orchestration:** Scripts import logic from **db/**, **exporter/**, and **tools/** to execute high-level workflows.
- **Integration:** They are the primary way the project interacts with CI/CD systems or local development environments.

## Interface
The interface is the CLI. Most scripts are intended to be run from the project root.
Example: `uv run scripts/export/sanskrit_export.py`
