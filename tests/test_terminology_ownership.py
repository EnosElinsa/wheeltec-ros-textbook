from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from terminology_audit import audit_rules, find_public_pages, load_rules  # noqa: E402


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
