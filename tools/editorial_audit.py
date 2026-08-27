from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path


PROHIBITED_EDITORIAL_PATTERNS = {
    "colloquial terminology": re.compile(r"(?:英文是|英文为|Topic\s*就是)"),
    "chapter meta-negation": re.compile(r"本章不要求"),
    "exercise meta-negation": re.compile(r"这项练习不要求"),
    "filler emphasis": re.compile(r"重点是|需要注意的是"),
    "reader prediction": re.compile(r"你应该能|应能理解"),
    "inflated technical prose": re.compile(r"至关重要|完整体系|深入理解"),
    "source-material framing": re.compile(
        r"(?:资料中|资料包中|当前资料|随货资料|本机资料中|用户资料|原始资料)"
    ),
}


@dataclass(frozen=True)
class EditorialIssue:
    path: str
    line: int
    category: str
    excerpt: str


@dataclass(frozen=True)
class ProtectedContent:
    path: str
    fenced_code_sha256: tuple[str, ...]
    table_sha256: tuple[str, ...]
    safety_admonition_sha256: tuple[str, ...]
    validation_marker_count: int


def _sha256(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _iter_paths(paths: list[Path]) -> list[Path]:
    result: set[Path] = set()
    for path in paths:
        if path.is_file() and path.suffix.lower() in {".md", ".yml", ".yaml"}:
            result.add(path.resolve())
        elif path.is_dir():
            result.update(item.resolve() for item in path.rglob("*.md"))
    return sorted(result)


def _is_fence(line: str) -> bool:
    return line.lstrip().startswith(("```", "~~~"))


def scan_markdown(path: Path) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []
    text = path.read_text(encoding="utf-8")
    fenced = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if _is_fence(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        for category, pattern in PROHIBITED_EDITORIAL_PATTERNS.items():
            if pattern.search(line):
                issues.append(
                    EditorialIssue(
                        path=path.as_posix(),
                        line=line_number,
                        category=category,
                        excerpt=line.strip(),
                    )
                )
    return issues


def scan_tree(paths: list[Path]) -> list[EditorialIssue]:
    issues: list[EditorialIssue] = []
    for path in _iter_paths(paths):
        issues.extend(scan_markdown(path))
    return issues


def _blocks(path: Path) -> tuple[list[str], list[str], list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    code: list[str] = []
    tables: list[str] = []
    safety: list[str] = []
    in_fence = False
    current_code: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if _is_fence(line):
            if in_fence:
                code.append("".join(current_code))
                current_code = []
                in_fence = False
            else:
                in_fence = True
            index += 1
            continue
        if in_fence:
            current_code.append(line)
            index += 1
            continue
        if line.lstrip().startswith("!!! "):
            kind = line.strip().split(maxsplit=1)[1].split()[0]
            block = [line]
            if kind in {"warning", "danger"}:
                index += 1
                while index < len(lines):
                    candidate = lines[index]
                    if candidate.startswith("    ") or not candidate.strip():
                        block.append(candidate)
                        index += 1
                        continue
                    break
                safety.append("".join(block))
                continue
        if line.lstrip().startswith("|") and index + 1 < len(lines):
            separator = lines[index + 1]
            if separator.lstrip().startswith("|") and "---" in separator:
                block = [line, separator]
                index += 2
                while index < len(lines) and lines[index].lstrip().startswith("|"):
                    block.append(lines[index])
                    index += 1
                tables.append("".join(block))
                continue
        index += 1
    return code, tables, safety


def extract_protected_content(path: Path) -> ProtectedContent:
    code, tables, safety = _blocks(path)
    text = path.read_text(encoding="utf-8")
    return ProtectedContent(
        path=path.as_posix(),
        fenced_code_sha256=tuple(_sha256(block) for block in code),
        table_sha256=tuple(_sha256(block) for block in tables),
        safety_admonition_sha256=tuple(_sha256(block) for block in safety),
        validation_marker_count=text.count("资料核对通过，实机未验证"),
    )


def compare_protected_content(
    before: list[ProtectedContent], after: list[ProtectedContent]
) -> list[str]:
    differences: list[str] = []
    if len(before) != len(after):
        return [f"protected file count changed: {len(before)} -> {len(after)}"]
    for old, new in zip(before, after):
        path = new.path
        for label, old_value, new_value in (
            ("fenced code", tuple(old.fenced_code_sha256), tuple(new.fenced_code_sha256)),
            ("tables", tuple(old.table_sha256), tuple(new.table_sha256)),
            ("safety admonitions", tuple(old.safety_admonition_sha256), tuple(new.safety_admonition_sha256)),
        ):
            if old_value != new_value:
                differences.append(f"{path}: {label} changed")
        if old.validation_marker_count != new.validation_marker_count:
            differences.append(f"{path}: validation marker count changed")
    return differences


def load_terminology(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan textbook editorial style without rewriting prose")
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan")
    scan.add_argument("--paths", type=Path, nargs="+", required=True)
    scan.add_argument("--report", type=Path, required=True)
    protect = subparsers.add_parser("protect")
    protect.add_argument("--paths", type=Path, nargs="+", required=True)
    protect.add_argument("--output", type=Path, required=True)
    compare = subparsers.add_parser("compare")
    compare.add_argument("--baseline", type=Path, required=True)
    compare.add_argument("--paths", type=Path, nargs="+", required=True)
    args = parser.parse_args()

    if args.command == "scan":
        issues = scan_tree(args.paths)
        _write_json(args.report, [asdict(issue) for issue in issues])
        print(f"editorial findings: {len(issues)}")
        return 0
    if args.command == "protect":
        protected = [asdict(extract_protected_content(path)) for path in _iter_paths(args.paths)]
        _write_json(args.output, protected)
        print(f"protected files: {len(protected)}")
        return 0

    baseline_data = json.loads(args.baseline.read_text(encoding="utf-8"))
    selected = _iter_paths(args.paths)
    selected_paths = {path.as_posix() for path in selected}
    before = [
        ProtectedContent(
            path=item["path"],
            fenced_code_sha256=tuple(item["fenced_code_sha256"]),
            table_sha256=tuple(item["table_sha256"]),
            safety_admonition_sha256=tuple(item["safety_admonition_sha256"]),
            validation_marker_count=item["validation_marker_count"],
        )
        for item in baseline_data
        if item["path"] in selected_paths
    ]
    after = [extract_protected_content(path) for path in selected]
    differences = compare_protected_content(before, after)
    for difference in differences:
        print(difference)
    print(f"protected differences: {len(differences)}")
    return 1 if differences else 0


if __name__ == "__main__":
    raise SystemExit(main())
