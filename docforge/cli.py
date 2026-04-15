import hashlib
import os
import subprocess

import click
from rich.console import Console
from rich.panel import Panel

from docforge import __version__

console = Console()


def find_project_root():
    current = os.getcwd()
    check = current
    while True:
        if os.path.exists(os.path.join(check, "docforge.yaml")):
            return check
        parent = os.path.dirname(check)
        if parent == check:
            break
        check = parent
    return current


@click.group()
@click.version_option(version=__version__)
def main():
    pass


@main.command()
@click.option(
    "--name", prompt="Project name", help="Name of the project"
)
def init(name):
    console.print(Panel(
        "🔨 Initializing docforge",
        style="bold blue",
    ))

    root = os.getcwd()

    from docforge.scaffold import (
        init_config,
        init_docusaurus,
        init_github_actions,
    )

    init_config(root, name)

    if click.confirm("\nInitialize Docusaurus site?", default=True):
        init_docusaurus(root)

    if click.confirm("Create GitHub Actions workflow?", default=True):
        init_github_actions(root)

    gitignore_path = os.path.join(root, ".gitignore")
    additions = (
        "\n# docforge\n"
        "docs/_context/\n"
        "docs-site/node_modules/\n"
        "docs-site/build/\n"
        "docs-site/.docusaurus/\n"
    )
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
        if "docforge" not in content:
            with open(gitignore_path, "a") as f:
                f.write(additions)
            console.print("✅ Updated .gitignore")
    else:
        with open(gitignore_path, "w") as f:
            f.write(additions)
        console.print("✅ Created .gitignore")

    console.print("\n" + "=" * 50)
    console.print("🎉 Done! Next steps:")
    console.print("  1. Edit [cyan]docforge.yaml[/]")
    console.print("  2. export GEMINI_API_KEY='...'")
    console.print("  3. [cyan]docforge generate[/]")
    console.print("  4. [cyan]docforge serve[/]")


@main.command()
@click.option("--only", default=None, help="Generate specific doc by ID")
@click.option("--config", default="docforge.yaml", help="Config file path")
def generate(only, config):
    console.print(Panel("🤖 Generating documentation", style="bold blue"))

    root = find_project_root()

    from docforge.config import ProjectConfig
    from docforge.collector import collect_all
    from docforge.generator import generate_all

    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    console.print("\n📦 [bold]Collecting context...[/]")
    context = collect_all(cfg, root)

    console.print("\n🤖 [bold]Generating with %s...[/]" % cfg.model)
    count = generate_all(cfg, context, root, only=only)

    console.print("\n✅ Generated %d document(s)" % count)


@main.command()
@click.option("--config", default="docforge.yaml")
def collect(config):
    root = find_project_root()

    from docforge.config import ProjectConfig
    from docforge.collector import collect_all

    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))
    context = collect_all(cfg, root)

    ctx_dir = os.path.join(str(root), "docs", "_context")
    if not os.path.exists(ctx_dir):
        os.makedirs(ctx_dir)
    for name, content in context.items():
        file_path = os.path.join(ctx_dir, "%s.txt" % name)
        with open(file_path, "w") as f:
            f.write(content)

    console.print("\n✅ Context saved to [cyan]%s[/]" % ctx_dir)


@main.command()
@click.option("--config", default="docforge.yaml")
def serve(config):
    root = find_project_root()

    from docforge.config import ProjectConfig
    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    site_dir = os.path.join(str(root), str(cfg.docusaurus_dir))
    if not os.path.exists(site_dir):
        console.print("[red]Docusaurus not initialized.[/]")
        console.print("Run: docforge init")
        return

    console.print("🌐 Starting dev server...")
    subprocess.call(["npm", "start"], cwd=str(site_dir))


@main.command()
@click.option("--config", default="docforge.yaml")
def build(config):
    root = find_project_root()

    from docforge.config import ProjectConfig
    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    site_dir = os.path.join(str(root), str(cfg.docusaurus_dir))
    console.print("🏗️ Building site...")
    subprocess.check_call(["npm", "run", "build"], cwd=str(site_dir))
    console.print("✅ Built to [cyan]%s[/]" % os.path.join(str(site_dir), "build"))


@main.command()
@click.argument("developer_name")
def token(developer_name):
    raw = "docforge-%s-%s" % (str(developer_name), _generate_token_hex(4))
    hash_hex = hashlib.sha256(raw.encode()).hexdigest()

    console.print(Panel("🔑 New Access Token", style="bold green"))
    console.print("  Developer: [cyan]%s[/]" % developer_name)
    console.print("  Token:     [bold green]%s[/]" % raw)
    console.print("  SHA-256:   [dim]%s[/]" % hash_hex)
    console.print("")
    console.print("  1. Send token to developer")
    console.print("  2. Add hash to docforge.yaml → auth.token_hashes:")
    console.print('     - "%s"' % hash_hex)
    console.print("")
    console.print("  Revoke: remove hash from config and redeploy")


def _generate_token_hex(nbytes):
    random_bytes = os.urandom(nbytes)
    return "".join("%02x" % b for b in bytearray(random_bytes))
