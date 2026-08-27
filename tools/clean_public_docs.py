from __future__ import annotations

import re
from pathlib import Path


REMOVED_SECTIONS = (
    "相关视频、代码和固件",
    "来源与延伸阅读",
)


def remove_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*\r?\n.*?(?=^##\s+|\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    return pattern.sub("", text)


def clean_markdown(text: str) -> str:
    for heading in REMOVED_SECTIONS:
        text = remove_section(text, heading)
    return re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"


def clean_tree(root: Path) -> list[Path]:
    changed: list[Path] = []
    for path in sorted((root / "docs").rglob("*.md")):
        original = path.read_text(encoding="utf-8")
        cleaned = clean_markdown(original)
        if cleaned != original:
            path.write_text(cleaned, encoding="utf-8")
            changed.append(path)
    return changed


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    changed = clean_tree(root)
    print(f"cleaned {len(changed)} public Markdown files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
