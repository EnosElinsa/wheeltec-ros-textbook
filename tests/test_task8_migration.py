from __future__ import annotations

from pathlib import Path

from heading_migration import assert_anchor_exists, heading_migration_complete
from workspace_paths import find_process_root


ROOT = Path(__file__).resolve().parents[1]
OLD = (
    "docs/04-ros2-development/turn-on-wheeltec-robot-source-walkthrough.md",
    "docs/05-sensors-navigation/ros1-bag-offline-diagnostics.md",
    "docs/06-stm32-firmware/stm32-peripheral-labs.md",
)
FIXED_TARGETS = (
    ("docs/05-ros2-development/22-environment-and-source-selection.md", "source-package-selection"),
    ("docs/05-ros2-development/25-launch-and-parameters.md", "bringup-launch-chain"),
    ("docs/05-ros2-development/27-modify-build-rollback.md", "source-change-exercise"),
    ("docs/07-stm32-firmware/37-firmware-architecture-freertos.md", "firmware-evidence-record"),
    ("docs/07-stm32-firmware/38-hardware-init-model-interfaces.md", "stm32-peripheral-labs"),
    ("docs/07-stm32-firmware/39-motor-control-pid.md", "closed-loop-prechecks"),
    ("docs/07-stm32-firmware/41-ros2-stm32-integration.md", "ros-serial-firmware-chain"),
    ("docs/appendices/a-ros1-maintenance.md", "ros1-bag-offline-diagnostics"),
)


def test_unnumbered_pages_are_absent_from_files_and_navigation() -> None:
    config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for relative in OLD:
        assert not (ROOT / relative).exists()
        assert relative.removeprefix("docs/") not in config


def test_fixed_target_anchors_exist_exactly_once() -> None:
    for relative, anchor in FIXED_TARGETS:
        assert_anchor_exists(ROOT / relative, anchor)


def test_chapter_25_uses_the_exact_numbered_launch_chain_title() -> None:
    text = (ROOT / "docs/05-ros2-development/25-launch-and-parameters.md").read_text(
        encoding="utf-8"
    )
    assert "## 25.5 启动链源码追踪 {#bringup-launch-chain}" in text


def test_every_retained_heading_is_substantively_represented() -> None:
    process_root = find_process_root(ROOT)
    if process_root is None:
        import pytest

        pytest.skip("standalone textbook checkout has no local heading-migration audit")
    migration = process_root / "docs/superpowers/audits/2026-08-29-page-heading-migration.csv"
    if not migration.is_file():
        import pytest

        pytest.skip("local process checkout does not contain heading-migration audit")
    heading_migration_complete(migration, ROOT)


def test_no_stale_internal_links_or_generic_appendix_only_notes() -> None:
    stale_names = tuple(Path(path).name for path in OLD)
    generic_phrases = (
        "本节使用的代码入口见[教材代码资源附录]",
        "详见[教材代码资源附录]",
    )
    offenders: list[str] = []
    for page in sorted((ROOT / "docs").rglob("*.md")):
        text = page.read_text(encoding="utf-8")
        if any(name in text for name in stale_names):
            offenders.append(f"{page.relative_to(ROOT)}: stale link")
        if any(phrase in text for phrase in generic_phrases):
            offenders.append(f"{page.relative_to(ROOT)}: generic resource note")
    assert offenders == []
