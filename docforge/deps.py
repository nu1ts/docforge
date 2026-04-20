import os
import platform
import shutil
import subprocess
import sys
import urllib.request
import tempfile

from rich.console import Console
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

_IS_WINDOWS = platform.system() == "Windows"
_IS_MACOS = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"


# ─────────────────────── helpers ───────────────────────

def _print_step(text):
    console.print("  [dim]›[/] %s" % text)


def _print_success(text):
    console.print("[success]  ✔[/]  %s" % text)


def _print_warning(text):
    console.print("[warning]  ⚠[/]  %s" % text)


def _print_error(text):
    console.print("[error]  ✖[/]  %s" % text)


def _run_silent(cmd):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "not found"


def _confirm(prompt):
    try:
        answer = input("  [?] %s [Y/n]: " % prompt).strip().lower()
        return answer in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


# ─────────────────────── node / npm ───────────────────────

def _get_node_exe():
    return shutil.which("node")


def _get_npm_exe():
    if _IS_WINDOWS:
        return shutil.which("npm.cmd") or shutil.which("npm")
    return shutil.which("npm")


def _node_version():
    exe = _get_node_exe()
    if not exe:
        return None
    code, out, _ = _run_silent([exe, "--version"])
    return out.strip() if code == 0 else None


def _npm_version():
    exe = _get_npm_exe()
    if not exe:
        return None
    code, out, _ = _run_silent([exe, "--version"])
    return out.strip() if code == 0 else None


def _install_node_windows():
    url = "https://nodejs.org/dist/v20.14.0/node-v20.14.0-x64.msi"
    _print_step("Downloading Node.js LTS (v20) for Windows...")

    with tempfile.NamedTemporaryFile(suffix=".msi", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        urllib.request.urlretrieve(url, tmp_path)
        _print_step("Running installer (administrator rights may be required)...")
        code = subprocess.call(
            ["msiexec", "/i", tmp_path, "/qb", "REBOOT=ReallySuppress"],
            shell=False,
        )
        if code != 0:
            raise RuntimeError("msiexec exited with code %d" % code)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass

    standard = r"C:\Program Files\nodejs\npm.cmd"
    if os.path.exists(standard):
        return True

    _print_warning(
        "Node.js installed, but PATH is not updated yet in this session.\n"
        "  Please restart your terminal and run [cyan]docforge init[/] again."
    )
    sys.exit(0)


def _install_node_macos():
    brew = shutil.which("brew")
    if brew:
        _print_step("Installing Node.js via Homebrew...")
        code = subprocess.call([brew, "install", "node@20"], shell=False)
        if code == 0:
            return True
        raise RuntimeError("brew install node@20 exited with code %d" % code)

    _print_error("Homebrew not found.")
    _print_step("Install Node.js manually: [cyan]https://nodejs.org[/]")
    _print_step("Then restart your terminal and run [cyan]docforge init[/] again.")
    sys.exit(1)


def _install_node_linux():
    apt = shutil.which("apt-get")
    if apt:
        _print_step("Adding NodeSource repository and installing Node.js 20...")
        script_url = "https://deb.nodesource.com/setup_20.x"
        with tempfile.NamedTemporaryFile(suffix=".sh", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            urllib.request.urlretrieve(script_url, tmp_path)
            os.chmod(tmp_path, 0o755)
            code = subprocess.call(["sudo", "bash", tmp_path], shell=False)
            if code != 0:
                raise RuntimeError("setup_20.x exited with code %d" % code)
            code = subprocess.call(["sudo", apt, "install", "-y", "nodejs"], shell=False)
            if code != 0:
                raise RuntimeError("apt-get install nodejs exited with code %d" % code)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return True

    dnf = shutil.which("dnf")
    if dnf:
        _print_step("Installing Node.js 20 via dnf...")
        code = subprocess.call(
            ["sudo", dnf, "module", "install", "-y", "nodejs:20"],
            shell=False,
        )
        if code == 0:
            return True
        raise RuntimeError("dnf install nodejs exited with code %d" % code)

    _print_error("Neither apt-get nor dnf was found.")
    _print_step("Install Node.js manually: [cyan]https://nodejs.org[/]")
    sys.exit(1)


def ensure_node():
    ver = _node_version()

    if ver:
        try:
            major = int(ver.lstrip("v").split(".")[0])
        except ValueError:
            major = 0

        if major >= 18:
            _print_success("Node.js %s is already installed" % ver)
            npm_exe = _get_npm_exe()
            if npm_exe:
                return npm_exe
            _print_warning("npm not found even though Node.js is installed.")
        else:
            _print_warning("Found Node.js %s, but version >= 18 is required." % ver)
    else:
        _print_warning("Node.js not found.")

    if not _confirm("Install Node.js 20 LTS automatically?"):
        _print_error(
            "Node.js is required to run Docusaurus.\n"
            "  Install it manually: https://nodejs.org"
        )
        sys.exit(1)

    if _IS_WINDOWS:
        _install_node_windows()
    elif _IS_MACOS:
        _install_node_macos()
    else:
        _install_node_linux()

    npm_exe = _get_npm_exe()
    if not npm_exe and _IS_WINDOWS:
        candidate = r"C:\Program Files\nodejs\npm.cmd"
        if os.path.exists(candidate):
            npm_exe = candidate

    if not npm_exe:
        _print_error(
            "npm still not found after installation.\n"
            "  Please restart your terminal and run [cyan]docforge init[/] again."
        )
        sys.exit(1)

    _print_success("Node.js installed successfully")
    return npm_exe


# ─────────────────────── git ───────────────────────

def _git_version():
    exe = shutil.which("git")
    if not exe:
        return None
    code, out, _ = _run_silent([exe, "--version"])
    return out.strip() if code == 0 else None


def _install_git_windows():
    url = (
        "https://github.com/git-for-windows/git/releases/download/"
        "v2.45.2.windows.1/Git-2.45.2-64-bit.exe"
    )
    _print_step("Downloading Git for Windows...")
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        urllib.request.urlretrieve(url, tmp_path)
        _print_step("Running Git installer (silent mode)...")
        code = subprocess.call(
            [tmp_path, "/VERYSILENT", "/NORESTART"],
            shell=False,
        )
        if code != 0:
            raise RuntimeError("Git installer exited with code %d" % code)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    return True


def _install_git_macos():
    brew = shutil.which("brew")
    if brew:
        _print_step("Installing Git via Homebrew...")
        code = subprocess.call([brew, "install", "git"], shell=False)
        if code == 0:
            return True
    _print_step("Install Git manually: [cyan]https://git-scm.com[/]")
    sys.exit(1)


def _install_git_linux():
    apt = shutil.which("apt-get")
    if apt:
        code = subprocess.call(["sudo", apt, "install", "-y", "git"], shell=False)
        if code == 0:
            return True
    dnf = shutil.which("dnf")
    if dnf:
        code = subprocess.call(["sudo", dnf, "install", "-y", "git"], shell=False)
        if code == 0:
            return True
    _print_step("Install Git manually: [cyan]https://git-scm.com[/]")
    sys.exit(1)


def ensure_git():
    ver = _git_version()
    if ver:
        _print_success("Git is already installed (%s)" % ver)
        return

    _print_warning("Git not found.")
    if not _confirm("Install Git automatically?"):
        _print_warning("Git is not required right now, but needed for GitHub Actions.")
        return

    if _IS_WINDOWS:
        _install_git_windows()
    elif _IS_MACOS:
        _install_git_macos()
    else:
        _install_git_linux()

    if _git_version():
        _print_success("Git installed successfully")
    else:
        _print_warning(
            "Git was installed, but PATH is not updated yet in this session.\n"
            "  Please restart your terminal."
        )


# ─────────────────────── main entry point ───────────────────────

def check_and_install_all(need_node=True, need_git=True):
    console.print()
    console.print("  [info]🔍 Checking system dependencies...[/]")
    console.print()

    result = {}

    if need_node:
        npm_exe = ensure_node()
        result["npm"] = npm_exe

    if need_git:
        ensure_git()
        result["git"] = shutil.which("git")

    console.print()
    return result
