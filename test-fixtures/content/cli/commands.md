---
id: commands
title: Command Reference
description: Detailed reference for all docforge CLI commands and their flags.
sidebar_label: Command Reference & Flags
slug: /cli/commands
---

# Command Reference

Full reference for all **docforge** CLI commands.

## `docforge init`

Initializes a new docforge project.

```bash
docforge init
```

### What it creates

```text
docforge.yaml
```

### Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--output` | `./docforge.yaml` | Config file path |
| `--force` | `false` | Overwrite existing config |

### Example

```bash
docforge init --output ./config/docforge.yaml
```

---

## `docforge generate`

Generates Markdown documentation from source code.

```bash
docforge generate
```

### What it does

1. reads `docforge.yaml`
2. scans `source_dir`
3. extracts context per file
4. sends prompts to Gemini
5. writes Markdown to `output_dir`

### Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--config` | `./docforge.yaml` | Config path |
| `--source` | from config | Override source directory |
| `--output` | from config | Override output directory |
| `--verbose` | `false` | Verbose logging |
| `--dry-run` | `false` | Skip file writes |

### Example

```bash
docforge generate --source ./src --output ./docs --verbose
```

---

## `docforge build`

Builds the static Docusaurus site.

```bash
docforge build
```

### What it does

Runs the Docusaurus build step on the generated content directory.

### Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--config` | `./docforge.yaml` | Config path |

---

## `docforge preview`

Serves the site locally for review.

```bash
docforge preview
```

### What it does

Starts a local development server with hot reload.

### Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--port` | `3000` | Local server port |
| `--host` | `localhost` | Bind host |

### Example

```bash
docforge preview --port 4000
```

---

## `docforge deploy`

Deploys the built site to GitHub Pages.

```bash
docforge deploy
```

### Requirements

- `github.user` and `github.repo` set in config
- built site exists in output directory
- write access to the repository

### Flags

| Flag | Default | Description |
| --- | --- | --- |
| `--branch` | from config | Target deployment branch |
| `--message` | auto | Custom commit message |

### Example

```bash
docforge deploy --branch gh-pages --message "docs: update reference"
```

---

## Full CI Example

```bash
docforge generate \
  --source ./src \
  --output ./docs \
  --verbose

docforge build

docforge deploy \
  --branch gh-pages
```
