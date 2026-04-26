import os
import platform
import shutil
import subprocess

from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.theme import Theme

custom_theme = Theme({
    "info":      "bold cyan",
    "success":   "bold green",
    "warning":   "bold yellow",
    "error":     "bold red",
    "dim":       "dim white",
    "highlight": "bold white",
})

console = Console(theme=custom_theme)

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
)

_IS_WINDOWS = platform.system() == "Windows"


def _print_step(text):
    console.print("  [dim]›[/] %s" % text)


def _print_success(text):
    console.print("[success]  ✔[/]  %s" % text)


def _print_warning(text):
    console.print("[warning]  ⚠[/]  %s" % text)


def _display_path(path, project_root=None):
    display = str(path)
    if project_root:
        try:
            display = os.path.relpath(str(path), str(project_root))
        except ValueError:
            display = str(path)
    return display.replace("\\", "/")


def _get_npm_exe():
    if _IS_WINDOWS:
        exe = shutil.which("npm.cmd") or shutil.which("npm")
        if not exe and os.path.exists(r"C:\Program Files\nodejs\npm.cmd"):
            exe = r"C:\Program Files\nodejs\npm.cmd"
        return exe
    return shutil.which("npm")


def _run_npm(args, cwd, description="Running npm...", npm_exe=None):
    exe = npm_exe or _get_npm_exe()

    if not exe:
        raise RuntimeError(
            "npm not found in PATH.\n"
            "Run: docforge init  (Node.js will be installed automatically)"
        )

    cmd = [exe] + args

    with Progress(
            TextColumn("  "),
            SpinnerColumn(spinner_name="dots", style="bold green"),
            TextColumn("[bold green]{task.description}[/]"),
            console=console,
            transient=True,
    ) as progress:
        progress.add_task(description, total=None)
        result = subprocess.run(
            cmd,
            cwd=cwd,
            shell=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    if result.returncode != 0:
        console.print(
            "[error]  ✖  npm %s failed (exit code %d):[/]"
            % (" ".join(args), result.returncode)
        )
        error_out = result.stderr or result.stdout or ""
        for line in error_out.splitlines()[-30:]:
            if line.strip():
                console.print("     [dim]%s[/]" % line)
        raise subprocess.CalledProcessError(result.returncode, cmd)


def _write_file(path, content):
    if content.startswith("\ufeff"):
        content = content[1:]
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _write_logo(site_dir, project_root=None):
    img_dir = os.path.join(site_dir, "static", "img")
    os.makedirs(img_dir, exist_ok=True)

    logo_dark = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<defs>'
        '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#EA580C"/>'
        '<stop offset="100%" stop-color="#F59E0B"/>'
        '</linearGradient>'
        '<filter id="glow" x="-30%" y="-30%" width="160%" height="160%">'
        '<feGaussianBlur stdDeviation="1.5" result="blur"/>'
        '<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        '</filter>'
        '</defs>'
        '<path d="M16 2L4 7v9c0 7 5.4 12.4 12 14 6.6-1.6 12-7 12-14V7L16 2z" '
        'fill="url(#g)" filter="url(#glow)"/>'
        '<path d="M11 16h10M11 12h6M11 20h8" stroke="white" '
        'stroke-width="1.75" stroke-linecap="round"/>'
        '</svg>'
    )

    logo_light = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<defs>'
        '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#4f46e5"/>'
        '<stop offset="100%" stop-color="#7c3aed"/>'
        '</linearGradient>'
        '</defs>'
        '<path d="M16 2L4 7v9c0 7 5.4 12.4 12 14 6.6-1.6 12-7 12-14V7L16 2z" '
        'fill="url(#g)"/>'
        '<path d="M11 16h10M11 12h6M11 20h8" stroke="white" '
        'stroke-width="1.75" stroke-linecap="round"/>'
        '</svg>'
    )

    favicon = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<defs>'
        '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#4f46e5"/>'
        '<stop offset="100%" stop-color="#7c3aed"/>'
        '</linearGradient>'
        '</defs>'
        '<rect width="32" height="32" rx="8" fill="url(#g)"/>'
        '<path d="M9 16h14M9 11h9M9 21h12" stroke="white" '
        'stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
    )

    _write_file(os.path.join(img_dir, "logo.svg"), logo_dark)
    _write_file(os.path.join(img_dir, "logo-dark.svg"), logo_light)
    _write_file(os.path.join(img_dir, "favicon.svg"), favicon)

    _print_success("[cyan]%s[/]" % _display_path(os.path.join(img_dir, "logo.svg"), project_root))
    _print_success("[cyan]%s[/]" % _display_path(os.path.join(img_dir, "logo-dark.svg"), project_root))
    _print_success("[cyan]%s[/]" % _display_path(os.path.join(img_dir, "favicon.svg"), project_root))


# ─────────────────────── sync ───────────────────────

def sync_docusaurus_config(project_root, config):
    site_dir = os.path.join(str(project_root), str(config.docusaurus_dir))
    if not os.path.exists(site_dir):
        return

    docusaurus_templates = os.path.join(TEMPLATES_DIR, "docusaurus")
    env = Environment(loader=FileSystemLoader(docusaurus_templates))

    template_vars = {
        "config": config,
        "site":   config.site,
        "auth":   config.auth,
    }

    files_to_sync = {
        "docusaurus.config.ts.j2": "docusaurus.config.ts",
        "sidebars.js.j2": os.path.join("src", "js", "sidebars.js"),
        "package.json.j2": "package.json",
        "ColorModeToggle.tsx.j2": os.path.join("src", "theme", "ColorModeToggle", "index.tsx"),
        "LocaleDropdown.tsx.j2": os.path.join("src", "theme", "LocaleDropdown", "index.tsx"),
        "VersionDropdown.tsx.j2": os.path.join("src", "theme", "VersionDropdown", "index.tsx"),
        "NavbarComponentTypes.tsx.j2": os.path.join("src", "theme", "NavbarItem", "ComponentTypes.tsx"),
        "TOC.tsx.j2": os.path.join("src", "theme", "TOC", "index.tsx"),
    }

    for template_name, output_name in files_to_sync.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        output_path = os.path.join(site_dir, output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        _write_file(output_path, content)

    theme_dir = os.path.join(site_dir, "src", "theme")
    root_tsx_path = os.path.join(theme_dir, "Root.tsx")

    if config.auth.enabled:
        os.makedirs(theme_dir, exist_ok=True)
        template = env.get_template("Root.tsx.j2")
        content = template.render(**template_vars)
        _write_file(root_tsx_path, content)
    elif os.path.exists(root_tsx_path):
        os.remove(root_tsx_path)


# ─────────────────────── init ───────────────────────

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
                         'docusaurus_dir: "docs"\n'
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
                         '# Algolia DocSearch — full-text search for your docs site.\n'
                         '# Apply for free at: https://docsearch.algolia.com/apply\n'
                         '# After approval you will receive appId, apiKey and indexName.\n'
                         '# Use the Search-Only API key here, never the Admin key.\n'
                         '# Leave the defaults to disable search.\n'
                         'algolia_app_id: ""\n'
                         'algolia_api_key: ""\n'
                         'algolia_index_name: ""\n'
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
                         '# Auth: false = public docs, true = token required.\n'
                         '# Generate a token: docforge token <name>\n'
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
                         '  locales: ["en"]\n'
                         '  no_index: false\n'
                         '\n'
                         '  # Documentation versions.\n'
                         '  # These settings must be nested under "site".\n'
                         '  # The dropdown appears in the navbar when at least one version is defined.\n'
                         '  # Mark exactly one version with is_current: true.\n'
                         '  # url can be absolute (https://...) or relative to the docs site.\n'
                         '  # For the current GitHub Pages version, usually use the same value as base_url.\n'
                         '  # Example:\n'
                         '  # versions:\n'
                         '  #   - label: "v2.0"\n'
                         '  #     url: "/<repo>/"\n'
                         '  #     is_current: true\n'
                         '  #   - label: "v1.0"\n'
                         '  #     url: "https://v1.example.com/docs"\n'
                         '  versions:\n'
                         '    - label: "v1.0 (latest)"\n'
                         '      url: "/%s/"\n'
                         '      is_current: true\n'
                     ) % (project_name, project_name, project_name, project_name, project_name)

    _write_file(config_path, config_content)
    _print_success("Created [cyan]docforge.yaml[/]")
    _print_step("Edit it to match your project structure")


def init_docusaurus(project_root, config_path="docforge.yaml", npm_exe=None):
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
        "site":   config.site,
        "auth":   config.auth,
    }

    files_to_render = {
        "docusaurus.config.ts.j2": "docusaurus.config.ts",
        "sidebars.js.j2": os.path.join("src", "js", "sidebars.js"),
        "package.json.j2": "package.json",
        "ColorModeToggle.tsx.j2": os.path.join("src", "theme", "ColorModeToggle", "index.tsx"),
        "LocaleDropdown.tsx.j2": os.path.join("src", "theme", "LocaleDropdown", "index.tsx"),
        "VersionDropdown.tsx.j2": os.path.join("src", "theme", "VersionDropdown", "index.tsx"),
        "NavbarComponentTypes.tsx.j2": os.path.join("src", "theme", "NavbarItem", "ComponentTypes.tsx"),
        "TOC.tsx.j2": os.path.join("src", "theme", "TOC", "index.tsx"),
    }

    for template_name, output_name in files_to_render.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        output_path = os.path.join(site_dir, output_name)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        _write_file(output_path, content)
        _print_success("[cyan]%s[/]" % _display_path(output_path, project_root))

    if config.auth.enabled:
        theme_dir = os.path.join(site_dir, "src", "theme")
        os.makedirs(theme_dir, exist_ok=True)
        template = env.get_template("Root.tsx.j2")
        content = template.render(**template_vars)
        root_tsx_path = os.path.join(theme_dir, "Root.tsx")
        _write_file(root_tsx_path, content)
        _print_success("[cyan]%s[/]" % _display_path(root_tsx_path, project_root))

    css_dir = os.path.join(site_dir, "src", "css")
    os.makedirs(css_dir, exist_ok=True)
    css_src = os.path.join(docusaurus_templates, "custom.css")
    if os.path.exists(css_src):
        shutil.copy2(css_src, os.path.join(css_dir, "custom.css"))
        _print_success("[cyan]%s[/]" % _display_path(os.path.join(css_dir, "custom.css"), project_root))

    css_mod_src = os.path.join(docusaurus_templates, "css")
    if os.path.exists(css_mod_src):
        for item in os.listdir(css_mod_src):
            s = os.path.join(css_mod_src, item)
            d = os.path.join(css_dir, item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
        _print_success("[cyan]%s/[/]" % _display_path(css_dir, project_root))

    _write_logo(site_dir, project_root=project_root)

    content_dir = os.path.join(site_dir, "content")
    os.makedirs(content_dir)

    index_content = (
        "---\n"
        "slug: /\n"
        "sidebar_position: 0\n"
        "---\n\n"
        "# %s\n\n"
        "Documentation will be generated here.\n\n"
        "Run `docforge generate` to create docs.\n"
    ) % config.project_name

    index_path = os.path.join(content_dir, "index.md")
    _write_file(index_path, index_content)
    _print_success("[cyan]%s[/]" % _display_path(index_path, project_root))

    console.print()
    _run_npm(
        ["install"],
        cwd=site_dir,
        description="Installing Docusaurus dependencies...",
        npm_exe=npm_exe,
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
                  '          path: %s/content\n'
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
                  config.docusaurus_dir,
                  config.docusaurus_dir,
                  config.docusaurus_dir,
                  config.docusaurus_dir,
              )

    _write_file(workflow_path, content)
    _print_success("Created [cyan]%s[/]" % _display_path(workflow_path, project_root))
