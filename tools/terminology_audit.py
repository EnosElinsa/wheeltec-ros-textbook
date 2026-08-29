from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path


COLUMNS = (
    "chinese",
    "english",
    "abbreviation",
    "canonical_path",
    "canonical_anchor",
    "first_use",
    "later_use",
)


@dataclass(frozen=True)
class TermRule:
    chinese: str
    english: str
    abbreviation: str
    canonical_path: str
    canonical_anchor: str
    first_use: str
    later_use: str


@dataclass(frozen=True)
class TerminologyIssue:
    category: str
    term: str
    path: str
    line: int
    message: str


def load_rules(path: Path) -> list[TermRule]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError(f"terminology columns must be {','.join(COLUMNS)}")
        rows = list(reader)
    rules: list[TermRule] = []
    for line, row in enumerate(rows, start=2):
        required = [column for column in COLUMNS if column != "abbreviation"]
        missing = [column for column in required if not row[column].strip()]
        if missing:
            raise ValueError(f"line {line} has empty fields: {','.join(missing)}")
        rules.append(TermRule(**{column: row[column].strip() for column in COLUMNS}))
    return rules


def find_public_pages(root: Path, paths: list[Path] | None = None) -> list[Path]:
    roots = paths or [root / "docs"]
    pages: set[Path] = set()
    for supplied in roots:
        path = supplied if supplied.is_absolute() else root / supplied
        if path.is_file() and path.suffix.lower() == ".md":
            pages.add(path.resolve())
        elif path.is_dir():
            pages.update(item.resolve() for item in path.rglob("*.md"))
    result: list[Path] = []
    for page in pages:
        relative = page.relative_to(root.resolve())
        if relative.parts[:2] == ("docs", "superpowers"):
            continue
        result.append(page)
    return sorted(result)


def _visible_lines(path: Path) -> list[tuple[int, str]]:
    visible: list[tuple[int, str]] = []
    in_fence = False
    in_front_matter = False
    for number, source in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = source.lstrip()
        if number == 1 and source.strip() == "---":
            in_front_matter = True
            continue
        if in_front_matter:
            if source.strip() == "---":
                in_front_matter = False
            continue
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        prose = re.sub(r"`[^`]*`", "", source)
        prose = re.sub(r"\]\([^)]+\)", "]", prose)
        visible.append((number, prose))
    return visible


def _line_for(lines: list[tuple[int, str]], needle: str) -> int:
    return next((number for number, text in lines if needle in text), 1)


def audit_rules(
    root: Path,
    rules: list[TermRule],
    paths: list[Path] | None = None,
    narrative_paths: list[Path] | None = None,
) -> list[TerminologyIssue]:
    root = root.resolve()
    selected = find_public_pages(root, paths)
    glossary = (root / "docs" / "glossary.md").resolve()
    visible = {page: _visible_lines(page) for page in selected}
    issues: list[TerminologyIssue] = []

    for page, lines in visible.items():
        for number, line in lines:
            if re.search(r"\*\*[^*\n]+\*\*", line):
                issues.append(
                    TerminologyIssue(
                        "inline bold",
                        "",
                        page.relative_to(root).as_posix(),
                        number,
                        "public prose must use headings, tables, or admonitions",
                    )
                )

    for rule in rules:
        canonical = (root / rule.canonical_path).resolve()
        label = rule.abbreviation or rule.chinese
        if not canonical.is_file():
            issues.append(
                TerminologyIssue(
                    "missing canonical page",
                    label,
                    rule.canonical_path,
                    1,
                    "canonical_path does not exist",
                )
            )
            continue
        canonical_lines = _visible_lines(canonical)
        anchor = f"{{#{rule.canonical_anchor}}}"
        anchor_count = canonical.read_text(encoding="utf-8").count(anchor)
        if anchor_count != 1:
            issues.append(
                TerminologyIssue(
                    "canonical anchor",
                    label,
                    rule.canonical_path,
                    1,
                    f"expected one {anchor}, found {anchor_count}",
                )
            )
        first_count = sum(line.count(rule.first_use) for _, line in canonical_lines)
        if rule.first_use == rule.later_use:
            if first_count == 0:
                issues.append(
                    TerminologyIssue(
                        "canonical first use",
                        label,
                        rule.canonical_path,
                        1,
                        "unexpanded term must occur on canonical page",
                    )
                )
        elif first_count != 1:
            issues.append(
                TerminologyIssue(
                    "canonical first use",
                    label,
                    rule.canonical_path,
                    _line_for(canonical_lines, rule.first_use),
                    f"expected canonical first_use once, found {first_count}",
                )
            )
        for page, lines in visible.items():
            if page in {canonical, glossary}:
                continue
            for number, line in lines:
                if rule.first_use != rule.later_use and rule.first_use in line:
                    issues.append(
                        TerminologyIssue(
                            "duplicate full form",
                            label,
                            page.relative_to(root).as_posix(),
                            number,
                            f"full form belongs to {rule.canonical_path}",
                        )
                    )

    if narrative_paths is None and paths is None:
        manifest = root / "metadata" / "chapter-manifest.csv"
        if manifest.is_file():
            with manifest.open(encoding="utf-8-sig", newline="") as handle:
                narrative_paths = [
                    root / row["path"]
                    for row in csv.DictReader(handle)
                    if row["kind"] in {"foundation", "chapter"}
                ]
    if narrative_paths:
        ordered_text: list[str] = []
        offsets: list[tuple[int, Path, int]] = []
        cursor = 0
        for supplied in narrative_paths:
            page = supplied if supplied.is_absolute() else root / supplied
            for number, line in _visible_lines(page):
                if line.lstrip().startswith("#"):
                    continue
                ordered_text.append(line)
                offsets.append((cursor, page.resolve(), number))
                cursor += len(line) + 1
        joined = "\n".join(ordered_text)
        for rule in rules:
            if not rule.abbreviation or rule.first_use == rule.later_use:
                continue
            full_position = joined.find(rule.first_use)
            abbreviation = re.compile(
                rf"(?<![A-Za-z0-9_]){re.escape(rule.abbreviation)}(?![A-Za-z0-9_])"
            )
            match = abbreviation.search(joined)
            if match and (full_position < 0 or match.start() < full_position):
                prior = max(
                    (item for item in offsets if item[0] <= match.start()),
                    key=lambda item: item[0],
                )
                issues.append(
                    TerminologyIssue(
                        "abbreviation before canonical definition",
                        rule.abbreviation,
                        prior[1].relative_to(root).as_posix(),
                        prior[2],
                        f"define in {rule.canonical_path} before narrative use",
                    )
                )
    return sorted(issues, key=lambda item: (item.path, item.line, item.category, item.term))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--terms", type=Path, required=True)
    parser.add_argument("--paths", type=Path, nargs="*")
    args = parser.parse_args()
    root = args.root.resolve()
    terms = args.terms if args.terms.is_absolute() else root / args.terms
    issues = audit_rules(root, load_rules(terms), paths=args.paths)
    for issue in issues:
        print(f"{issue.path}:{issue.line}: {issue.category}: {issue.term}: {issue.message}")
    print(f"terminology findings: {len(issues)}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
