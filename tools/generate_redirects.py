from __future__ import annotations

import argparse
import csv
import html
import json
import os
import posixpath
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath


@dataclass(frozen=True)
class Redirect:
    source: str
    target: str


def load_redirects(path: Path) -> list[Redirect]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["source", "target"]:
            raise ValueError("redirect map columns must be source,target")
        return [Redirect(row["source"].strip(), row["target"].strip()) for row in reader]


def _path_error(value: str) -> str | None:
    if not value or value.startswith(("/", "\\")):
        return "must be a non-empty site-relative path"
    if "\\" in value or not value.endswith("/"):
        return "must use forward slashes and end with /"
    if any(
        not (character.isalnum() or character in "/._-")
        for character in value
    ):
        return "contains characters outside the safe route alphabet"
    if any(part in {".", ".."} for part in PurePosixPath(value).parts):
        return "must not contain path traversal"
    return None


def validate_map(rows: list[Redirect]) -> list[str]:
    errors: list[str] = []
    sources: set[str] = set()
    for row in rows:
        for field, value in (("source", row.source), ("target", row.target)):
            message = _path_error(value)
            if message:
                errors.append(f"{field} {value!r} {message}")
        if row.source in sources:
            errors.append(f"duplicate source: {row.source}")
        sources.add(row.source)
        if row.source == row.target:
            errors.append(f"redirect points to itself: {row.source}")
    for row in rows:
        if row.target in sources:
            errors.append(f"redirect chain: {row.source} -> {row.target}")
    return errors


def _site_file(site_dir: Path, route: str) -> Path:
    resolved_site = site_dir.resolve()
    target = (resolved_site / Path(*PurePosixPath(route).parts) / "index.html").resolve()
    try:
        target.relative_to(resolved_site)
    except ValueError as exc:
        raise ValueError(f"route leaves site directory: {route}") from exc
    return target


def validate_built_targets(rows: list[Redirect], site_dir: Path) -> list[str]:
    return [
        f"missing built redirect target: {row.target}"
        for row in rows
        if not _site_file(site_dir, row.target).is_file()
    ]


def render_redirect(source: str, target: str) -> str:
    source_dir = source.rstrip("/") or "."
    relative = posixpath.relpath(target, start=source_dir)
    if not relative.endswith("/"):
        relative += "/"
    escaped = html.escape(relative, quote=True)
    js_target = (
        json.dumps(relative, ensure_ascii=True)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url={escaped}">
  <link rel="canonical" href="{escaped}">
  <title>页面已迁移</title>
</head>
<body>
  <p>页面已迁移到 <a href="{escaped}">{escaped}</a>。</p>
  <script>
    location.replace({js_target} + location.search + location.hash);
  </script>
</body>
</html>
"""


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_redirects(rows: list[Redirect], site_dir: Path) -> list[Path]:
    map_errors = validate_map(rows)
    if map_errors:
        raise ValueError("; ".join(map_errors))
    target_errors = validate_built_targets(rows, site_dir)
    if target_errors:
        raise ValueError("; ".join(target_errors))

    outputs: list[Path] = []
    for row in rows:
        output = _site_file(site_dir, row.source)
        if output.exists():
            raise FileExistsError(f"refusing to overwrite built page: {output}")
        _write_atomic(output, render_redirect(row.source, row.target))
        outputs.append(output)
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate legacy URL redirect pages")
    parser.add_argument("--mapping", type=Path, required=True)
    parser.add_argument("--site-dir", type=Path, required=True)
    args = parser.parse_args()
    rows = load_redirects(args.mapping)
    outputs = write_redirects(rows, args.site_dir)
    print(f"generated {len(outputs)} legacy redirects")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
