---
id: architecture
title: Architecture
description: Internal pipeline overview of docforge from source scanning to site deployment.
sidebar_label: Architecture & Internals
slug: /architecture
---

# Architecture

This page describes the internal flow of **docforge**.

## Pipeline Overview

```text
source code
    │
    ▼
file discovery
    │
    ▼
language filtering
    │
    ▼
context extraction
    │
    ▼
prompt construction
    │
    ▼
Gemini API
    │
    ▼
Markdown assembly
    │
    ▼
sidebar scaffolding
    │
    ▼
Docusaurus build
    │
    ▼
static site
    │
    ▼
GitHub Pages
```

## Stage 1 — File Discovery

docforge recursively scans `source_dir` and collects all matching files.

Supported languages:

- Python
- TypeScript
- JavaScript
- Go
- Rust
- Java

## Stage 2 — Context Extraction

For each file, docforge extracts:

- module or package name
- classes and their methods
- standalone functions
- inline comments and docstrings
- imports and dependencies
- file-level structure

## Stage 3 — Prompt Construction

Extracted context is assembled into structured prompts sent to Gemini.

The prompt instructs the model to produce:

- clear section headings
- usage examples
- parameter descriptions
- return value descriptions
- relevant notes and caveats

## Stage 4 — Markdown Assembly

Generated responses are cleaned, validated, and assembled into Markdown pages.

Each page gets:

- frontmatter with `id`, `title`, `description`, `sidebar_label`, `slug`
- structured heading hierarchy
- code blocks with language hints
- internal links where applicable

## Stage 5 — Sidebar Scaffolding

docforge generates a `sidebars.js` file that reflects the structure of the
generated content, including:

- top-level pages
- nested categories based on source directories
- stable IDs derived from file paths

## Stage 6 — Build and Deployment

After generation, docforge optionally runs:

```bash
docforge build
docforge deploy
```

The build step runs Docusaurus. The deploy step pushes to the configured
GitHub Pages branch.

## Design Goals

- generated docs should feel like human-written documentation
- output should be predictable and repeatable in CI
- configuration should be minimal for simple projects
- advanced options should not complicate simple setups

:::note
The pipeline is designed to be stateless. Running `docforge generate` twice
on the same source should produce equivalent output.
:::
