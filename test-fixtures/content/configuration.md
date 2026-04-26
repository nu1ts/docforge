---
id: configuration
title: Configuration
description: Full reference for docforge.yaml configuration options.
sidebar_label: Configuration Reference
slug: /configuration
---

# Configuration

docforge is configured through a `docforge.yaml` file in your project root.

## Minimal Configuration

```yaml
project_name: my-library
source_dir: ./src
output_dir: ./docs
site:
  title: My Library Docs
  locale: en
```

## Full Configuration

```yaml
project_name: docforge
source_dir: ./src
output_dir: ./docs

site:
  title: docforge
  description: AI-powered developer documentation
  url: https://example.github.io
  base_url: /
  locale: en
  locales:
    - en
    - ru
  no_index: false

github:
  user: nu1ts
  repo: docforge
  branch: gh-pages

auth:
  enabled: true
  strategy: token

ai:
  provider: gemini
  model: gemini-1.5-pro
  temperature: 0.2

search:
  provider: local

algolia:
  app_id: YOUR_APP_ID
  api_key: YOUR_SEARCH_API_KEY
  index_name: YOUR_INDEX
```

## Site Options

### `title`

The site title used in the navbar, browser tab, and metadata.

### `description`

Short description used in meta tags and the navbar tagline.

### `url`

Full public URL of the deployed site.

```yaml
site:
  url: https://nu1ts.github.io
```

### `base_url`

Path prefix for the site.

```yaml
site:
  base_url: /docforge/
```

### `locale` and `locales`

Primary locale and all supported locales.

```yaml
site:
  locale: en
  locales:
    - en
    - ru
```

### `no_index`

Set to `true` to prevent search engine indexing.

## AI Options

### `provider`

The AI provider used for documentation generation.

Currently supported:

- `gemini`

### `model`

The model identifier passed to the provider.

Recommended:

```yaml
ai:
  model: gemini-1.5-pro
```

### `temperature`

Controls output creativity. Lower values produce more consistent documentation.

```yaml
ai:
  temperature: 0.2
```

## Search Options

### Local Search

Default option, no external services required.

```yaml
search:
  provider: local
```

### Algolia

For larger projects with full-text search needs.

```yaml
algolia:
  app_id: YOUR_APP_ID
  api_key: YOUR_SEARCH_API_KEY
  index_name: YOUR_INDEX
```

## Auth Options

### Token-Based

```yaml
auth:
  enabled: true
  strategy: token
```

## Best Practices

- keep `source_dir` narrow and specific
- exclude build artifacts and dependencies
- use fixed model versions in CI
- never commit real API keys or tokens

:::warning Secrets
Keep `GEMINI_API_KEY` and auth tokens out of `docforge.yaml`.
Use environment variables instead.
:::
