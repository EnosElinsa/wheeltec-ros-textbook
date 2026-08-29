from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _is_git_checkout(path: Path) -> bool:
    if not path.is_dir():
        return False
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def _contains_revision(path: Path, revision: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(path), "cat-file", "-e", f"{revision}^{{commit}}"],
        capture_output=True,
    ).returncode == 0


def _has_only_public_roots(path: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(path), "ls-tree", "--name-only", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False
    allowed = {"applications", "chassis", "examples", "platform", "r680", "ros1", "ros2", "stm32"}
    entries = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return bool(entries) and entries.issubset(allowed)


def find_source_root(textbook_root: Path) -> Path | None:
    """Find an optional local public-source Git checkout across supported layouts."""
    root = textbook_root.resolve()
    configured = os.environ.get("WHEELTEC_SOURCE_ROOT")
    candidates = [Path(configured)] if configured else []
    candidates.extend(
        (
            root.parent / "code-resource-curation-source",
            root.parent / ".worktrees/code-resource-curation-source",
            root.parent / "wheeltec-ros-source-reference",
            root.parent.parent / "wheeltec-ros-source-reference",
        )
    )
    revision = ""
    mapping = root / "metadata/code-resources.yml"
    if mapping.is_file():
        import yaml

        revision = str(yaml.safe_load(mapping.read_text(encoding="utf-8"))["source_revision"])
    return next(
        (
            path.resolve()
            for path in candidates
            if _is_git_checkout(path)
            and _has_only_public_roots(path)
            and (not revision or _contains_revision(path, revision))
        ),
        None,
    )


def find_process_root(textbook_root: Path) -> Path | None:
    """Find optional local-only audit inputs; standalone textbook clones omit them."""
    root = textbook_root.resolve()
    configured = os.environ.get("WHEELTEC_PROCESS_ROOT")
    candidates = [Path(configured)] if configured else []
    candidates.extend(
        (
            root.parent / "wheeltec-ros-source-reference",
            root.parent.parent / "wheeltec-ros-source-reference",
        )
    )
    return next((path.resolve() for path in candidates if path.is_dir()), None)
