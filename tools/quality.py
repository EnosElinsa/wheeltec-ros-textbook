from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from editorial_audit import scan_markdown


REQUIRED_MANIFEST_COLUMNS = {
    "kind",
    "number",
    "volume",
    "path",
    "title",
    "status",
    "size_limit_bytes",
}
ALLOWED_STATUSES = {"draft", "complete"}
ALLOWED_KINDS = {"foundation", "chapter", "appendix"}
FOUNDATION_HEADINGS = [
    "本章要回答的问题",
    "从一个具体场景开始",
    "新概念",
    "图示或逐步例子",
    "可选实验",
    "本章小结",
    "自检问题",
    "章节导航",
]
REQUIRED_CHAPTER_HEADINGS = [
    "本章目标",
    "适用范围",
    "开始前检查",
    "工作原理",
    "操作步骤",
    "结果验收",
    "常见故障与处理",
    "章节导航",
]
PROMOTIONAL_PATTERNS = ["推荐关注我们的公众号", "关注公众号", "获取更新资料"]
UNFINISHED_PATTERNS = [r"\bTODO\b", r"\bTBD\b", r"\[待写\]", r"\[内容待补\]"]
FORBIDDEN_FOUNDATION_PATTERNS = {
    "later chapter prerequisite": r"(?:已读|先读|完成|先完成)第\s*(?:[6-9]|[1-3][0-9]|4[0-6])\s*章",
    "advanced middleware jargon": r"\b(?:DDS|QoS|TF|colcon|Launch|Docker)\b",
    "required SSH access": r"必须(?:使用|通过).*SSH",
    "required robot runtime": r"(?:机器人|WHEELTEC).*(?:节点|系统).*已启动",
}
LINK_PATTERN = re.compile(r"!?\[[^\]]*\]\(([^)\r\n]+)\)")


@dataclass(frozen=True)
class Issue:
    severity: str
    path: str
    message: str


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def check_manifest(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return ["chapter manifest is empty"]

    errors: list[str] = []
    if set(rows[0]) != REQUIRED_MANIFEST_COLUMNS:
        errors.append("chapter manifest columns do not match the schema")

    paths = [row.get("path", "") for row in rows]
    if len(paths) != len(set(paths)):
        errors.append("chapter manifest paths are not unique")

    for row in rows:
        if row.get("kind") not in ALLOWED_KINDS:
            errors.append(f"invalid kind: {row.get('kind', '')}")
        if row.get("status") not in ALLOWED_STATUSES:
            errors.append(f"invalid status: {row.get('status', '')}")
        if not row.get("path", "").startswith("docs/"):
            errors.append(f"path is outside docs: {row.get('path', '')}")
        try:
            if int(row.get("size_limit_bytes", "0")) <= 0:
                raise ValueError
        except ValueError:
            errors.append(f"invalid size limit: {row.get('path', '')}")

    foundations = [row for row in rows if row.get("kind") == "foundation"]
    chapters = [row for row in rows if row.get("kind") == "chapter"]
    appendices = [row for row in rows if row.get("kind") == "appendix"]
    try:
        foundation_numbers = [int(row["number"]) for row in foundations]
        chapter_numbers = [int(row["number"]) for row in chapters]
        numbered_rows = [
            int(row["number"])
            for row in rows
            if row.get("kind") in {"foundation", "chapter"}
        ]
    except (KeyError, ValueError):
        foundation_numbers = []
        chapter_numbers = []
        numbered_rows = []
    if foundation_numbers != list(range(1, 6)):
        errors.append("foundation numbers must be consecutive from 1 through 5")
    if chapter_numbers != list(range(6, 47)):
        errors.append("engineering chapter numbers must be consecutive from 6 through 46")
    if numbered_rows != list(range(1, 47)):
        errors.append("all numbered pages must be ordered from 1 through 46")
    if [row.get("number") for row in appendices] != ["A", "B", "C"]:
        errors.append("public chapter manifest must contain appendices A through C")
    return errors


def check_chapter(path: Path, size_limit: int) -> list[Issue]:
    issues: list[Issue] = []
    relative = path.as_posix()
    if path.stat().st_size > size_limit:
        issues.append(Issue("error", relative, "file exceeds size limit"))
    text = path.read_text(encoding="utf-8")
    headings = set(re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE))
    for heading in REQUIRED_CHAPTER_HEADINGS:
        if heading not in headings:
            issues.append(Issue("error", relative, f"missing section: {heading}"))
    if any(pattern in text for pattern in PROMOTIONAL_PATTERNS):
        issues.append(Issue("error", relative, "supplier promotional copy is not allowed"))
    for pattern in UNFINISHED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(Issue("error", relative, "unfinished-work marker is not allowed"))
            break
    return issues


def check_foundation(path: Path, size_limit: int) -> list[Issue]:
    issues: list[Issue] = []
    relative = path.as_posix()
    if path.stat().st_size > size_limit:
        issues.append(Issue("error", relative, "file exceeds size limit"))
    text = path.read_text(encoding="utf-8")
    headings = set(re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE))
    for heading in FOUNDATION_HEADINGS:
        if heading not in headings:
            issues.append(Issue("error", relative, f"missing section: {heading}"))
    for category, pattern in FORBIDDEN_FOUNDATION_PATTERNS.items():
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(Issue("error", relative, category))
    if any(pattern in text for pattern in PROMOTIONAL_PATTERNS):
        issues.append(Issue("error", relative, "supplier promotional copy is not allowed"))
    for pattern in UNFINISHED_PATTERNS:
        if re.search(pattern, text, flags=re.IGNORECASE):
            issues.append(Issue("error", relative, "unfinished-work marker is not allowed"))
            break
    return issues


def check_links(path: Path, docs_root: Path) -> list[Issue]:
    issues: list[Issue] = []
    text = path.read_text(encoding="utf-8")
    for match in LINK_PATTERN.finditer(text):
        raw = match.group(1).strip()
        if raw.startswith(("http://", "https://", "mailto:", "data:", "#")):
            continue
        path_part = unquote(raw.split("#", 1)[0].split("?", 1)[0])
        if not path_part:
            continue
        target = (path.parent / path_part).resolve()
        try:
            target.relative_to(docs_root.resolve())
        except ValueError:
            issues.append(Issue("error", path.as_posix(), f"link leaves docs root: {raw}"))
            continue
        if not target.exists():
            issues.append(Issue("error", path.as_posix(), f"missing internal link target: {raw}"))
    return issues


def _markdown_files(root: Path, selected_paths: list[Path] | None) -> list[Path]:
    if not selected_paths:
        return sorted((root / "docs").rglob("*.md"))
    files: set[Path] = set()
    for path in selected_paths:
        resolved = path if path.is_absolute() else root / path
        if resolved.is_file() and resolved.suffix.lower() == ".md":
            files.add(resolved)
        elif resolved.is_dir():
            files.update(resolved.rglob("*.md"))
    return sorted(files)


def check_duplicate_prose(paths: list[Path]) -> list[Issue]:
    seen: dict[str, Path] = {}
    issues: list[Issue] = []
    for path in paths:
        text = re.sub(r"```.*?```", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        for paragraph in re.split(r"\n\s*\n", text):
            normalized = re.sub(r"\s+", " ", paragraph).strip()
            if len(normalized) <= 500 or normalized.startswith("|"):
                continue
            if normalized in seen:
                issues.append(
                    Issue(
                        "error",
                        path.as_posix(),
                        f"duplicate prose block also appears in {seen[normalized].as_posix()}",
                    )
                )
            else:
                seen[normalized] = path
    return issues


def check_all(root: Path, selected_paths: list[Path] | None = None) -> list[Issue]:
    root = root.resolve()
    issues: list[Issue] = []
    manifest = load_manifest(root / "metadata" / "chapter-manifest.csv")
    issues.extend(Issue("error", "metadata/chapter-manifest.csv", message) for message in check_manifest(manifest))
    manifest_by_path = {row["path"]: row for row in manifest}
    markdown_files = _markdown_files(root, selected_paths)

    for path in markdown_files:
        relative = path.relative_to(root).as_posix()
        row = manifest_by_path.get(relative)
        if row and row["status"] == "complete":
            size_limit = int(row["size_limit_bytes"])
            if row["kind"] == "foundation":
                issues.extend(check_foundation(path, size_limit))
            elif row["kind"] == "chapter":
                issues.extend(check_chapter(path, size_limit))
            elif path.stat().st_size > size_limit:
                issues.append(Issue("error", relative, "file exceeds size limit"))
        if relative == "docs/index.md" and path.stat().st_size > 20_000:
            issues.append(Issue("error", relative, "file exceeds size limit"))
        if relative.endswith("/index.md") and relative != "docs/index.md" and path.stat().st_size > 30_000:
            issues.append(Issue("error", relative, "file exceeds size limit"))
        issues.extend(check_links(path, root / "docs"))

    complete_paths = [
        root / row["path"]
        for row in manifest
        if row["status"] == "complete" and (root / row["path"]).is_file()
    ]
    issues.extend(check_duplicate_prose(complete_paths))
    return issues


def check_editorial_style(path: Path) -> list[Issue]:
    return [
        Issue("error", issue.path, f"{issue.category}: {issue.excerpt}")
        for issue in scan_markdown(path)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check textbook structure and content quality")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--paths", type=Path, nargs="*")
    check.add_argument("--editorial-strict", action="store_true")
    args = parser.parse_args()

    issues = check_all(args.root, args.paths)
    if args.editorial_strict:
        files = _markdown_files(args.root.resolve(), args.paths)
        for path in files:
            issues.extend(check_editorial_style(path))
    for issue in issues:
        print(f"{issue.severity.upper()} {issue.path}: {issue.message}")
    errors = [issue for issue in issues if issue.severity == "error"]
    print(f"quality check: {len(errors)} errors, {len(issues) - len(errors)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
