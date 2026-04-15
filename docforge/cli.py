import hashlib
import os
import platform
import signal
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from docforge import __version__

custom_theme = Theme({
    "info": "bold cyan",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "dim": "dim white",
    "highlight": "bold white",
})

console = Console(theme=custom_theme)

_IS_WINDOWS = platform.system() == "Windows"
_SHELL = _IS_WINDOWS


def _terminate_process(proc):
    if proc is None:
        return
    if _IS_WINDOWS:
        subprocess.call(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except OSError:
            proc.kill()


def _run(cmd, cwd=None):
    kwargs = {"cwd": cwd}
    if not _IS_WINDOWS:
        kwargs["preexec_fn"] = os.setsid

    proc = subprocess.Popen(cmd, **kwargs)
    try:
        proc.wait()
    except KeyboardInterrupt:
        _terminate_process(proc)
        console.print("\n[warning]⚠ Interrupted[/]")
        sys.exit(0)
    return proc.returncode


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


def _print_header(text, emoji=""):
    content = "%s  %s" % (emoji, text) if emoji else text
    console.print(Panel(
        content,
        style="bold blue",
        padding=(0, 2),
    ))


def _print_step(text):
    console.print("  [dim]›[/] %s" % text)


def _print_success(text):
    console.print("[success]  ✔[/]  %s" % text)


def _print_warning(text):
    console.print("[warning]  ⚠[/]  %s" % text)


def _print_error(text):
    console.print("[error]  ✖[/]  %s" % text)


def _print_help():
    console.print(Panel(
        "🔨  docforge — AI-powered documentation generator",
        style="bold blue",
        padding=(0, 2),
    ))
    console.print()
    console.print(
        "  Generates Markdown docs from source code using Gemini AI\n"
        "  and publishes them via Docusaurus to GitHub Pages."
    )
    console.print()
    console.print("  [dim]Usage:[/] docforge [dim]<command>[/] [dim][options][/]")
    console.print()
    console.print("  [dim]Version:[/] [highlight]%s[/]" % __version__)
    console.print("  [dim]Docs:[/]    [cyan]https://github.com/nu1ts/docforge[/]")
    console.print()
    console.rule("[dim]Commands[/]")
    console.print()

    commands = [
        ("init",     "🔨", "Initialize a new docforge project"),
        ("generate", "🤖", "Generate docs from source code using Gemini AI"),
        ("collect",  "📦", "Collect source context into docs/_context/"),
        ("serve",    "🌐", "Start Docusaurus local dev server"),
        ("build",    "🏗️", "Build Docusaurus site for production"),
        ("token",    "🔑", "Generate a new developer access token"),
    ]

    for cmd, emoji, desc in commands:
        console.print(
            "  %s  [cyan]%-10s[/]  [dim]%s[/]" % (emoji, cmd, desc)
        )

    console.print()
    console.print(
        "  Run [cyan]docforge <command> --help[/] for command-specific options."
    )


def _confirm(prompt):
    return click.confirm("  [?] %s" % prompt, default=True)


# ─────────────────────────── CLI ────────────────────────────

class RichGroup(click.Group):
    def format_help(self, ctx, formatter):
        _print_help()


@click.group(cls=RichGroup, invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        _print_help()
        console.print()


@main.command(help="Initialize a new docforge project in the current directory.")
@click.option("--name", default=None, help="Name of the project.")
def init(name):
    _print_header("Initializing docforge", "🔨")
    console.print()

    if name is None:
        name = console.input("  [dim]›[/] Project name: ").strip()
        if not name:
            _print_error("Project name cannot be empty.")
            sys.exit(1)

    console.print()

    root = os.getcwd()

    from docforge.scaffold import (
        init_config,
        init_docusaurus,
        init_github_actions,
    )

    init_config(root, name)

    console.print()
    if _confirm("Initialize Docusaurus site?"):
        init_docusaurus(root)

    console.print()
    if _confirm("Create GitHub Actions workflow?"):
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
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "docforge" not in content:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(additions)
            _print_success("Updated [cyan].gitignore[/]")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
            f.write(additions)
        _print_success("Created [cyan].gitignore[/]")

    console.print()
    console.print(Panel(
        "  [dim]1.[/] Edit [cyan]docforge.yaml[/]\n"
        "  [dim]2.[/] export [cyan]GEMINI_API_KEY[/]='...'\n"
        "  [dim]3.[/] Run [cyan]docforge generate[/]\n"
        "  [dim]4.[/] Run [cyan]docforge serve[/]",
        title="[dim]Next steps[/]",
        border_style="dim",
        padding=(0, 2),
    ))
    console.print()
    _print_success("Initialization complete 🎉")


@main.command(help="Generate documentation using Gemini AI.")
@click.option("--only", default=None, help="Generate only a specific doc by its ID.")
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def generate(only, config):
    _print_header("Generating documentation", "🤖")

    root = find_project_root()

    from docforge.config import ProjectConfig
    from docforge.collector import collect_all
    from docforge.generator import generate_all

    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    console.print()
    console.print("  [info]📦 Collecting context...[/]")
    context = collect_all(cfg, root)

    console.print("  [info]🤖 Generating with [highlight]%s[/]...[/]" % cfg.model)
    count = generate_all(cfg, context, root, only=only)

    console.print()
    _print_success("Generated [highlight]%d[/] document(s)" % count)


@main.command(help="Collect source context and save to docs/_context/.")
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def collect(config):
    _print_header("Collecting context", "📦")

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
        _print_step("Saved [cyan]%s.txt[/]" % name)

    console.print()
    _print_success("Context saved to [cyan]%s[/]" % ctx_dir)


@main.command(help="Start Docusaurus local dev server.")
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def serve(config):
    _print_header("Starting dev server", "🌐")

    root = find_project_root()

    from docforge.config import ProjectConfig
    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    site_dir = os.path.join(str(root), str(cfg.docusaurus_dir))
    if not os.path.exists(site_dir):
        _print_error("Docusaurus not initialized.")
        _print_step("Run: [cyan]docforge init[/]")
        sys.exit(1)

    console.print("  [dim]URL:[/] [cyan]http://localhost:3000[/]")
    console.print("  [dim]Dir:[/] [cyan]%s[/]" % site_dir)
    console.print()

    _run(["npm", "start"], cwd=str(site_dir))


@main.command(help="Build Docusaurus site for production.")
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def build(config):
    _print_header("Building site", "🏗️")

    root = find_project_root()

    from docforge.config import ProjectConfig
    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    site_dir = os.path.join(str(root), str(cfg.docusaurus_dir))
    build_dir = os.path.join(site_dir, "build")

    console.print("  [dim]Dir:[/] [cyan]%s[/]" % site_dir)
    console.print()

    code = _run(["npm", "run", "build"], cwd=str(site_dir))

    if code == 0:
        _print_success("Built to [cyan]%s[/]" % build_dir)
    else:
        _print_error("Build failed (exit code %d)" % code)
        sys.exit(code)


@main.command(help="Generate a new developer access token.")
@click.argument("developer_name")
def token(developer_name):
    _print_header("New Access Token", "🔑")

    raw = "docforge-%s-%s" % (str(developer_name), _generate_token_hex(4))
    hash_hex = hashlib.sha256(raw.encode()).hexdigest()

    console.print()
    _print_step("Developer: [cyan]%s[/]" % developer_name)
    _print_step("Token:     [success]%s[/]" % raw)
    _print_step("SHA-256:   [dim]%s[/]" % hash_hex)

    console.print()
    console.rule("[dim]How to use[/]")
    _print_step("Send token to developer")
    _print_step("Add hash to [cyan]docforge.yaml[/] → [cyan]auth.token_hashes[/]:")
    console.print('     [dim]- "%s"[/]' % hash_hex)
    _print_step("Revoke: remove hash from config and redeploy")
    console.print()


def _generate_token_hex(nbytes):
    random_bytes = os.urandom(nbytes)
    return "".join("%02x" % b for b in bytearray(random_bytes))
