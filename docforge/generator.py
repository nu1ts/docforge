import os
import time

from google import genai
from google.genai import types
from jinja2 import Environment, BaseLoader
from rich.console import Console

console = Console()

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
    "prompts",
)


def _get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY not set.\n"
            "Get one at: https://aistudio.google.com/apikey"
        )
    return genai.Client(api_key=api_key)


def _build_config(config):
    system_prompt = config.system_prompt or (
            "Ты — эксперт-технический писатель. "
            "Проект: %s. "
            "%s "
            "Пиши чётко, структурированно, с примерами кода. "
            "Язык: русский. Формат: чистый Markdown."
            % (config.project_name, config.description)
    )

    return types.GenerateContentConfig(
        system_instruction=system_prompt,
        temperature=0.3,
        max_output_tokens=8192,
    )


def _render_prompt(doc, context, project_root):
    template_name = doc.prompt_template

    local_template = os.path.join(
        str(project_root), "docs", "templates", "%s.md" % template_name
    )
    if os.path.exists(local_template):
        with open(local_template, "r") as f:
            template_str = f.read()

    elif os.path.exists(os.path.join(TEMPLATES_DIR, "%s.md" % template_name)):
        with open(os.path.join(TEMPLATES_DIR, "%s.md" % template_name), "r") as f:
            template_str = f.read()

    else:
        template_str = template_name

    env = Environment(loader=BaseLoader())
    template = env.from_string(template_str)

    variables = dict(context)
    variables.update(doc.extra_context)
    return template.render(**variables)


def generate_doc(doc, context, config, project_root, client, gen_config):
    filtered = {}
    for k, v in context.items():
        if k in doc.sources:
            filtered[k] = v

    prompt = _render_prompt(doc, filtered, project_root)

    console.print("  🤖 Generating [cyan]%s[/]..." % doc.output)

    try:
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=gen_config,
        )
        content = response.text
    except (ValueError, RuntimeError) as e:
        console.print("  ⚠️  Retry: %s" % e)
        time.sleep(5)
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=gen_config,
        )
        content = response.text

    frontmatter = (
            "---\n"
            'title: "%s"\n'
            "sidebar_position: %d\n"
            "generated: true\n"
            'model: "%s"\n'
            "---\n\n"
            % (doc.title, doc.sidebar_position, config.model)
    )

    return frontmatter + content


def generate_all(config, context, project_root, only=None):
    client = _get_client()
    gen_config = _build_config(config)
    output_dir = os.path.join(str(project_root), config.output_dir)

    docs = config.docs
    if only:
        docs = [d for d in docs if d.id == only]
        if not docs:
            available = ", ".join(d.id for d in config.docs)
            console.print("[red]Unknown doc: %s[/]" % only)
            console.print("Available: %s" % available)
            return 0

    success = 0
    for doc in docs:
        try:
            content = generate_doc(
                doc, context, config, project_root, client, gen_config
            )
            out_path = os.path.join(output_dir, doc.output)
            out_dir = os.path.dirname(out_path)
            if not os.path.exists(out_dir):
                os.makedirs(out_dir)
            with open(out_path, "w") as f:
                f.write(content)
            console.print("  ✅ %s" % out_path)
            success += 1
            time.sleep(2)
        except (IOError, OSError, ValueError, RuntimeError) as e:
            console.print("  ❌ %s: %s" % (doc.output, e))

    if not only:
        _generate_index(config, output_dir)

    return success


def _generate_index(config, output_dir):
    lines = [
        "---",
        'title: "%s — Документация"' % config.project_name,
        "sidebar_position: 0",
        "slug: /",
        "---",
        "",
        "# %s" % config.project_name,
        "",
        config.description,
        "",
        "## Разделы",
        "",
        ]

    categories = {}
    for doc in config.docs:
        cat = doc.output.split("/")[0]
        categories.setdefault(cat, []).append(doc)

    for cat, cat_docs in categories.items():
        lines.append("### %s" % cat.replace("-", " ").title())
        lines.append("")
        for d in cat_docs:
            lines.append("- [%s](%s)" % (d.title, d.output))
        lines.append("")

    path = os.path.join(str(output_dir), "index.md")
    if not os.path.exists(str(output_dir)):
        os.makedirs(str(output_dir))
    with open(path, "w") as f:
        f.write("\n".join(lines))
    console.print("  ✅ %s" % path)
