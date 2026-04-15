import os
import platform
import shutil
import subprocess

from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.theme import Theme

custom_theme = Theme({
    "info": "bold cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "dim": "dim white",
    "highlight": "bold white",
})

console = Console(theme=custom_theme)

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
)

_IS_WINDOWS = platform.system() == "Windows"
_SHELL = _IS_WINDOWS


def _print_step(text):
    console.print("  [dim]›[/] %s" % text)


def _print_success(text):
    console.print("[success]  ✔[/]  %s" % text)


def _print_warning(text):
    console.print("[warning]  ⚠[/]  %s" % text)


def _run_npm(args, cwd, description="Running npm..."):
    cmd = ["npm"] + args
    with Progress(
            TextColumn("  "),
            SpinnerColumn(spinner_name="dots", style="bold green"),
            TextColumn("[bold green]{task.description}[/]"),
            console=console,
            transient=True,
    ) as progress:
        progress.add_task(description, total=None)
        result = subprocess.call(
            cmd, cwd=cwd, shell=_SHELL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    if result != 0:
        raise subprocess.CalledProcessError(result, cmd)


def _write_file(path, content):
    if content.startswith("\ufeff"):
        content = content[1:]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def init_config(project_root, project_name):
    config_path = os.path.join(str(project_root), "docforge.yaml")
    if os.path.exists(config_path):
        _print_warning("[cyan]docforge.yaml[/] already exists, skipping")
        return

    config_content = (
                         '# docforge.yaml\n'
                         '# Docs: https://github.com/nu1ts/docforge\n'
                         '\n'
                         'project_name: "%s"\n'
                         'description: ""\n'
                         'model: "gemini-3.1-flash-lite-preview"\n'
                         'output_dir: "docs-site/docs"\n'
                         'docusaurus_dir: "docs-site"\n'
                         '\n'
                         '# Language for generated documentation.\n'
                         '# Supported: english, russian, german, french, spanish, portuguese,\n'
                         '#            chinese, japanese, korean, arabic, italian, dutch,\n'
                         '#            polish, turkish, hindi, ukrainian, czech, swedish\n'
                         '# Tip: for any unlisted language, just type its name (e.g. "finnish").\n'
                         'language: "english"\n'
                         '\n'
                         '# System prompt override (leave empty to use the default).\n'
                         'system_prompt: ""\n'
                         '\n'
                         '# Sources: files that AI will read when generating docs.\n'
                         '#\n'
                         '# Pattern examples by language:\n'
                         '#   Python:     ["**/*.py"]\n'
                         '#   Go:         ["**/*.go"]\n'
                         '#   TypeScript: ["**/*.ts", "**/*.tsx"]\n'
                         '#   Java:       ["**/*.java"]\n'
                         '#   Rust:       ["**/*.rs"]\n'
                         '#   C/C++:      ["**/*.c", "**/*.cpp", "**/*.h"]\n'
                         'sources:\n'
                         '\n'
                         '  - name: source_code\n'
                         '    base_dir: "."\n'
                         '    patterns: ["**/*.py"]   # <- change to your language\n'
                         '    exclude:\n'
                         '      - ".git/"\n'
                         '      - "node_modules/"\n'
                         '      - "__pycache__/"\n'
                         '      - "*.pyc"\n'
                         '      - "dist/"\n'
                         '      - "build/"\n'
                         '    max_chars: 80000\n'
                         '\n'
                         '  - name: configs\n'
                         '    base_dir: "."\n'
                         '    patterns: ["*.toml", "*.yaml", "*.yml", "*.json", "*.ini", "*.cfg"]\n'
                         '    exclude: ["docforge.yaml"]\n'
                         '    max_chars: 10000\n'
                         '\n'
                         '  - name: readme\n'
                         '    base_dir: "."\n'
                         '    patterns: ["README*", "CONTRIBUTING*", "CHANGELOG*"]\n'
                         '    max_chars: 10000\n'
                         '\n'
                         '# Documents to generate.\n'
                         'docs:\n'
                         '\n'
                         '  - id: "overview"\n'
                         '    output: "overview.md"\n'
                         '    title: "Project Overview"\n'
                         '    prompt_template: "overview"\n'
                         '    sources: ["source_code", "readme"]\n'
                         '    sidebar_position: 1\n'
                         '\n'
                         '  - id: "architecture"\n'
                         '    output: "architecture.md"\n'
                         '    title: "Architecture"\n'
                         '    prompt_template: "architecture"\n'
                         '    sources: ["source_code"]\n'
                         '    sidebar_position: 2\n'
                         '\n'
                         '  - id: "setup"\n'
                         '    output: "setup.md"\n'
                         '    title: "Setup & Installation"\n'
                         '    prompt_template: "setup-guide"\n'
                         '    sources: ["configs", "readme"]\n'
                         '    sidebar_position: 3\n'
                         '\n'
                         '# Auth: false = public docs, true = token required\n'
                         '# Generate token: docforge token <name>\n'
                         'auth:\n'
                         '  enabled: false\n'
                         '  method: "token"\n'
                         '  token_hashes: []\n'
                         '\n'
                         '# Site settings (GitHub Pages).\n'
                         'site:\n'
                         '  title: "%s Docs"\n'
                         '  url: "https://YOUR_USER.github.io"\n'
                         '  base_url: "/%s/"\n'
                         '  github_user: "YOUR_USER"\n'
                         '  repo_name: "%s"\n'
                         '  locale: "en"\n'
                         '  no_index: true\n'
                     ) % (project_name, project_name, project_name, project_name)

    _write_file(config_path, config_content)
    _print_success("Created [cyan]%s[/]" % config_path)
    _print_step("Edit it to match your project structure")


def init_docusaurus(project_root, config_path="docforge.yaml"):
    from docforge.config import ProjectConfig
    config = ProjectConfig.from_file(
        os.path.join(str(project_root), str(config_path))
    )

    site_dir = os.path.join(str(project_root), str(config.docusaurus_dir))
    if os.path.exists(site_dir):
        _print_warning("[cyan]%s[/] already exists, skipping" % site_dir)
        return

    os.makedirs(site_dir)

    docusaurus_templates = os.path.join(TEMPLATES_DIR, "docusaurus")
    env = Environment(loader=FileSystemLoader(docusaurus_templates))

    template_vars = {
        "config": config,
        "site": config.site,
        "auth": config.auth,
    }

    files_to_render = {
        "docusaurus.config.ts.j2": "docusaurus.config.ts",
        "sidebars.js.j2": "sidebars.js",
        "package.json.j2": "package.json",
    }

    for template_name, output_name in files_to_render.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        output_path = os.path.join(site_dir, output_name)
        _write_file(output_path, content)
        _print_success("[cyan]%s[/]" % output_path)

    if config.auth.enabled:
        theme_dir = os.path.join(site_dir, "src", "theme")
        os.makedirs(theme_dir)
        template = env.get_template("Root.tsx.j2")
        content = template.render(**template_vars)
        root_tsx_path = os.path.join(theme_dir, "Root.tsx")
        _write_file(root_tsx_path, content)
        _print_success("[cyan]%s[/]" % root_tsx_path)

    css_dir = os.path.join(site_dir, "src", "css")
    os.makedirs(css_dir)
    css_src = os.path.join(docusaurus_templates, "custom.css")
    if os.path.exists(css_src):
        shutil.copy2(css_src, os.path.join(css_dir, "custom.css"))

    docs_dir = os.path.join(site_dir, "docs")
    os.makedirs(docs_dir)

    index_content = (
                        "---\n"
                        "slug: /\n"
                        "sidebar_position: 0\n"
                        "---\n"
                        "\n"
                        "# %s\n"
                        "\n"
                        "Documentation will be generated here.\n"
                        "\n"
                        "Run `docforge generate` to create docs.\n"
                    ) % config.project_name

    index_path = os.path.join(docs_dir, "index.md")
    _write_file(index_path, index_content)
    _print_success("[cyan]%s[/]" % index_path)

    console.print()
    _run_npm(
        ["install"],
        cwd=site_dir,
        description="Installing Docusaurus dependencies...",
    )
    _print_success("Docusaurus initialized in [cyan]%s[/]" % site_dir)


def init_github_actions(project_root, config_path="docforge.yaml"):
    from docforge.config import ProjectConfig
    config = ProjectConfig.from_file(
        os.path.join(str(project_root), str(config_path))
    )

    workflows_dir = os.path.join(str(project_root), ".github", "workflows")
    if not os.path.exists(workflows_dir):
        os.makedirs(workflows_dir)

    workflow_path = os.path.join(workflows_dir, "docs.yml")

    content = (
                  'name: Generate & Deploy Docs\n'
                  '\n'
                  'on:\n'
                  '  push:\n'
                  '    branches: [main]\n'
                  '    paths:\n'
                  '      - "src/**"\n'
                  '      - "docforge.yaml"\n'
                  '  workflow_dispatch:\n'
                  '\n'
                  'permissions:\n'
                  '  contents: read\n'
                  '  pages: write\n'
                  '  id-token: write\n'
                  '\n'
                  'concurrency:\n'
                  '  group: pages\n'
                  '  cancel-in-progress: false\n'
                  '\n'
                  'jobs:\n'
                  '  build-and-deploy:\n'
                  '    runs-on: ubuntu-latest\n'
                  '    environment:\n'
                  '      name: github-pages\n'
                  '      url: ${{ steps.deployment.outputs.page_url }}\n'
                  '\n'
                  '    steps:\n'
                  '      - uses: actions/checkout@v4\n'
                  '\n'
                  '      - name: Cache generated docs\n'
                  '        id: cache\n'
                  '        uses: actions/cache@v4\n'
                  '        with:\n'
                  '          path: %s\n'
                  '          key: docs-${{ hashFiles(\'src/**\', \'docforge.yaml\') }}\n'
                  '\n'
                  '      - name: Setup Python\n'
                  '        if: steps.cache.outputs.cache-hit != \'true\'\n'
                  '        uses: actions/setup-python@v5\n'
                  '        with:\n'
                  '          python-version: "3.12"\n'
                  '\n'
                  '      - name: Install docforge\n'
                  '        if: steps.cache.outputs.cache-hit != \'true\'\n'
                  '        run: pip install docforge\n'
                  '\n'
                  '      - name: Generate docs\n'
                  '        if: steps.cache.outputs.cache-hit != \'true\'\n'
                  '        env:\n'
                  '          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}\n'
                  '        run: docforge generate\n'
                  '\n'
                  '      - uses: actions/setup-node@v4\n'
                  '        with:\n'
                  '          node-version: "20"\n'
                  '          cache: npm\n'
                  '          cache-dependency-path: %s/package-lock.json\n'
                  '\n'
                  '      - name: Build site\n'
                  '        working-directory: %s\n'
                  '        run: |\n'
                  '          npm ci\n'
                  '          npm run build\n'
                  '\n'
                  '      - uses: actions/configure-pages@v4\n'
                  '      - uses: actions/upload-pages-artifact@v3\n'
                  '        with:\n'
                  '          path: %s/build\n'
                  '      - uses: actions/deploy-pages@v4\n'
                  '        id: deployment\n'
              ) % (
                  config.output_dir,
                  config.docusaurus_dir,
                  config.docusaurus_dir,
                  config.docusaurus_dir,
              )

    _write_file(workflow_path, content)
    _print_success("Created [cyan]%s[/]" % workflow_path)
