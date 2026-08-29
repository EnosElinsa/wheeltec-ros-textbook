from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OLD=(
 'docs/04-ros2-development/turn-on-wheeltec-robot-source-walkthrough.md',
 'docs/05-sensors-navigation/ros1-bag-offline-diagnostics.md',
 'docs/06-stm32-firmware/stm32-peripheral-labs.md',
)

def test_unnumbered_pages_are_deleted_and_fixed_anchors_exist():
    assert not any((ROOT/p).exists() for p in OLD)
    anchors=('source-package-selection','bringup-launch-chain','source-change-exercise','firmware-evidence-record','stm32-peripheral-labs','closed-loop-prechecks','ros-serial-firmware-chain','ros1-bag-offline-diagnostics')
    text='\n'.join(path.read_text(encoding='utf8') for path in (ROOT/'docs').rglob('*.md'))
    assert all(f'{{#{anchor}}}' in text for anchor in anchors)
