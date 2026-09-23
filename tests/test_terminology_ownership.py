from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from terminology_audit import (  # noqa: E402
    TERM_DEFINITION_BOLD,
    audit_rules,
    disallowed_bold,
    find_public_pages,
    load_rules,
)


FULL = "控制器局域网（Controller Area Network, CAN）"
HEADER = (
    "chinese,english,abbreviation,canonical_path,canonical_anchor,"
    "first_use,later_use\n"
)
ROW = (
    '控制器局域网,Controller Area Network,CAN,docs/chapter.md,can,'
    '"控制器局域网（Controller Area Network, CAN）",CAN\n'
)


def write_fixture(
    tmp_path: Path, later_text: str = "检查 CAN 总线。\n"
) -> tuple[Path, Path, Path]:
    docs = tmp_path / "docs"
    docs.mkdir()
    chapter = docs / "chapter.md"
    later = docs / "later.md"
    chapter.write_text(
        "# Chapter\n\n## Concept {#can}\n\n"
        f"{FULL}允许多个控制器共享总线。\n",
        encoding="utf-8",
    )
    later.write_text(f"# Later\n\n{later_text}", encoding="utf-8")
    (docs / "glossary.md").write_text(f"{FULL}\n", encoding="utf-8")
    csv_path = tmp_path / "terms.csv"
    csv_path.write_text(HEADER + ROW, encoding="utf-8")
    return csv_path, chapter, later


def test_valid_fixture_has_no_issues(tmp_path: Path) -> None:
    csv_path, chapter, later = write_fixture(tmp_path)
    assert audit_rules(
        tmp_path,
        load_rules(csv_path),
        narrative_paths=[chapter, later],
    ) == []


def test_duplicate_full_form_and_bold_are_reported(tmp_path: Path) -> None:
    csv_path, chapter, later = write_fixture(
        tmp_path,
        later_text=f"{FULL}用于通信。\n检查 **CAN** 总线。\n",
    )
    categories = {
        issue.category
        for issue in audit_rules(
            tmp_path,
            load_rules(csv_path),
            narrative_paths=[chapter, later],
        )
    }
    assert "duplicate full form" in categories
    assert "inline bold" in categories


def test_abbreviation_before_canonical_definition_is_reported(tmp_path: Path) -> None:
    csv_path, chapter, later = write_fixture(tmp_path)
    categories = {
        issue.category
        for issue in audit_rules(
            tmp_path,
            load_rules(csv_path),
            narrative_paths=[later, chapter],
        )
    }
    assert "abbreviation before canonical definition" in categories


def test_unexpanded_product_name_can_be_reused(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "chapter.md").write_text(
        "# FreeRTOS\n\n## Scheduler {#freertos}\n\nFreeRTOS 调度任务。\n",
        encoding="utf-8",
    )
    (docs / "later.md").write_text("# Later\n\n继续使用 FreeRTOS。\n", encoding="utf-8")
    (docs / "glossary.md").write_text("FreeRTOS\n", encoding="utf-8")
    csv_path = tmp_path / "terms.csv"
    csv_path.write_text(
        HEADER
        + "FreeRTOS,FreeRTOS,,docs/chapter.md,freertos,FreeRTOS,FreeRTOS\n",
        encoding="utf-8",
    )
    assert audit_rules(tmp_path, load_rules(csv_path)) == []


def test_public_pages_exclude_superpowers(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    (docs / "superpowers").mkdir(parents=True)
    (docs / "reader.md").write_text("# Reader\n", encoding="utf-8")
    (docs / "superpowers" / "plan.md").write_text("# Plan\n", encoding="utf-8")
    assert find_public_pages(tmp_path) == [(docs / "reader.md").resolve()]


def test_scoped_audit_defers_unselected_canonical_validation(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    selected = docs / "selected.md"
    selected.write_text(f"# Selected\n\n{FULL}用于通信。\n", encoding="utf-8")
    csv_path = tmp_path / "terms.csv"
    csv_path.write_text(HEADER + ROW, encoding="utf-8")
    issues = audit_rules(tmp_path, load_rules(csv_path), paths=[selected])
    categories = {issue.category for issue in issues}
    assert categories == {"duplicate full form"}


def test_can_is_defined_once_before_task_use() -> None:
    rules = load_rules(ROOT / "metadata/terminology.csv")
    can = next(rule for rule in rules if rule.abbreviation == "CAN")
    assert can.canonical_path == (
        "docs/02-hardware-basics/07-electrical-interfaces-communication.md"
    )
    assert audit_rules(ROOT, rules) == []


def test_firmware_full_form_is_not_reintroduced() -> None:
    full = "固件（Firmware）"
    occurrences: list[Path] = []
    for path in find_public_pages(ROOT):
        if path == (ROOT / "docs/glossary.md").resolve():
            continue
        occurrences.extend([path] * path.read_text(encoding="utf-8").count(full))
    assert occurrences == [
        (ROOT / "docs/02-hardware-basics/06-controller-and-firmware.md").resolve()
    ]


def test_public_reader_pages_bold_only_term_definitions() -> None:
    offenders = [
        path.relative_to(ROOT).as_posix()
        for path in find_public_pages(ROOT)
        if "**" in TERM_DEFINITION_BOLD.sub("", path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_term_definition_bold_is_allowed_but_other_bold_is_not() -> None:
    assert not disallowed_bold("称为**视差**（Disparity），记为 d。")
    assert not disallowed_bold("**视觉里程计**（Visual Odometry, VO）和**基线**（Baseline）")
    assert disallowed_bold("**只有红外可用。** 这台相机的外参为零。")
    assert disallowed_bold("检查 **CAN** 总线。")
