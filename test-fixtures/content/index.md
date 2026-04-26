---
id: index
title: docforge
description: AI-powered CLI tool for automated developer documentation.
sidebar_label: Overview
slug: /
---

# docforge

**docforge** is an AI-powered CLI tool for automated developer documentation.

It extracts context from source code, generates Markdown via Google Gemini,
and scaffolds a Docusaurus site with token-based authentication.
Configurable for any project via `docforge.yaml` with built-in GitHub Pages
deployment and CI/CD integration.

## What docforge does

- scans your source code automatically
- generates structured Markdown documentation
- scaffolds a full Docusaurus site
- supports token-based authentication
- deploys to GitHub Pages
- integrates with CI/CD pipelines

## Quick Start

```bash
pip install docforge
docforge init
docforge generate
docforge build
docforge preview
```

## Minimal Configuration

```yaml
project_name: my-project
source_dir: ./src
output_dir: ./docs
site:
  title: My Project Docs
  locale: en
ai:
  provider: gemini
  model: gemini-1.5-pro
```

## Navigation

Use the sidebar to explore:

- [Getting Started](/getting-started) — install and run docforge
- [Configuration](/configuration) — all available options
- [CLI](/cli/overview) — command reference
- [Guides](/guides/deployment) — deployment and authentication
- [Architecture](/architecture) — internal pipeline overview

:::tip Start here
If this is your first time using docforge, go to [Getting Started](/getting-started).
:::
