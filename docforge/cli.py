import hashlib
import os
import platform
import shutil
import subprocess
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.theme import Theme

from docforge import __version__

custom_theme = Theme({
    "info":      "bold cyan",
    "success":   "bold green",
    "warning":   "bold yellow",
    "error":     "bold red",
    "dim":       "dim white",
    "highlight": "bold white",
})

console = Console(theme=custom_theme)

_IS_WINDOWS = platform.system() == "Windows"

_COMMAND_META = {
    "init": (
        "🔨 ",
        "Initialize a new docforge project in the current directory.",
        "docforge init [--name NAME]",
        [
            ("--name NAME", "Name of the project (prompted if omitted)."),
            ("--help",      "Show this message and exit."),
        ],
        [],
    ),
    "generate": (
        "🤖 ",
        "Generate documentation from source code using Gemini AI.",
        "docforge generate [--only ID] [--config FILE]",
        [
            ("--only ID",     "Generate only a specific doc by its ID."),
            ("--config FILE", "Path to config file.  [default: docforge.yaml]"),
            ("--help",        "Show this message and exit."),
        ],
        [],
    ),
    "collect": (
        "📦 ",
        "Collect source context and save to docs/_context/.",
        "docforge collect [--config FILE]",
        [
            ("--config FILE", "Path to config file.  [default: docforge.yaml]"),
            ("--help",        "Show this message and exit."),
        ],
        [],
    ),
    "serve": (
        "🌐 ",
        "Start Docusaurus local dev server at http://localhost:3000",
        "docforge serve [--config FILE]",
        [
            ("--config FILE", "Path to config file.  [default: docforge.yaml]"),
            ("--help",        "Show this message and exit."),
        ],
        [],
    ),
    "build": (
        "🏗️ ",
        "Build Docusaurus site for production.",
        "docforge build [--config FILE]",
        [
            ("--config FILE", "Path to config file.  [default: docforge.yaml]"),
            ("--help",        "Show this message and exit."),
        ],
        [],
    ),
    "token": (
        "🔑 ",
        "Generate a new developer access token and print its SHA-256 hash.",
        "docforge token DEVELOPER_NAME",
        [
            ("--help", "Show this message and exit."),
        ],
        [
            ("DEVELOPER_NAME", "Name of the developer to associate with the token."),
        ],
    ),
}


def _print_command_help(name):
    if name not in _COMMAND_META:
        return

    emoji, desc, usage, options, args = _COMMAND_META[name]

    console.print(Panel(
        "%s docforge %s" % (emoji, name),
        style="bold blue",
        padding=(0, 2),
    ))
    console.print()
    console.print("  %s" % desc)
    console.print()
    console.print("  [dim]Usage:[/] [cyan]%s[/]" % usage)

    if args:
        console.print()
        console.rule("[dim]Arguments[/]")
        console.print()
        for arg, arg_desc in args:
            console.print("  [cyan]%-20s[/]  [dim]%s[/]" % (arg, arg_desc))

    console.print()
    console.rule("[dim]Options[/]")
    console.print()
    for opt, opt_desc in options:
        console.print("  [cyan]%-20s[/]  [dim]%s[/]" % (opt, opt_desc))

    console.print()


# ─────────────────────── executable resolution ───────────────────────

def _get_node_exe():
    try:
        from docforge.deps import _get_node_exe as _deps_get_node
        return _deps_get_node()
    except Exception:
        return shutil.which("node")


def _get_npm_exe():
    try:
        from docforge.deps import _get_npm_exe as _deps_get_npm
        return _deps_get_npm()
    except Exception:
        if _IS_WINDOWS:
            exe = shutil.which("npm.cmd") or shutil.which("npm")
            if not exe and os.path.exists(r"C:\Program Files\nodejs\npm.cmd"):
                return r"C:\Program Files\nodejs\npm.cmd"
            return exe
        return shutil.which("npm")


def _ensure_node_in_path():
    if not _IS_WINDOWS:
        return
    try:
        from docforge.deps import (
            _refresh_path_windows,
            _ensure_node_tools_in_path_windows,
        )
        _refresh_path_windows()
        _ensure_node_tools_in_path_windows()
    except Exception:
        pass


def _find_docusaurus_cli(site_dir):
    candidates = [
        os.path.join(site_dir, "node_modules", "@docusaurus", "core", "bin", "docusaurus.mjs"),
        os.path.join(site_dir, "node_modules", "@docusaurus", "core", "bin", "docusaurus.js"),
        os.path.join(site_dir, "node_modules", "@docusaurus", "core", "bin", "docusaurus.cjs"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def _get_docusaurus_cmd(site_dir, action):
    node = _get_node_exe()
    cli = _find_docusaurus_cli(site_dir)

    if node and cli:
        return [node, cli, action]

    npm = _get_npm_exe()
    if not npm:
        console.print()
        raise RuntimeError(
            "Neither node nor npm found in PATH.\n"
            "  Install Node.js from: https://nodejs.org\n"
            "  After installation restart your IDE completely."
        )

    if action == "start":
        return [npm, "start"]
    if action == "build":
        return [npm, "run", "build"]

    raise ValueError("Unknown Docusaurus action: %s" % action)


# ─────────────────────── subprocess helpers ───────────────────────

def _run(cmd, cwd=None):
    proc = subprocess.Popen(cmd, cwd=cwd)

    try:
        return proc.wait()
    except KeyboardInterrupt:
        console.print("\n[warning]⚠ Stopping the process...[/]")

        try:
            return proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass

        if _IS_WINDOWS:
            subprocess.call(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            proc.terminate()
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()

        sys.exit(0)


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


# ─────────────────────── rich helpers ───────────────────────

def _print_header(text, emoji=""):
    content = "%s  %s" % (emoji, text) if emoji else text
    console.print(Panel(content, style="bold blue", padding=(0, 2)))


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
        ("init",     "🔨 ", "Initialize a new docforge project"),
        ("generate", "🤖 ", "Generate docs from source code using Gemini AI"),
        ("collect",  "📦 ", "Collect source context into docs/_context/"),
        ("serve",    "🌐 ", "Start Docusaurus local dev server"),
        ("build",    "🏗️",  "Build Docusaurus site for production"),
        ("token",    "🔑 ", "Generate a new developer access token"),
    ]

    for cmd, emoji, desc in commands:
        console.print("  %s  [cyan]%-10s[/]  [dim]%s[/]" % (emoji, cmd, desc))

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


class RichCommand(click.Command):
    def format_help(self, ctx, formatter):
        _print_command_help(self.name)


@click.group(cls=RichGroup, invoke_without_command=True)
@click.version_option(version=__version__)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        _print_help()
        console.print()


# ── init ──────────────────────────────────────────────────────────────

@main.command(cls=RichCommand)
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
        from docforge.deps import check_and_install_all
        deps = check_and_install_all(need_node=True, need_git=False)
        npm_exe = deps.get("npm")
        init_docusaurus(root, npm_exe=npm_exe)

    console.print()
    if _confirm("Create GitHub Actions workflow?"):
        from docforge.deps import ensure_git
        ensure_git()
        init_github_actions(root)

    gitignore_path = os.path.join(root, ".gitignore")
    additions = (
        "\n# docforge\n"
        "docs/node_modules/\n"
        "docs/build/\n"
        "docs/.docusaurus/\n"
        "docs/_context/\n"
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
        "  [dim]2.[/] Set [cyan]GEMINI_API_KEY[/]='...'\n"
        "  [dim]3.[/] Run [cyan]docforge generate[/]\n"
        "  [dim]4.[/] Run [cyan]docforge serve[/]",
        title="[dim]Next steps[/]",
        border_style="dim",
        padding=(0, 2),
    ))
    console.print()
    _print_success("Initialization complete 🎉")


# ── generate ──────────────────────────────────────────────────────────

@main.command(cls=RichCommand)
@click.option("--only",   default=None,           help="Generate only a specific doc by its ID.")
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


# ── collect ───────────────────────────────────────────────────────────

@main.command(cls=RichCommand)
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def collect(config):
    _print_header("Collecting context", "📦")

    root = find_project_root()

    from docforge.config import ProjectConfig
    from docforge.collector import collect_all

    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))
    context = collect_all(cfg, root)

    ctx_dir = os.path.join(str(root), str(cfg.docusaurus_dir), "_context")
    if not os.path.exists(ctx_dir):
        os.makedirs(ctx_dir)

    for name, content in context.items():
        file_path = os.path.join(ctx_dir, "%s.txt" % name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        _print_step("Saved [cyan]%s.txt[/]" % name)

    console.print()
    _print_success("Context saved to [cyan]%s[/]" % ctx_dir)


# ── serve ─────────────────────────────────────────────────────────────

@main.command(cls=RichCommand)
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def serve(config):
    _print_header("Starting dev server", "🌐")

    _ensure_node_in_path()

    root = find_project_root()

    from docforge.config import ProjectConfig
    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    site_dir = os.path.join(str(root), str(cfg.docusaurus_dir))
    if not os.path.exists(site_dir):
        _print_error("Docusaurus not initialized.")
        _print_step("Run: [cyan]docforge init[/]")
        sys.exit(1)

    node_modules = os.path.join(site_dir, "node_modules")
    if not os.path.exists(node_modules):
        _print_warning("node_modules not found — running npm install first...")
        from docforge.scaffold import _run_npm
        _run_npm(["install"], cwd=site_dir, description="Installing dependencies...")

    try:
        cmd = _get_docusaurus_cmd(str(site_dir), "start")
    except RuntimeError as exc:
        _print_error(str(exc))
        sys.exit(1)

    console.print("  [dim]URL:[/] [cyan]http://localhost:3000[/]")
    console.print("  [dim]Dir:[/] [cyan]%s[/]" % site_dir)
    console.print()

    _run(cmd, cwd=str(site_dir))


# ── build ─────────────────────────────────────────────────────────────

@main.command(cls=RichCommand)
@click.option("--config", default="docforge.yaml", help="Path to config file.")
def build(config):
    _print_header("Building site", "🏗️")

    _ensure_node_in_path()

    root = find_project_root()

    from docforge.config import ProjectConfig
    cfg = ProjectConfig.from_file(os.path.join(str(root), str(config)))

    site_dir = os.path.join(str(root), str(cfg.docusaurus_dir))
    build_dir = os.path.join(site_dir, "build")

    node_modules = os.path.join(site_dir, "node_modules")
    if not os.path.exists(node_modules):
        _print_warning("node_modules not found — running npm install first...")
        from docforge.scaffold import _run_npm
        _run_npm(["install"], cwd=site_dir, description="Installing dependencies...")

    try:
        cmd = _get_docusaurus_cmd(str(site_dir), "build")
    except RuntimeError as exc:
        _print_error(str(exc))
        sys.exit(1)

    console.print("  [dim]Dir:[/] [cyan]%s[/]" % site_dir)
    console.print()

    code = _run(cmd, cwd=str(site_dir))

    if code == 0:
        _print_success("Built to [cyan]%s[/]" % build_dir)
    else:
        _print_error("Build failed (exit code %d)" % code)
        sys.exit(code)


# ── token ─────────────────────────────────────────────────────────────

@main.command(cls=RichCommand)
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
