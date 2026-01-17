# Digital Pāḷi Dictionary (DPD)

## Product Vision
To be the world's most precise, comprehensive, and accessible digital resource for the Pāḷi language. DPD bridges the gap between ancient Tipitaka texts and modern scholars by providing word-by-word grammatical analysis, complex compound deconstruction, and deep etymological insights across every digital platform.

## Target Audience
- **Scholars & Translators:** Requiring high-precision grammatical data and Sanskrit cognates for academic work.
- **Dhamma Practitioners:** Students of Pāḷi looking for contextual meanings and examples from the Suttas.
- **Developers:** Using our open-source data and API to build the next generation of Buddhist study tools (e.g., Tipitaka Pali Reader, Dhamma Gift).

## Core Features & Functionality
- **Word-by-Word Analysis:** Every word in the CST4 Pāḷi corpus is analyzed for its root, case, gender, and construction.
- **Compound Deconstructor:** A sophisticated engine (Python/Go) that breaks down complex Pāḷi compounds into their constituent parts.
- **Mobile-Optimized Webapp:** Responsive design with double-tap-to-lookup, collapsible panels, and touch-optimized interactions for a seamless experience on smartphones.
- **Multi-Format Exporters:** Automated pipelines that generate production-ready dictionary files for GoldenDict, MDict, Kindle, Kobo, and PDF (via Typst).
- **Modern GUI:** A Flet-based interface for lexicographers to add, edit, and verify data with real-time integrity checks.
- **Audio Integration:** Synthesized and recorded Pāḷi pronunciations integrated directly into the lookup experience.
- **Pāḷi MCP Server:** A Model Context Protocol server that enables AI agents to interact with the DPD database for high-precision linguistic analysis.

## AI-Ready Data
DPD is uniquely positioned for the AI era. By providing a structured MCP interface, we enable Large Language Models (LLMs) to perform accurate word-by-word translation and grammatical analysis, reducing hallucinations in Buddhist AI applications.

## Technical Competitive Edge
- **Hybrid Performance:** Using Go for CPU-bound tasks like compound deconstruction while maintaining Python's flexibility for database management.
- **Data Integrity:** Strict SQLAlchemy models and a suite of over 100 automated data-integrity tests ensure the dictionary remains error-free.
- **Platform Agnostic:** We don't just provide a website; we provide the *data* in formats that work offline, in e-readers, and on mobile devices.

## Future Road Map
- **DPD Mobile (Expo):** A full-featured mobile application with "Tap-to-Lookup" capabilities across the OS.
- **Chrome Extension:** Instant Pāḷi lookup for SuttaCentral and other Dhamma websites.
- **AI-Assisted Lexicography:** Integrated AI tools in the GUI to suggest spelling and grammar corrections, identify rare grammatical forms, and suggest literal meanings for verification.