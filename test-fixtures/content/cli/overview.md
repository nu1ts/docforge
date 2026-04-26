---
id: overview
title: CLI Overview
description: Overview of the docforge command-line interface and core commands.
sidebar_label: CLI Overview
slug: /cli/overview
---

# CLI Overview

The **docforge** CLI is built around a simple, linear workflow.

## Core Commands

| Command | Description |
| --- | --- |
| `docforge init` | Create a starter configuration |
| `docforge generate` | Generate Markdown from source code |
| `docforge build` | Build the static Docusaurus site |
| `docforge preview` | Serve the site locally |
| `docforge deploy` | Deploy to GitHub Pages |

## Typical Workflow

```bash
# 1. initialize
docforge init

# 2. generate docs
docforge generate

# 3. preview
docforge preview

# 4. build for production
docforge build

# 5. deploy
docforge deploy
```

## Global Flags

### `--config`

Path to the configuration file. Defaults to `./docforge.yaml`.

```bash
docforge generate --config ./custom/docforge.yaml
```

### `--verbose`

Enable verbose logging.

```bash
docforge generate --verbose
```

### `--dry-run`

Run without writing any files. Useful for debugging config issues.

```bash
docforge generate --dry-run
```

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | Configuration error |
| `2` | Generation error |
| `3` | Build error |
| `127` | Command not found |

## Design Principles

### Predictable

Each command does one thing.

### Scriptable

All commands are safe to use in shell scripts and CI pipelines.

### Minimal by Default

Flags are optional. A plain `docforge generate` should work
with just a valid `docforge.yaml`.

:::tip Automation
For CI, combine commands into a single step:

```bash
docforge generate && docforge build && docforge deploy
```
:::
