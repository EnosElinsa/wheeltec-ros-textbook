from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path


ALLOWED_DISPOSITIONS = {"move", "merge", "drop"}


def assert_anchor_exists(page: Path, anchor: str) -> None:
    """Require one explicit Markdown anchor on the expected page."""
    assert page.is_file(), f"missing migration target: {page}"
    marker = f"{{#{anchor}}}"
    count = page.read_text(encoding="utf-8").count(marker)
    assert count == 1, f"expected exactly one {marker} in {page}, found {count}"


def _anchored_section(text: str, anchor: str) -> str:
    marker = f"{{#{anchor}}}"
    start = text.index(marker)
    line_start = text.rfind("\n", 0, start) + 1
    heading = re.match(r"(#{1,6})\s", text[line_start:])
    assert heading, f"anchor {anchor!r} is not attached to a Markdown heading"
    level = len(heading.group(1))
    end = len(text)
    in_fence = False
    offset = 0
    for line in text[line_start:].splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
        elif offset and not in_fence:
            candidate = re.match(r"^(#{1,6})\s", line)
            if candidate and len(candidate.group(1)) <= level:
                end = line_start + offset
                break
        offset += len(line)
    return text[line_start:end]


def _visible_heading(source_heading: str) -> str:
    return source_heading.rsplit(" / ", 1)[-1].replace("`", "").strip()


def heading_migration_complete(csv_path: Path, textbook_root: Path) -> None:
    """Validate each retained source heading against its fixed anchored section."""
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows, f"empty heading migration ledger: {csv_path}"

    identities = Counter((row["source_file"], row["source_heading"]) for row in rows)
    duplicates = [identity for identity, count in identities.items() if count != 1]
    assert duplicates == [], f"headings must have one disposition: {duplicates}"

    retained: dict[tuple[str, str], list[str]] = defaultdict(list)
    for row in rows:
        disposition = row["disposition"].strip()
        assert disposition in ALLOWED_DISPOSITIONS, f"invalid disposition: {disposition!r}"
        assert row["reason"].strip(), f"missing migration reason: {row['source_heading']}"
        if disposition == "drop":
            continue
        target_file = row["target_file"].strip()
        target_anchor = row["target_anchor"].strip()
        assert target_file and target_anchor, f"retained heading lacks target: {row['source_heading']}"
        retained[(target_file, target_anchor)].append(_visible_heading(row["source_heading"]))

    missing: list[str] = []
    for (target_file, target_anchor), headings in retained.items():
        page = textbook_root / target_file
        assert_anchor_exists(page, target_anchor)
        section = _anchored_section(page.read_text(encoding="utf-8"), target_anchor).replace("`", "")
        required_counts = Counter(headings)
        for heading, required in required_counts.items():
            observed = section.count(heading)
            if observed < required:
                missing.append(
                    f"{target_file}#{target_anchor}: {heading!r} required {required}, found {observed}"
                )
    assert missing == [], "retained headings missing from target sections:\n" + "\n".join(missing)
