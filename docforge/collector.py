import glob
import os

from rich.console import Console

console = Console()


def collect_source(source, project_root):
    base = os.path.join(str(project_root), str(source.base_dir))
    lines = []
    total_chars = 0

    for pattern in source.patterns:
        search_path = os.path.join(base, str(pattern))
        matched_files = sorted(glob.glob(search_path))

        for filepath in matched_files:
            rel = os.path.relpath(str(filepath), str(project_root))

            if any(ex in rel for ex in source.exclude):
                continue

            if not os.path.isfile(filepath):
                continue

            try:
                with open(filepath, "r") as f:
                    content = f.read()
            except (IOError, OSError):
                continue

            header = "===== FILE: %s =====" % rel
            entry = "%s\n%s\n\n" % (header, content)

            if total_chars + len(entry) > source.max_chars:
                lines.append("\n... [TRUNCATED — limit reached] ...")
                break

            lines.append(entry)
            total_chars += len(entry)

    return "".join(lines)


def collect_all(config, project_root):
    result = {}
    root = str(project_root)

    for source in config.sources:
        console.print(
            "  📦 Collecting [cyan]%s[/]..." % source.name
        )
        content = collect_source(source, root)
        result[source.name] = content
        char_count = len(content)
        console.print(
            "     → %s chars" % "{:,}".format(char_count)
        )

    return result
