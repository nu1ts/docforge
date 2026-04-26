---
id: authentication
title: Authentication
description: Protect your docforge documentation with token-based authentication.
sidebar_label: Token-Based Authentication
slug: /guides/authentication
---

# Authentication

docforge supports token-based authentication for protecting documentation portals.

## When to Use Auth

Common use cases:

- internal engineering documentation
- private API references
- staging documentation environments
- documentation for paying customers

## Enable Authentication

```yaml
auth:
  enabled: true
  strategy: token
```

## Set the Token

Use an environment variable to avoid committing secrets:

```bash
export DOCFORGE_AUTH_TOKEN=your-secure-token
```

For CI, add this as a repository secret and reference it in your workflow:

```yaml
- name: Generate docs
  env:
    DOCFORGE_AUTH_TOKEN: ${{ secrets.DOCFORGE_AUTH_TOKEN }}
  run: docforge generate
```

## How Token Auth Works

1. docforge injects auth middleware into the generated site
2. visitors are prompted for a token on first access
3. the token is stored in the browser session
4. protected pages are inaccessible without a valid token

## Token Rotation

To rotate the token:

1. generate a new token
2. update the environment variable or CI secret
3. rebuild and redeploy

## Security Recommendations

- use long, random tokens
- rotate tokens periodically
- never commit tokens to version control
- use HTTPS for all deployments
- combine with private GitHub Pages for stronger access control

:::danger Never commit tokens
Do not put real tokens inside `docforge.yaml`
or any file that is committed to the repository.
:::

## Combining Auth with Deployment

```yaml
auth:
  enabled: true
  strategy: token

github:
  user: your-username
  repo: your-repo
  branch: gh-pages
```

```bash
export DOCFORGE_AUTH_TOKEN=your-secure-token
docforge generate
docforge build
docforge deploy
```