---
id: deployment
title: Deployment
description: Deploy docforge documentation to GitHub Pages with built-in CI/CD support.
sidebar_label: Deployment to GitHub Pages
slug: /guides/deployment
---

# Deployment

docforge has built-in support for deploying to **GitHub Pages**.

## Configuration

Add deployment settings to `docforge.yaml`:

```yaml
github:
  user: your-github-username
  repo: your-repo-name
  branch: gh-pages
```

## Deploy Command

```bash
docforge deploy
```

## Custom Domain

To use a custom domain, add:

```yaml
site:
  url: https://docs.yourdomain.com
  base_url: /
```

Then configure DNS and enable custom domain in GitHub Pages settings.

## CI/CD with GitHub Actions

### Minimal Workflow

```yaml
name: Deploy Docs

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install docforge
        run: pip install docforge

      - name: Generate docs
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: docforge generate

      - name: Build site
        run: docforge build

      - name: Deploy to GitHub Pages
        run: docforge deploy
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Troubleshooting

### Blank page after deploy

Check these settings:

```yaml
site:
  url: https://your-user.github.io
  base_url: /your-repo/
```

### Assets not loading

The `base_url` must match the repository name when using the default
GitHub Pages subdomain.

### Deployment fails in CI

Make sure `GITHUB_TOKEN` and `GEMINI_API_KEY` are set as repository secrets.

:::warning Branch protection
If your default branch has protection rules,
make sure the GitHub Actions workflow has write permissions.
:::
