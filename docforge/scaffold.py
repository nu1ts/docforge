import os
import shutil
import subprocess

from jinja2 import Environment, FileSystemLoader
from rich.console import Console

console = Console()

TEMPLATES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "templates",
)


def init_config(project_root, project_name):
    config_path = os.path.join(str(project_root), "docforge.yaml")
    if os.path.exists(config_path):
        console.print("[yellow]docforge.yaml already exists[/]")
        return

    config_content = (
                         '# docforge.yaml — конфигурация генерации документации\n'
                         '# Docs: https://github.com/YOUR_USER/docforge\n'
                         '\n'
                         'project_name: "%s"\n'
                         'description: "Описание проекта"\n'
                         'model: "gemini-2.5-flash"\n'
                         'output_dir: "docs/dev"\n'
                         'docusaurus_dir: "docs-site"\n'
                         '\n'
                         '# ─── Системный промпт для AI ─────────────────────────────────\n'
                         'system_prompt: |\n'
                         '  Ты — эксперт-технический писатель.\n'
                         '  Проект: %s.\n'
                         '  Пиши чётко, структурированно, с примерами кода.\n'
                         '  Язык: русский. Формат: чистый Markdown.\n'
                         '\n'
                         '# ─── Источники контекста ─────────────────────────────────────\n'
                         '# Настройте паттерны под вашу структуру проекта.\n'
                         '# Документация по glob: https://docs.python.org/3/library/glob.html\n'
                         'sources:\n'
                         '\n'
                         '  # Исходный код проекта\n'
                         '  # Замените паттерны под ваш язык:\n'
                         '  #   Python:     ["**/*.py"]\n'
                         '  #   Go:         ["**/*.go"]\n'
                         '  #   TypeScript: ["**/*.ts", "**/*.tsx"]\n'
                         '  #   Java:       ["**/*.java"]\n'
                         '  #   Rust:       ["**/*.rs"]\n'
                         '  - name: source_code\n'
                         '    base_dir: "src"\n'
                         '    patterns: ["**/*"]\n'
                         '    exclude: ["**/__pycache__/**", "**/node_modules/**", "**/*.pyc"]\n'
                         '    max_chars: 80000\n'
                         '\n'
                         '  # Файлы конфигурации в корне проекта\n'
                         '  - name: configs\n'
                         '    base_dir: "."\n'
                         '    patterns: ["*.toml", "*.yaml", "*.yml", "*.json", "*.ini", "*.cfg"]\n'
                         '    exclude: ["docforge.yaml"]\n'
                         '    max_chars: 10000\n'
                         '\n'
                         '  # Структура корневой директории\n'
                         '  - name: structure\n'
                         '    base_dir: "."\n'
                         '    patterns: ["*"]\n'
                         '    exclude: ["*.pyc", ".git"]\n'
                         '    max_chars: 5000\n'
                         '\n'
                         '  # README и документация\n'
                         '  - name: readme\n'
                         '    base_dir: "."\n'
                         '    patterns: ["README*", "CONTRIBUTING*", "CHANGELOG*"]\n'
                         '    max_chars: 10000\n'
                         '\n'
                         '# ─── Документы для генерации ─────────────────────────────────\n'
                         'docs:\n'
                         '\n'
                         '  - id: "architecture/overview"\n'
                         '    output: "architecture/overview.md"\n'
                         '    title: "Архитектура проекта"\n'
                         '    prompt_template: "architecture"\n'
                         '    sources: ["source_code", "structure"]\n'
                         '    sidebar_position: 1\n'
                         '\n'
                         '  - id: "development/setup"\n'
                         '    output: "development/setup.md"\n'
                         '    title: "Настройка среды разработки"\n'
                         '    prompt_template: "setup-guide"\n'
                         '    sources: ["configs", "structure", "readme"]\n'
                         '    sidebar_position: 1\n'
                         '\n'
                         '# ─── Авторизация ─────────────────────────────────────────────\n'
                         'auth:\n'
                         '  enabled: true\n'
                         '  method: "token"\n'
                         '  token_hashes: []\n'
                         '\n'
                         '# ─── Настройки сайта (GitHub Pages) ─────────────────────────\n'
                         'site:\n'
                         '  title: "%s Docs"\n'
                         '  url: "https://YOUR_USER.github.io"\n'
                         '  base_url: "/%s/"\n'
                         '  github_user: "YOUR_USER"\n'
                         '  repo_name: "%s"\n'
                         '  locale: "ru"\n'
                         '  no_index: true\n'
                     ) % (
                         project_name, project_name,
                         project_name, project_name, project_name,
                     )

    with open(config_path, "w") as f:
        f.write(config_content)
    console.print("✅ Created [cyan]%s[/]" % config_path)
    console.print("   Edit it to match your project structure")


def init_docusaurus(project_root, config_path="docforge.yaml"):
    from docforge.config import ProjectConfig
    config = ProjectConfig.from_file(
        os.path.join(str(project_root), str(config_path))
    )

    site_dir = os.path.join(str(project_root), str(config.docusaurus_dir))
    if os.path.exists(site_dir):
        console.print("[yellow]%s already exists[/]" % site_dir)
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
        "sidebars.ts.j2": "sidebars.ts",
        "package.json.j2": "package.json",
    }

    for template_name, output_name in files_to_render.items():
        template = env.get_template(template_name)
        content = template.render(**template_vars)
        output_path = os.path.join(site_dir, output_name)
        with open(output_path, "w") as f:
            f.write(content)
        console.print("  ✅ %s" % output_path)

    if config.auth.enabled:
        theme_dir = os.path.join(site_dir, "src", "theme")
        os.makedirs(theme_dir)
        template = env.get_template("Root.tsx.j2")
        content = template.render(**template_vars)
        root_tsx_path = os.path.join(theme_dir, "Root.tsx")
        with open(root_tsx_path, "w") as f:
            f.write(content)
        console.print("  ✅ %s" % root_tsx_path)

    css_dir = os.path.join(site_dir, "src", "css")
    os.makedirs(css_dir)
    css_src = os.path.join(docusaurus_templates, "custom.css")
    if os.path.exists(css_src):
        shutil.copy2(css_src, os.path.join(css_dir, "custom.css"))

    console.print("\n📦 Installing Docusaurus dependencies...")
    subprocess.check_call(["npm", "install"], cwd=site_dir)

    console.print("\n✅ Docusaurus initialized in [cyan]%s[/]" % site_dir)


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

    with open(workflow_path, "w") as f:
        f.write(content)
    console.print("✅ Created [cyan]%s[/]" % workflow_path)
