# How to Create Skills for KiloCode - DPD Project

This document explains how to create skills for the KiloCode AI agent system in the context of the Digital Pāḷi Dictionary (DPD) project.

## Overview

Skills in KiloCode are modular units of functionality that extend the agents capabilities. Each skill is contained in its own directory with a standardized structure.

## Directory Structure

```
.kilocode/skills/
├── skill-name/
│   └── SKILL.md
├── another-skill/
│   └── SKILL.md
└── HOW_TO_MAKE_SKILLS.md  # This file
```

Each skill must have its own directory with a mandatory `SKILL.md` file containing the skill definition.

## SKILL.md Format

A standard SKILL.md file contains two parts:

1. YAML frontmatter with metadata
2. Markdown content with instructions

### Required Structure:

```markdown
---
name: skill-identifier
description: A concise description of what this skill does
tags: [tag1, tag2]
version: 1.0.0
author: Your Name
dependencies: []
---

# Skill Name

## When to use this skill
Explain when and why to use this skill...

## Instructions
Step-by-step guide on how to perform the task...

## Examples
Concrete examples showing the skill in action...

## Best Practices
Tips and recommendations...
```

## YAML Frontmatter Fields

### Required fields:
- `name`: The skill unique identifier
- `description`: A concise functional description

### Recommended fields:
- `tags`: For categorization and search (e.g., [dpd, database, gui])
- `version`: Semantic versioning
- `author`: Author information
- `license`: Open source license

### Advanced fields:
- `dependencies`: Other skills this skill depends on
- `modes`: Applicable agent modes
- `requires`: External dependencies

## Markdown Content Sections

The markdown content should include:

1. **"When to use this skill"** section - Tells the agent when to activate the skill, using specific verbs and clear use cases
2. **"Instructions"** section - Detailed step-by-step guidance
3. **"Examples"** section - Concrete code examples
4. **"Best Practices"** section - Tips and recommendations

## Creating a New Skill

1. Create a new directory in `.kilocode/skills/` with a descriptive name
2. Inside the directory, create a `SKILL.md` file
3. Follow the format described above
4. Use the existing skills as templates for structure and style

## Example Skill Creation Process

Lets say you want to create a skill for working with DPDs export functionality:

1. Create the directory: `.kilocode/skills/dpd-export-functionality/`
2. Create the file: `.kilocode/skills/dpd-export-functionality/SKILL.md`
3. Fill in the YAML frontmatter and content following the template

## Best Practices for DPD Skills

- Follow the existing code style and patterns used in the DPD codebase
- Use the established modules and helpers (e.g., `get_db_session()` for database operations)
- Include concrete examples that relate to DPDs specific use cases
- Reference the existing DPD file structure and modules
- Ensure examples are executable and tested when possible
- Use appropriate error handling in examples
- Follow the projects type hinting conventions (modern style like `list[str]` not `List[str]`)

