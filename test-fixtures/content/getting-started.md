---
id: getting-started
title: Getting Started
description: Install docforge and generate your first documentation site in minutes.
sidebar_label: Getting Started
slug: /getting-started
---

# Getting Started

This guide walks you through installing **docforge** and generating your first
documentation site.

## Requirements

- Python 3.10 or later
- Google Gemini API key
- A source code project

## Install

### Using pip

```bash
pip install docforge
```

### Using uv

```bash
uv pip install docforge
```

### Verify

```bash
docforge --version
```

Expected output:

```text
docforge 0.1.0
```

## Set Up Your API Key

docforge uses Google Gemini to generate documentation.

```bash
export GEMINI_API_KEY=your-api-key-here
```

For permanent setup, add this to your shell profile:

```bash
echo 'export GEMINI_API_KEY=your-api-key-here' >> ~/.zshrc
source ~/.zshrc
```

## Initialize a Project

Navigate to your project root and run:

```bash
docforge init
```

This creates a `docforge.yaml` configuration file with sensible defaults.

## Generate Documentation

```bash
docforge generate
```

docforge will:

1. scan your source directory
2. extract context from each file
3. send chunks to Gemini
4. write Markdown to the output directory

## Build the Site

```bash
docforge build
```

This runs the Docusaurus build step and produces a static site.

## Preview Locally

```bash
docforge preview
```

Open your browser and inspect:

- sidebar navigation
- page content spacing
- code block rendering
- dark and light mode

## Next Steps

- Customize your setup with [Configuration](/configuration)
- Learn all commands in the [CLI Reference](/cli/overview)
- Set up [Deployment](/guides/deployment) to GitHub Pages

:::tip First generation
The first run will take longer as docforge scans all files.
Subsequent runs are faster because only changed files are re-processed.
:::
