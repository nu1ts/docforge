import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request

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

_MIN_NODE_MAJOR = 18

_WINGET_ALREADY_INSTALLED = {
    0,
    2316632070,
    2316632089,
}


# ─────────────────────── output helpers ───────────────────────

def _print_step(text):
    console.print("  [dim]›[/] %s" % text)


def _print_success(text):
    console.print("[success]  ✔[/]  %s" % text)


def _print_warning(text):
    console.print("[warning]  ⚠[/]  %s" % text)


def _print_error(text):
    console.print("[error]  ✖[/]  %s" % text)


# ─────────────────────── utilities ───────────────────────

def _run_silent(cmd, timeout=300):
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        return 1, "", "not found"
    except subprocess.TimeoutExpired:
        return 1, "", "timeout"


def _confirm(prompt):
    try:
        answer = input("  [?] %s [Y/n]: " % prompt).strip().lower()
        return answer in ("", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


def _normalize_path_entry(path):
    return os.path.normcase(os.path.normpath(path))


def _unique_existing_dirs(paths):
    result = []
    seen = set()

    for path in paths:
        if not path:
            continue
        if not os.path.isdir(path):
            continue

        norm = _normalize_path_entry(path)
        if norm in seen:
            continue

        seen.add(norm)
        result.append(path)

    return result


def _prepend_to_process_path(paths):
    valid = _unique_existing_dirs(paths)
    if not valid:
        return

    current = os.environ.get("PATH", "")
    parts = [p for p in current.split(os.pathsep) if p]
    seen = {_normalize_path_entry(p) for p in parts}

    new_parts = []
    for path in valid:
        norm = _normalize_path_entry(path)
        if norm not in seen:
            new_parts.append(path)
            seen.add(norm)

    if new_parts:
        os.environ["PATH"] = os.pathsep.join(new_parts + parts)


def _broadcast_environment_change_windows():
    if not _IS_WINDOWS:
        return

    try:
        import ctypes

        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002

        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            5000,
            None,
        )
    except Exception:
        pass


def _persist_windows_user_path(paths):
    if not _IS_WINDOWS:
        return

    valid = _unique_existing_dirs(paths)
    if not valid:
        return

    try:
        import winreg

        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Environment")
        try:
            try:
                current, reg_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current, reg_type = "", winreg.REG_EXPAND_SZ

            parts = [p for p in str(current).split(";") if p]
            seen = {_normalize_path_entry(p) for p in parts}

            changed = False
            for path in reversed(valid):
                norm = _normalize_path_entry(path)
                if norm not in seen:
                    parts.insert(0, path)
                    seen.add(norm)
                    changed = True

            if changed:
                if reg_type not in (winreg.REG_SZ, winreg.REG_EXPAND_SZ):
                    reg_type = winreg.REG_EXPAND_SZ

                winreg.SetValueEx(
                    key,
                    "Path",
                    0,
                    reg_type,
                    ";".join(parts),
                )
        finally:
            winreg.CloseKey(key)

        _broadcast_environment_change_windows()

    except Exception:
        pass


def _refresh_path_windows():
    if not _IS_WINDOWS:
        return

    try:
        import winreg

        parts = []

        try:
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            )
            value, _ = winreg.QueryValueEx(key, "Path")
            winreg.CloseKey(key)
            if value:
                parts.append(value)
        except OSError:
            pass

        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
            value, _ = winreg.QueryValueEx(key, "Path")
            winreg.CloseKey(key)
            if value:
                parts.append(value)
        except OSError:
            pass

        if parts:
            os.environ["PATH"] = ";".join(parts) + ";" + os.environ.get("PATH", "")

    except Exception:
        pass


def _fetch_latest_lts_version():
    fallback = "24.15.0"

    try:
        req = urllib.request.Request(
            "https://nodejs.org/dist/index.json",
            headers={"User-Agent": "docforge"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            releases = json.loads(resp.read().decode("utf-8"))

        for release in releases:
            if release.get("lts"):
                return str(release["version"]).lstrip("v")

    except Exception:
        pass

    return fallback


def _fetch_latest_lts_major():
    version = _fetch_latest_lts_version()
    return version.split(".")[0]


# ─────────────────────── executable detection ───────────────────────

def _get_fnm_exe():
    exe = shutil.which("fnm")
    if exe:
        return exe

    if _IS_WINDOWS:
        local = os.environ.get("LOCALAPPDATA", "")
        candidate = os.path.join(local, "fnm", "fnm.exe")
        if os.path.exists(candidate):
            return candidate

    return None


def _get_fnm_node_dirs_windows():
    if not _IS_WINDOWS:
        return []

    dirs = []
    local = os.environ.get("LOCALAPPDATA", "")
    if not local:
        return []

    fnm_root = os.path.join(local, "fnm")
    alias_default = os.path.join(fnm_root, "aliases", "default")

    if os.path.isdir(alias_default):
        dirs.append(alias_default)

    fnm = _get_fnm_exe()
    if fnm:
        code, out, _ = _run_silent([fnm, "which", "lts-latest"], timeout=30)
        if code == 0:
            node_path = out.strip().splitlines()[-1].strip().strip('"')
            if os.path.exists(node_path):
                dirs.append(os.path.dirname(node_path))

    node_versions_root = os.path.join(fnm_root, "node-versions")
    if os.path.isdir(node_versions_root):
        found = []

        for root, _, files in os.walk(node_versions_root):
            if "node.exe" in files or "npm.cmd" in files:
                found.append(root)

        found.sort(
            key=lambda p: os.path.getmtime(p) if os.path.exists(p) else 0,
            reverse=True,
        )
        dirs.extend(found)

    return _unique_existing_dirs(dirs)


def _get_windows_node_candidate_dirs():
    dirs = [
        r"C:\Program Files\nodejs",
        r"C:\Program Files (x86)\nodejs",
    ]

    dirs.extend(_get_fnm_node_dirs_windows())

    return _unique_existing_dirs(dirs)


def _get_node_exe():
    exe = shutil.which("node")
    if exe or not _IS_WINDOWS:
        return exe

    for base in _get_windows_node_candidate_dirs():
        candidate = os.path.join(base, "node.exe")
        if os.path.exists(candidate):
            return candidate

    return None


def _get_npm_exe():
    if not _IS_WINDOWS:
        return shutil.which("npm")

    exe = shutil.which("npm.cmd") or shutil.which("npm")
    if exe:
        return exe

    for base in _get_windows_node_candidate_dirs():
        candidate = os.path.join(base, "npm.cmd")
        if os.path.exists(candidate):
            return candidate

    return None


def _ensure_node_tools_in_path_windows():
    if not _IS_WINDOWS:
        return

    dirs = []

    node_exe = _get_node_exe()
    npm_exe = _get_npm_exe()
    fnm_exe = _get_fnm_exe()

    if node_exe:
        dirs.append(os.path.dirname(node_exe))

    if npm_exe:
        dirs.append(os.path.dirname(npm_exe))

    if fnm_exe:
        dirs.append(os.path.dirname(fnm_exe))

    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        fnm_root = os.path.join(local, "fnm")
        fnm_default = os.path.join(local, "fnm", "aliases", "default")

        if os.path.isdir(fnm_root):
            dirs.append(fnm_root)

        if os.path.isdir(fnm_default):
            dirs.append(fnm_default)

    dirs = _unique_existing_dirs(dirs)

    _prepend_to_process_path(dirs)
    _persist_windows_user_path(dirs)
    _refresh_path_windows()


def _node_major_version():
    exe = _get_node_exe()
    if not exe:
        return 0

    code, out, _ = _run_silent([exe, "--version"])
    if code != 0:
        return 0

    try:
        return int(out.strip().lstrip("v").split(".")[0])
    except ValueError:
        return 0


# ─────────────────────── Windows: winget ───────────────────────

def _try_winget_install_node():
    winget = shutil.which("winget")
    if not winget:
        return False

    _print_step("Trying winget...")

    _run_silent([winget, "source", "update"], timeout=60)

    code, stdout, stderr = _run_silent(
        [
            winget, "install",
            "--id", "OpenJS.NodeJS.LTS",
            "--source", "winget",
            "--accept-source-agreements",
            "--accept-package-agreements",
            "--silent",
        ],
        timeout=600,
    )

    combined = (stdout or "") + (stderr or "")
    unsigned_code = code & 0xFFFFFFFF

    if code == 0:
        _refresh_path_windows()
        _ensure_node_tools_in_path_windows()
        return True

    if unsigned_code in _WINGET_ALREADY_INSTALLED or \
            "already installed" in combined.lower():
        _print_warning("Node.js is already installed according to winget.")
        _refresh_path_windows()
        _ensure_node_tools_in_path_windows()
        return True

    if unsigned_code == 0x8A150013:
        _print_step("Retrying winget without --source filter...")

        code2, stdout2, stderr2 = _run_silent(
            [
                winget, "install",
                "--id", "OpenJS.NodeJS.LTS",
                "--accept-source-agreements",
                "--accept-package-agreements",
                "--silent",
            ],
            timeout=600,
        )

        combined2 = (stdout2 or "") + (stderr2 or "")
        unsigned_code2 = code2 & 0xFFFFFFFF

        if code2 == 0:
            _refresh_path_windows()
            _ensure_node_tools_in_path_windows()
            return True

        if unsigned_code2 in _WINGET_ALREADY_INSTALLED or \
                "already installed" in combined2.lower():
            _print_warning("Node.js is already installed according to winget.")
            _refresh_path_windows()
            _ensure_node_tools_in_path_windows()
            return True

    _print_step("winget could not install Node.js (code 0x%08X)." % unsigned_code)
    return False


# ─────────────────────── Windows: fnm ───────────────────────

def _try_fnm_install_node():
    _print_step("Trying fnm (Fast Node Manager — no admin rights required)...")

    fnm = _get_fnm_exe()

    if not fnm:
        ps = shutil.which("pwsh") or shutil.which("powershell")
        if not ps:
            return False

        _print_step("Installing fnm via PowerShell...")
        code, _, stderr = _run_silent(
            [
                ps,
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-Command",
                "irm https://fnm.vercel.app/install | iex",
            ],
            timeout=180,
        )

        if code != 0:
            _print_step("fnm install script failed: %s" % stderr.strip())
            return False

        _refresh_path_windows()
        fnm = _get_fnm_exe()
        if not fnm:
            return False

    _print_step("Installing latest Node.js LTS via fnm...")
    code, _, stderr = _run_silent([fnm, "install", "--lts"], timeout=300)
    if code != 0:
        _print_step("fnm install --lts failed: %s" % stderr.strip())
        return False

    _run_silent([fnm, "default", "lts-latest"], timeout=30)
    _run_silent([fnm, "use", "lts-latest"], timeout=30)

    _refresh_path_windows()
    _ensure_node_tools_in_path_windows()
    return True


# ─────────────────────── Windows: MSI ───────────────────────

def _try_msi_install_node():
    lts_version = _fetch_latest_lts_version()
    arch = "x64" if platform.machine().endswith("64") else "x86"
    url = (
        "https://nodejs.org/dist/v%s/node-v%s-%s.msi"
        % (lts_version, lts_version, arch)
    )

    _print_step("Downloading Node.js LTS v%s MSI (%s)..." % (lts_version, arch))

    fd, tmp_path = tempfile.mkstemp(suffix=".msi", prefix="nodejs_")
    os.close(fd)

    try:
        try:
            urllib.request.urlretrieve(url, tmp_path)
        except Exception as exc:
            _print_error("Download failed: %s" % exc)
            return False

        if os.path.getsize(tmp_path) < 1_000_000:
            _print_error("Downloaded MSI file is too small — likely corrupted.")
            return False

        _print_step("Running MSI installer (a UAC prompt may appear)...")

        code = subprocess.call(
            [
                "msiexec",
                "/i", tmp_path,
                "/passive",
                "/norestart",
                "ADDLOCAL=ALL",
            ],
            shell=False,
        )

        if code == 0:
            _refresh_path_windows()
            _ensure_node_tools_in_path_windows()
            return True

        if code == 1602:
            _print_error("Installation was cancelled by the user.")
            return False

        if code == 1603:
            _print_error(
                "MSI installer failed with code 1603.\n"
                "  Most likely causes:\n"
                "  • A previous (possibly broken) Node.js installation exists.\n"
                "    Open 'Apps & Features', uninstall all Node.js entries,\n"
                "    delete C:\\Program Files\\nodejs if it still exists,\n"
                "    then retry.\n"
                "  • The terminal does not have administrator rights.\n"
                "    Right-click PowerShell → 'Run as Administrator', then retry."
            )
            return False

        _print_error("MSI installer exited with code %d." % code)
        return False

    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


# ─────────────────────── Windows: orchestration ───────────────────────

def _install_node_windows():
    if _try_winget_install_node():
        return

    if _try_fnm_install_node():
        return

    if _try_msi_install_node():
        return

    _print_error(
        "All automatic installation methods failed.\n"
        "  Please install Node.js manually: [cyan]https://nodejs.org/en/download[/]\n"
        "  After installation restart your terminal and run "
        "[cyan]docforge init[/] again."
    )
    sys.exit(1)


# ─────────────────────── macOS ───────────────────────

def _install_node_macos():
    lts_major = _fetch_latest_lts_major()
    brew = shutil.which("brew")

    if brew:
        formula = "node@%s" % lts_major
        _print_step("Installing latest Node.js LTS via Homebrew (%s)..." % formula)

        code = subprocess.call([brew, "install", formula], shell=False)
        if code == 0:
            subprocess.call(
                [brew, "link", "--overwrite", "--force", formula],
                shell=False,
            )
            return

        _print_warning("brew install failed (code %d)." % code)

    _print_error(
        "Could not install Node.js automatically.\n"
        "  Install Homebrew first: [cyan]https://brew.sh[/]\n"
        "  Then install the latest LTS formula manually."
    )
    sys.exit(1)


# ─────────────────────── Linux ───────────────────────

def _install_node_linux():
    apt = shutil.which("apt-get")
    if apt:
        _print_step("Adding NodeSource repository and installing latest Node.js LTS...")

        fd, tmp = tempfile.mkstemp(suffix=".sh", prefix="nodesource_")
        os.close(fd)

        try:
            try:
                urllib.request.urlretrieve(
                    "https://deb.nodesource.com/setup_lts.x",
                    tmp,
                )
            except Exception as exc:
                _print_error("Failed to download NodeSource setup script: %s" % exc)
                sys.exit(1)

            os.chmod(tmp, 0o755)

            if subprocess.call(["sudo", "bash", tmp], shell=False) != 0:
                _print_error("NodeSource setup script failed.")
                sys.exit(1)

            if subprocess.call(["sudo", apt, "install", "-y", "nodejs"], shell=False) == 0:
                return

            _print_error("apt-get install nodejs failed.")
            sys.exit(1)
        finally:
            try:
                os.remove(tmp)
            except OSError:
                pass

    dnf = shutil.which("dnf")
    if dnf:
        _print_step("Installing latest Node.js LTS via dnf...")
        if subprocess.call(
            ["sudo", dnf, "module", "install", "-y", "nodejs:lts"],
            shell=False,
        ) == 0:
            return

        _print_error("dnf install nodejs:lts failed.")
        sys.exit(1)

    pacman = shutil.which("pacman")
    if pacman:
        _print_step("Installing Node.js via pacman...")
        if subprocess.call(
            ["sudo", pacman, "-S", "--noconfirm", "nodejs", "npm"],
            shell=False,
        ) == 0:
            return

        _print_error("pacman install failed.")
        sys.exit(1)

    _print_error(
        "No supported package manager found (apt / dnf / pacman).\n"
        "  Install Node.js manually: [cyan]https://nodejs.org[/]"
    )
    sys.exit(1)


# ─────────────────────── public API: Node ───────────────────────

def ensure_node():
    major = _node_major_version()

    if major >= _MIN_NODE_MAJOR:
        npm_exe = _get_npm_exe()
        if npm_exe:
            if _IS_WINDOWS:
                _refresh_path_windows()
                _ensure_node_tools_in_path_windows()
                npm_exe = _get_npm_exe() or npm_exe

            _print_success("Node.js v%d is already installed" % major)
            return npm_exe

        _print_warning("Node.js v%d is installed, but npm was not found." % major)

    elif major > 0:
        _print_warning(
            "Node.js v%d found, but v%d or newer is required."
            % (major, _MIN_NODE_MAJOR)
        )
    else:
        _print_warning("Node.js not found.")

    if not _confirm("Install the latest Node.js LTS automatically?"):
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

    if _IS_WINDOWS:
        _refresh_path_windows()
        _ensure_node_tools_in_path_windows()

    npm_exe = _get_npm_exe()
    if not npm_exe:
        _print_warning(
            "Node.js appears to be installed, but npm is not visible "
            "in this terminal session.\n"
            "  Please restart your terminal and run "
            "[cyan]docforge init[/] again."
        )
        sys.exit(0)

    console.print()
    _print_success("Node.js installed successfully")
    _print_warning(
        "[warning]If your IDE terminal was already open, fully restart the IDE "
        "[warning]to refresh PATH."
    )
    return npm_exe


# ─────────────────────── public API: Git ───────────────────────

def _git_version():
    exe = shutil.which("git")
    if not exe:
        return None

    code, out, _ = _run_silent([exe, "--version"])
    return out.strip() if code == 0 else None


def _install_git_windows():
    winget = shutil.which("winget")
    if winget:
        _print_step("Installing Git via winget...")
        code, _, _ = _run_silent(
            [
                winget, "install",
                "--id", "Git.Git",
                "--source", "winget",
                "--accept-source-agreements",
                "--accept-package-agreements",
                "--silent",
            ],
            timeout=300,
        )

        if code == 0 or (code & 0xFFFFFFFF) in _WINGET_ALREADY_INSTALLED:
            _refresh_path_windows()
            return True

    url = (
        "https://github.com/git-for-windows/git/releases/download/"
        "v2.45.2.windows.1/Git-2.45.2-64-bit.exe"
    )

    _print_step("Downloading Git for Windows...")
    fd, tmp = tempfile.mkstemp(suffix=".exe", prefix="git_")
    os.close(fd)

    try:
        urllib.request.urlretrieve(url, tmp)

        _print_step("Running Git installer (silent)...")
        code = subprocess.call(
            [tmp, "/VERYSILENT", "/NORESTART"],
            shell=False,
        )

        if code == 0:
            _refresh_path_windows()
            return True

        _print_error("Git installer exited with code %d." % code)
        return False

    except Exception as exc:
        _print_error("Failed to install Git: %s" % exc)
        return False

    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def _install_git_macos():
    brew = shutil.which("brew")
    if brew:
        _print_step("Installing Git via Homebrew...")
        if subprocess.call([brew, "install", "git"], shell=False) == 0:
            return True

    _print_error(
        "Could not install Git automatically.\n"
        "  Install it manually: [cyan]https://git-scm.com[/]"
    )
    sys.exit(1)


def _install_git_linux():
    for pkg_mgr, cmd in [
        ("apt-get", ["sudo", "apt-get", "install", "-y", "git"]),
        ("dnf",     ["sudo", "dnf",     "install", "-y", "git"]),
        ("pacman",  ["sudo", "pacman",  "-S", "--noconfirm", "git"]),
    ]:
        if shutil.which(pkg_mgr):
            if subprocess.call(cmd, shell=False) == 0:
                return True

    _print_error(
        "Could not install Git automatically.\n"
        "  Install it manually: [cyan]https://git-scm.com[/]"
    )
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
            "Git was installed, but PATH is not updated yet in this terminal session.\n"
            "  Please restart your terminal."
        )


# ─────────────────────── main entry point ───────────────────────

def check_and_install_all(need_node=True, need_git=True):
    console.print()
    console.print("  [info]🔍 Checking system dependencies...[/]")
    console.print()

    result = {}

    if need_node:
        result["npm"] = ensure_node()

    if need_git:
        ensure_git()
        result["git"] = shutil.which("git")

    console.print()
    return result
