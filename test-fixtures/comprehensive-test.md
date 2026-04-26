# Comprehensive Markdown + Docusaurus Admonitions Test Fixture

> This document is designed to exercise **GitHub Flavored Markdown (GFM)** features and **Docusaurus admonitions** in one place.

---

## 1. Headings

# H1 Title
## H2 Section
### H3 Subsection
#### H4 Level
##### H5 Level
###### H6 Level

---

## 2. Paragraphs, Line Breaks, and Escaping

This is a normal paragraph with **bold**, *italic*, and ***bold italic*** text.  
This line ends with two spaces to force a line break.

Use backslash escapes for special chars: \* \_ \` \# \[ \].

---

## 3. Blockquotes

> Basic quote.
>
> > Nested quote level 2.
> >
> > > Nested quote level 3.

> [!NOTE]
> GitHub-style callout syntax may render on GitHub, but Docusaurus admonitions are tested below using `:::type`.

---

## 4. Lists

### Unordered

- Item A
- Item B
  - Nested B.1
  - Nested B.2
    - Deep B.2.a

### Ordered

1. First
2. Second
   1. Second.1
   2. Second.2
3. Third

### Mixed

1. Ordered starts
   - Unordered child
   - Another child
2. Ordered continues

---

## 5. Task Lists (GFM)

- [x] Completed task
- [ ] Pending task
- [x] Task with `inline code`
  - [ ] Nested pending subtask
  - [x] Nested completed subtask

---

## 6. Links and Autolinks

- Inline link: [Docusaurus](https://docusaurus.io/)
- Reference link: [GitHub Docs][gh-docs]
- URL autolink: https://github.com
- Email autolink: [example@example.com](mailto:example@example.com)

[gh-docs]: https://docs.github.com/

---

## 7. Images

![Sample SVG logo](/img/logo.svg "Docforge Logo")

---

## 8. Inline Code and Fenced Code Blocks

Inline code example: `print("hello")`.

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("Markdown"))
```

```bash
# Shell example
echo "Testing fenced code blocks"
```

```json
{
  "name": "docforge-test",
  "enabled": true,
  "features": ["gfm", "admonitions", "tables"]
}
```

```diff
- old line
+ new line
```

---

## 9. Tables (GFM)

| Feature        | Supported | Notes                             |
|----------------|-----------|-----------------------------------|
| Tables         | Yes       | Pipe syntax with alignment        |
| Task Lists     | Yes       | `- [x]` / `- [ ]`                 |
| Strikethrough  | Yes       | `~~text~~`                        |
| Footnotes      | Yes*      | Depends on parser configuration   |

Alignment test:

| Left | Center | Right |
|:-----|:------:|------:|
| L1   |   C1   |    R1 |
| L2   |   C2   |    R2 |

---

## 10. Horizontal Rules

---
***
___

---

## 11. Strikethrough and Highlight-ish Patterns

This text is ~~removed~~ and this text is still valid.

`==Highlight==` is shown as plain text in many parsers unless extra plugins are enabled.

---

## 12. Footnotes (GFM)

Here is a statement with a footnote reference.[^1]  
Here is another reference to the same footnote.[^1]  
And a second footnote.[^long-note]

[^1]: This is the first footnote.
[^long-note]: This is a longer footnote that can contain **formatting**, links like [GitHub](https://github.com), and `inline code`.

---

## 13. Definition-like Pattern (Plain Markdown Fallback)

Term
: Definition style syntax may require parser support (not universal in GFM).

---

## 14. Collapsible Details (HTML in Markdown)

<details>
  <summary>Click to expand details block</summary>

This content is hidden by default.

- It can include lists
- **Formatting**
- `code`

```ts
const expanded = true;
console.log("Details opened:", expanded);
```

</details>

---

## 15. Raw HTML

<div align="center">
  <strong>Raw HTML block</strong><br />
  <em>Used for parser compatibility testing.</em>
</div>

<table>
  <tr><th>HTML Table</th><th>Status</th></tr>
  <tr><td>Allowed in many Markdown engines</td><td>Varies</td></tr>
</table>

---

## 16. Emoji and Entities

- Emoji shortcode style (platform-dependent): :rocket: :warning: :sparkles:
- Unicode emoji: 🚀 ⚠️ ✨
- HTML entities: &copy; &amp; &lt; &gt;

---

## 17. Escaped and Literal Markdown

\# Not a heading  
\* Not emphasized \*  
\`Not code\`

---

## 18. Docusaurus Admonitions

:::note
This is a **note** admonition.
:::

:::tip
This is a **tip** admonition with a list:

- Keep docs short
- Add examples
- Validate output
:::

:::info
This is an **info** admonition with `inline code` and a [link](https://docusaurus.io/docs/markdown-features/admonitions).
:::

:::warning
This is a **warning** admonition.
Be careful with parser-specific syntax differences.
:::

:::danger
This is a **danger** admonition.
Use in production docs only for critical notices.
:::

### 18.1 Admonition with Custom Title

:::note Custom Title
You can provide a custom title after the admonition type.
:::

### 18.2 Nested Content in Admonition

:::tip Advanced Tip
1. Step one
2. Step two
3. Step three

```yaml
admonition:
  type: tip
  title: Advanced Tip
```
:::

---

## 19. Mixed Stress Test Section

> Combine multiple features together:

1. Ordered item with footnote reference[^combo]
2. Ordered item with task list:
   - [x] done
   - [ ] pending
3. Ordered item with table:

| Key | Value |
|-----|-------|
| A   | 1     |
| B   | 2     |

:::warning Mixed Block
Inside this admonition we use:

- **bold**
- `code`
- [link](https://example.com)
:::

[^combo]: Combo footnote used in a mixed-content section.

---

## 20. Final Checklist

- [x] Headings
- [x] Lists
- [x] Task lists
- [x] Links and references
- [x] Images
- [x] Code fences
- [x] Tables
- [x] Footnotes
- [x] HTML blocks
- [x] Docusaurus admonitions

End of fixture.
