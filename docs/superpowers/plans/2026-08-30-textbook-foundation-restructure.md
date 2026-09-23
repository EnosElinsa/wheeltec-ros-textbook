# Textbook Foundation Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the textbook as ten parts and 50 chapters, teach hardware and control prerequisites in new Chapters 6–9, assign every reusable term to one canonical teaching page, remove inline term bolding and duplicate definitions, and publish only the new URL structure.

**Architecture:** Add a four-chapter hardware foundation part before all real-robot tasks, then atomically shift every existing chapter from 6–46 to 10–50 and every existing part from 2–9 to 3–10. A terminology ownership audit will make canonical definition pages machine-checkable; task chapters will use prerequisite links instead of repeating definitions. Redirect generation and all old-path compatibility code will be removed.

**Tech Stack:** Markdown, MkDocs Material, Python 3 standard library, PyYAML, pytest/unittest, PowerShell, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-08-30-textbook-foundation-restructure-design.md`

## Global Constraints

- The public textbook contains ten parts, Chapters 1–50, and Appendices A–D.
- Chapters 1–9 are foundation chapters; Chapters 10–50 are engineering chapters.
- New Chapters 6–9 live in `docs/02-hardware-basics/` and cover hardware/firmware, interfaces/communication, sensors/feedback, and chassis/control respectively.
- Every old Chapter 6–46 becomes old number + 4; every old Part 2–9 becomes old part number + 1.
- Old URLs, redirect pages, redirect metadata, and redirect-generation code are deleted. Old paths returning 404 is expected.
- Each reusable term has one `canonical_path` and `canonical_anchor`. Its full standard form may occur only there and in `docs/glossary.md`.
- `docs/glossary.md` is a lookup page and does not determine narrative first use.
- Public reader prose contains no double-asterisk inline emphasis; headings, tables, admonitions, lists, and code spans carry hierarchy instead.
- Commands, paths, package names, topic names, parameters, and symbols remain in backticks.
- Existing fenced code, tables, safety admonitions, explicit resource anchors, and code-resource boundaries must survive content migration unless a task explicitly names them.
- Preserve unrelated worktree changes. Each task stages only its listed files and verifies staged scope before committing.
- Use UTF-8 explicitly for all PowerShell/Python text operations.

---

### Task 1: Build terminology ownership and prose-style audit primitives

**Files:**
- Create: `tools/terminology_audit.py`
- Create: `tests/test_terminology_ownership.py`
- Modify: `tools/quality.py`

**Interfaces:**
- Consumes: the future CSV columns `chinese,english,abbreviation,canonical_path,canonical_anchor,first_use,later_use`.
- Produces: `TermRule`, `TerminologyIssue`, `load_rules()`, `audit_rules()`, `find_public_pages()`, and a CLI usable with `--paths` for scoped cleanup and without it for the final full-tree gate.

- [ ] **Step 1: Add failing tests for schema, canonical ownership, duplicate definitions, definition order, and inline bold**

Create `tests/test_terminology_ownership.py` with these test cases:

```python
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from terminology_audit import audit_rules, load_rules  # noqa: E402


FULL = "控制器局域网（Controller Area Network, CAN）"
HEADER = (
    "chinese,english,abbreviation,canonical_path,canonical_anchor,"
    "first_use,later_use\n"
)
ROW = (
    '控制器局域网,Controller Area Network,CAN,docs/chapter.md,can,'
    '"控制器局域网（Controller Area Network, CAN）",CAN\n'
)


def write_fixture(tmp_path: Path, later_text: str = "检查 CAN 总线。\n") -> tuple[Path, Path, Path]:
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
```

- [ ] **Step 2: Run the new test file and confirm it fails before implementation**

Run:

```powershell
$env:PYTHONUTF8='1'
python -m pytest tests/test_terminology_ownership.py -q
```

Expected: import failure for `terminology_audit`.

- [ ] **Step 3: Implement the audit module**

Implement these exact public types and functions:

```python
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
    result = []
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
        expanded_form = rule.first_use != rule.later_use
        required_count = 1 if expanded_form else max(first_count, 1)
        if first_count != required_count:
            issues.append(
                TerminologyIssue(
                    "canonical first use",
                    label,
                    rule.canonical_path,
                    _line_for(canonical_lines, rule.first_use),
                    f"expected canonical first_use, found {first_count}",
                )
            )
        for page, lines in visible.items():
            if page in {canonical, glossary}:
                continue
            for number, line in lines:
                if expanded_form and rule.first_use in line:
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
        ordered_text = []
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
                prior = max((item for item in offsets if item[0] <= match.start()), key=lambda item: item[0])
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
```

Implementation rules:

- Ignore fenced code blocks and `docs/superpowers/`.
- Require all seven CSV columns exactly.
- Require every `canonical_path` to exist and contain exactly one `{#canonical_anchor}`.
- When `first_use != later_use`, require the expanded `first_use` exactly once on its canonical page.
- When `first_use == later_use` for an unexpanded product/package name such as FreeRTOS or `cv_bridge`, require at least one canonical-page occurrence and allow normal reuse.
- Allow expanded `first_use` on `docs/glossary.md`; report it anywhere else.
- When `narrative_paths` is supplied, report a bare abbreviation found before the canonical page's first-use position. Do not treat code spans, URLs, front matter, or Markdown link targets as prose occurrences.
- Report every public prose double-asterisk span as `inline bold`.
- CLI:

```text
python tools/terminology_audit.py --root . --terms metadata/terminology.csv --paths docs/01-foundations docs/02-hardware-basics
```

Return exit code 1 when issues exist and print one issue per line.

- [ ] **Step 4: Expose the audit through quality.py without enabling the full-tree gate yet**

Import `audit_rules` and `load_rules`. Add a helper:

```python
def check_terminology(
    root: Path, paths: list[Path] | None = None
) -> list[Issue]:
    return [
        Issue("error", item.path, f"{item.category}: {item.term}: {item.message}")
        for item in audit_rules(
            root,
            load_rules(root / "metadata" / "terminology.csv"),
            paths=paths,
        )
    ]
```

Do not call it from `check_all()` until Task 7, because the current tree intentionally violates the new rule.

- [ ] **Step 5: Run unit tests**

Run:

```powershell
$env:PYTHONUTF8='1'
python -m pytest tests/test_terminology_ownership.py tests/test_editorial_style.py tests/test_quality.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit the audit primitives**

```powershell
git add -- tools/terminology_audit.py tools/quality.py tests/test_terminology_ownership.py
git diff --cached --check
git commit -m "test: add textbook terminology ownership audit"
```

---

### Task 2: Write the four new hardware foundation chapters

**Files:**
- Create: `docs/02-hardware-basics/index.md`
- Create: `docs/02-hardware-basics/06-controller-and-firmware.md`
- Create: `docs/02-hardware-basics/07-electrical-interfaces-communication.md`
- Create: `docs/02-hardware-basics/08-sensors-and-feedback.md`
- Create: `docs/02-hardware-basics/09-chassis-motion-control.md`
- Create: `tests/test_hardware_foundations.py`

**Interfaces:**
- Consumes: Chapter 2's system-level model and Task 1's future terminology ownership model.
- Produces: canonical teaching pages for all hardware/control terms used by Chapters 10–21 and 37–41.

- [ ] **Step 1: Add failing content tests**

Create `tests/test_hardware_foundations.py` asserting the files exist, their H1 numbers are 6–9, and they contain these exact canonical groups:

```python
EXPECTED = {
    "docs/02-hardware-basics/06-controller-and-firmware.md": (
        "中央处理器（Central Processing Unit, CPU）",
        "微控制器（Microcontroller Unit, MCU）",
        "STM32 微控制器（STM32 Microcontroller）",
        "固件（Firmware）",
        "构建",
        "烧录",
        "回滚",
    ),
    "docs/02-hardware-basics/07-electrical-interfaces-communication.md": (
        "通用串行总线（Universal Serial Bus, USB）",
        "串行端口（Serial Port）",
        "通用异步收发传输器（Universal Asynchronous Receiver-Transmitter, UART）",
        "控制器局域网（Controller Area Network, CAN）",
        "波特率（Baud Rate）",
        "数据长度代码（Data Length Code, DLC）",
        "块校验字符（Block Check Character, BCC）",
    ),
    "docs/02-hardware-basics/08-sensors-and-feedback.md": (
        "编码器（Encoder）",
        "惯性测量单元（Inertial Measurement Unit, IMU）",
        "巨磁阻（Giant Magnetoresistance, GMR）编码器",
        "霍尔效应编码器（Hall Effect Encoder）",
        "有机发光二极管（Organic Light-Emitting Diode, OLED）",
        "激光雷达（Light Detection And Ranging, LiDAR）",
    ),
    "docs/02-hardware-basics/09-chassis-motion-control.md": (
        "底盘运动模型（Chassis Kinematics）",
        "里程计（Odometry）",
        "电机驱动器（Motor Driver）",
        "脉宽调制（Pulse-Width Modulation, PWM）",
        "比例—积分—微分控制（Proportional–Integral–Derivative Control, PID）",
    ),
}
```

Also assert none of the five new pages contains `**`.

- [ ] **Step 2: Run the new tests and confirm missing-file failures**

```powershell
python -m pytest tests/test_hardware_foundations.py -q
```

Expected: four chapter paths and the part index are missing.

- [ ] **Step 3: Write Chapter 6 and the part index**

Use these exact H2 headings:

```text
## 6.1 主控与控制板
## 6.2 CPU、MCU 与 STM32
## 6.3 源码、固件与构建结果
## 6.4 烧录与回滚
## 6.5 电源域、信号域与功率级
## 6.6 观察练习
## 6.7 本章小结
## 章节导航
```

The prose must explain the causal chain before introducing commands. Do not include any flashing command or board-specific pin.

- [ ] **Step 4: Write Chapter 7**

Use these exact H2 headings:

```text
## 7.1 接线前先分清电气条件
## 7.2 USB 与串行端口
## 7.3 UART、USART 与逻辑电平
## 7.4 CAN 总线
## 7.5 字节流、数据帧与校验
## 7.6 GPIO、I²C、SPI 与 DMA
## 7.7 本章小结与观察练习
## 章节导航
```

The CAN paragraph must introduce the full term before the abbreviation is used in prose.

- [ ] **Step 5: Write Chapter 8**

Use these exact H2 headings:

```text
## 8.1 环境信息与机器人自身状态
## 8.2 编码器怎样记录转动
## 8.3 GMR 与霍尔效应编码器
## 8.4 IMU 怎样测量运动
## 8.5 OLED 是状态窗口
## 8.6 激光雷达、相机与 GNSS
## 8.7 采样、时间与坐标方向
## 8.8 本章小结与观察练习
## 章节导航
```

- [ ] **Step 6: Write Chapter 9**

Use these exact H2 headings:

```text
## 9.1 机体坐标与底盘自由度
## 9.2 正运动学与逆运动学
## 9.3 从编码器到里程计
## 9.4 电机驱动器与 PWM
## 9.5 PI/PID 闭环控制
## 9.6 限幅、超时与停止
## 9.7 本章小结与观察练习
## 章节导航
```

- [ ] **Step 7: Link the temporary chapter chain without adding it to the manifest yet**

Until Task 3 moves the old chapters, Chapter 9's next link should target the existing `../02-bringup/06-identify-configuration.md`. Task 3 will replace it with `../03-bringup/10-identify-configuration.md`. The new part index links only to Chapters 6–9.

- [ ] **Step 8: Run targeted tests and quality checks**

```powershell
python -m pytest tests/test_hardware_foundations.py -q
python tools/quality.py check --root . --paths docs/02-hardware-basics
git diff --check
```

Expected: all pass; new pages contain no inline bold.

- [ ] **Step 9: Commit the new foundation content**

```powershell
git add -- docs/02-hardware-basics tests/test_hardware_foundations.py
git diff --cached --check
git commit -m "docs: add robot hardware foundation chapters"
```

---

### Task 3: Atomically renumber all chapters and rebuild navigation

**Files:**
- Move: every old numbered file under `docs/02-bringup/` through `docs/09-deployment-maintenance/`
- Move: each old part `index.md` and `system-acceptance-checklist.md`
- Modify: every moved Markdown file's H1/H2 numbers and chapter navigation
- Modify: `metadata/chapter-manifest.csv`
- Modify: `mkdocs.yml`
- Modify: `README.md`
- Modify: `docs/index.md`
- Modify: `docs/reading-paths.md`
- Modify: `tools/quality.py`
- Modify: `tools/scaffold.py`
- Modify: all tests that contain fixed chapter paths/numbers, including the files returned by the search command below

**Interfaces:**
- Consumes: new Chapters 6–9 and the old manifest's exact old path/number pairs.
- Produces: ten part directories, contiguous Chapters 1–50, and no numbered file in an old part directory.

- [ ] **Step 1: Change structural tests to the final 50-chapter contract and run them red**

Update `tests/test_renumbering.py`, `tests/test_navigation.py`, `tests/test_quality.py`, and `tests/test_foundations.py`:

```python
FINAL_PARTS = [
    "01-foundations",
    "02-hardware-basics",
    "03-bringup",
    "04-chassis-control",
    "05-ros2-development",
    "06-sensors-navigation",
    "07-stm32-firmware",
    "08-advanced-applications",
    "09-r680-platform",
    "10-deployment-maintenance",
]
```

Assertions must require:

```python
self.assertEqual(foundation_numbers, list(range(1, 10)))
self.assertEqual(chapter_numbers, list(range(10, 51)))
self.assertEqual(numbered_rows, list(range(1, 51)))
self.assertEqual(len(numbered), 50)
```

The navigation regex must accept Chinese part labels 一 through 十 and count 50 numbered entries.

Run:

```powershell
python -m pytest tests/test_renumbering.py tests/test_navigation.py tests/test_quality.py tests/test_foundations.py -q
```

Expected: failures still report nine parts/46 chapters and missing final directories.

- [ ] **Step 2: Record and verify the deterministic move rule**

Use this exact directory map and `new_number = old_number + 4`:

```powershell
$directoryMap = [ordered]@{
  '02-bringup' = '03-bringup'
  '03-chassis-control' = '04-chassis-control'
  '04-ros2-development' = '05-ros2-development'
  '05-sensors-navigation' = '06-sensors-navigation'
  '06-stm32-firmware' = '07-stm32-firmware'
  '07-advanced-applications' = '08-advanced-applications'
  '08-r680-platform' = '09-r680-platform'
  '09-deployment-maintenance' = '10-deployment-maintenance'
}
```

Before moving, resolve every source and destination beneath the repository root and abort if a destination exists unexpectedly. Use native PowerShell `Move-Item -LiteralPath` for directories/files; do not pass enumerated paths through `cmd.exe`.

- [ ] **Step 3: Move part indexes and numbered pages**

For each old manifest chapter, preserve the slug after the two-digit prefix and write the new two-digit prefix. Examples that define the rule:

```text
docs/02-bringup/06-identify-configuration.md
  -> docs/03-bringup/10-identify-configuration.md
docs/04-ros2-development/21-launch-and-parameters.md
  -> docs/05-ros2-development/25-launch-and-parameters.md
docs/09-deployment-maintenance/46-system-acceptance.md
  -> docs/10-deployment-maintenance/51-system-acceptance.md
```

Move `system-acceptance-checklist.md` with the deployment part without numbering it.

- [ ] **Step 4: Rewrite headings and local navigation mechanically**

For every moved chapter:

- Replace `# old.` with `# new.`.
- Replace every H2 prefix `old.` with `new.` while preserving anchors.
- Replace previous/next links using the final manifest order.
- Replace all relative links affected by directory moves.
- Preserve fenced code, tables, safety admonitions, and explicit heading anchors byte-for-byte except for numbered headings/paths that must change.

Use a temporary script outside the final shipped tree or delete it before committing; `tests/test_navigation.py::test_one_shot_migration_tools_are_not_shipped` must remain true.

- [ ] **Step 5: Rewrite the manifest and quality heading contracts**

`metadata/chapter-manifest.csv` must list:

- foundation rows 1–9,
- chapter rows 10–50,
- appendices A–D.

Add exact `FOUNDATION_HEADINGS_BY_NUMBER` entries for Chapters 6–9 matching Task 2. Shift every special engineering heading in `tools/quality.py` by +4:

```python
task_titles = {
    (22, 5): "源码包确认",
    (25, 5): "启动链源码追踪",
    (27, 5): "源码修改练习",
    (37, 5): "固件实验记录",
    (38, 5): "外设最小实验",
    (39, 3): "闭环前置检查",
    (41, 5): "ROS—串口—固件链",
}
```

Shift the special Chapter 43 schema to new Chapter 47.

- [ ] **Step 6: Rebuild MkDocs navigation and entry pages**

Update `mkdocs.yml` to ten parts with the exact directories/ranges above. Update README, homepage, reading paths, and all part indexes. Required reading-path sequences become:

```text
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10
1 → 4 → 5 → 22
10 → 11 → 12 → 13 → 14
1 → 4 → 5 → 22 → 29 → 30 → 31 → 32
10 → 21 → 46 → 47 → 49
```

The firmware path uses Chapters 37–41.

- [ ] **Step 7: Update every fixed path and chapter assertion**

Run:

```powershell
rg -l 'docs/(02-bringup|03-chassis-control|04-ros2-development|05-sensors-navigation|06-stm32-firmware|07-advanced-applications|08-r680-platform|09-deployment-maintenance)|(?:02-bringup|03-chassis-control|04-ros2-development|05-sensors-navigation|06-stm32-firmware|07-advanced-applications|08-r680-platform|09-deployment-maintenance)/' .github docs metadata tests tools README.md mkdocs.yml --glob '!site/**'
```

Update every returned path except the design/plan history under `docs/superpowers/`. At minimum this includes code-resource metadata, ROS example workflow/tests, concept-placement tests, diagram tests, source-walkthrough tests, STM32 lab tests, public-source-reference tests, Task 8 migration tests, and appendix links.

Then search semantic chapter references:

```powershell
rg -n '第\s*(?:[6-9]|[1-3][0-9]|4[0-6])\s*章|第[二三四五六七八九]篇' docs README.md tests metadata mkdocs.yml --glob '!docs/superpowers/**'
```

Map every old numbered reference with `new = old + 4`; review the surrounding title so dates, quantities, and model numbers are not rewritten.

- [ ] **Step 8: Run structural and link tests**

```powershell
$env:PYTHONUTF8='1'
python -m pytest tests/test_renumbering.py tests/test_navigation.py tests/test_quality.py tests/test_foundations.py tests/test_concept_placement.py tests/test_task8_migration.py -q
python tools/quality.py check --root .
git diff --check
```

Expected: all selected tests pass and quality reports no broken internal links.

- [ ] **Step 9: Commit the atomic renumbering**

```powershell
git add -- .github docs metadata tests tools README.md mkdocs.yml
git diff --cached --check
git commit -m "docs: renumber textbook into ten parts"
```

---

### Task 4: Remove the old-URL redirect subsystem

**Files:**
- Delete: `metadata/legacy-redirects.csv`
- Delete: `tools/generate_redirects.py`
- Delete: `tests/test_redirects.py`
- Modify: `.github/workflows/deploy-docs.yml`
- Modify: `tools/build_site.ps1`
- Modify: `tests/test_deployment.py`
- Modify: `tests/test_renumbering.py`
- Modify: `tests/test_task8_migration.py`

**Interfaces:**
- Consumes: final new paths from Task 3.
- Produces: direct MkDocs/Pages publication with no generated compatibility pages.

- [ ] **Step 1: Write failing absence and workflow-order tests**

Replace redirect expectations with:

```python
def test_legacy_redirect_subsystem_is_absent() -> None:
    for relative in (
        "metadata/legacy-redirects.csv",
        "tools/generate_redirects.py",
        "tests/test_redirects.py",
    ):
        assert not (ROOT / relative).exists()


def test_pages_workflow_builds_then_uploads_site() -> None:
    workflow = (ROOT / ".github/workflows/deploy-docs.yml").read_text(encoding="utf-8")
    assert "mkdocs build --strict" in workflow
    assert "generate_redirects.py" not in workflow
    assert workflow.index("mkdocs build --strict") < workflow.index("upload-pages-artifact")
```

Update the local-build test to require `build --strict` and reject `generate_redirects.py`.

- [ ] **Step 2: Run deployment/renumbering tests red**

```powershell
python -m pytest tests/test_deployment.py tests/test_renumbering.py tests/test_task8_migration.py -q
```

Expected: failures show the three redirect artifacts and workflow steps still exist.

- [ ] **Step 3: Delete redirect artifacts and calls**

Use `apply_patch` to delete the CSV, generator, and test file. Remove the generation step from GitHub Actions and the final generator invocation from `tools/build_site.ps1`. Remove imports/assertions from renumbering and Task 8 tests.

- [ ] **Step 4: Prove no compatibility code remains**

```powershell
rg -n 'legacy-redirect|generate_redirects|redirect chain|legacy redirects' .github tools tests README.md mkdocs.yml metadata
```

Expected: no output.

- [ ] **Step 5: Run deployment tests and a strict local build**

```powershell
python -m pytest tests/test_deployment.py tests/test_renumbering.py tests/test_task8_migration.py -q
powershell -ExecutionPolicy Bypass -File tools/build_site.ps1
```

Expected: tests pass; local build ends after MkDocs strict build without a redirect count.

- [ ] **Step 6: Commit redirect removal**

```powershell
git add -- .github/workflows/deploy-docs.yml tools/build_site.ps1 tests/test_deployment.py tests/test_renumbering.py tests/test_task8_migration.py
git add -u -- metadata/legacy-redirects.csv tools/generate_redirects.py tests/test_redirects.py
git diff --cached --check
git commit -m "build: remove legacy textbook redirects"
```

---

### Task 5: Assign canonical terms and clean Parts 1–4

**Files:**
- Modify: `metadata/terminology.csv`
- Modify: `docs/glossary.md`
- Modify: `docs/01-foundations/*.md`
- Modify: `docs/02-hardware-basics/*.md`
- Modify: `docs/03-bringup/*.md`
- Modify: `docs/04-chassis-control/*.md`
- Modify: `tests/test_terminology_ownership.py`

**Interfaces:**
- Consumes: Task 1 audit, Task 2 foundation content, Task 3 final paths.
- Produces: canonical ownership for all general, hardware, communication, sensor, and control terms; downstream task prose without repeated full definitions.

- [ ] **Step 1: Migrate the CSV schema and assign all general/hardware owner groups**

Add `canonical_path` and `canonical_anchor`. Use this exact ownership for every existing general/hardware row:

```text
Chapter 1: ROS, ROS 2
Chapter 3: OS, terminal, file, directory, process, Shell, SSH
Chapter 5: node, topic, publisher, subscriber, service, action, parameter
Chapter 2: sensor
Chapter 6: CPU, GPU, MCU, STM32, firmware, EEPROM
Chapter 7: USB, serial communication, serial port, baud rate, UART, USART,
           CAN, ID, DLC, BCC, GPIO, I²C, SPI, TTL
Chapter 8: encoder, IMU, GMR, Hall Effect Encoder, OLED, LiDAR, GNSS
Chapter 9: motor driver, chassis kinematics, odometry, PWM, PI, PID
Chapter 13: IP Address, VNC
```

Chapter 2 owns the generic sensor concept; Chapter 8 owns the specific sensor types. Rewrite earlier chapters to avoid USB/UART/CAN abbreviations before Chapters 7–8 rather than duplicating their definitions.

Every canonical anchor must be the explicit anchor attached to the matching H2 in Chapters 1–9. Add anchors where absent.

- [ ] **Step 2: Run scoped audit and observe duplicate failures**

```powershell
python tools/terminology_audit.py --root . --terms metadata/terminology.csv --paths docs/01-foundations docs/02-hardware-basics docs/03-bringup docs/04-chassis-control
```

Expected: duplicate full forms and inline bold are reported.

- [ ] **Step 3: Remove duplicate definitions from the real-robot task chapters**

Examples of required transformations:

```text
Before:
若控制板上有 CAN 接口，记录其连接对象。控制器局域网（Controller Area Network, CAN）是……

After:
检查控制板是否接入 CAN 总线（见第 7 章），并记录总线上的设备。
```

```text
Before:
固件（Firmware）是存放在控制板中……

After:
烧录前先核对第 6 章说明的固件与控制板对应关系。
```

Use one prerequisite paragraph per task chapter when multiple concepts share the same foundation page; do not add one link sentence per term.

- [ ] **Step 4: Remove inline bold from Parts 1–4**

Replace term bold with plain prose. Convert a bold label bullet such as “阅读与练习：” to a two-column table or H3 heading. Do not alter fenced code or admonition syntax.

- [ ] **Step 5: Normalize the glossary**

Keep one row per CSV rule, use the exact `first_use` string in the term column, and make definitions concise. The glossary may repeat full forms; it must not use inline bold.

- [ ] **Step 6: Run scoped audit, chapter tests, and editorial scan**

```powershell
python tools/terminology_audit.py --root . --terms metadata/terminology.csv --paths docs/01-foundations docs/02-hardware-basics docs/03-bringup docs/04-chassis-control
python -m pytest tests/test_foundations.py tests/test_hardware_foundations.py tests/test_concept_placement.py -q
$report=Join-Path $env:TEMP 'terms-parts-1-4.json'
python tools/editorial_audit.py scan --paths docs/01-foundations docs/02-hardware-basics docs/03-bringup docs/04-chassis-control --report $report
```

Expected: zero terminology/editorial findings and all selected tests pass.

- [ ] **Step 7: Commit Parts 1–4 cleanup**

```powershell
git add -- metadata/terminology.csv docs/glossary.md docs/01-foundations docs/02-hardware-basics docs/03-bringup docs/04-chassis-control tests/test_terminology_ownership.py
git diff --cached --check
git commit -m "docs: centralize hardware terminology foundations"
```

---

### Task 6: Assign canonical terms and clean Parts 5–6

**Files:**
- Modify: `metadata/terminology.csv`
- Modify: `docs/glossary.md`
- Modify: `docs/05-ros2-development/*.md`
- Modify: `docs/06-sensors-navigation/*.md`
- Modify: related tests under `tests/`

**Interfaces:**
- Consumes: canonical hardware terms from Task 5.
- Produces: unique ROS engineering, mapping/navigation, and vision term ownership.

- [ ] **Step 1: Assign exact owner groups**

```text
Chapter 22: Docker, Host, Container, Image
Chapter 23: workspace, package
Chapter 24: DDS, QoS, Domain ID
Chapter 25: Launch, YAML, remapping
Chapter 26: TF2, URDF, Xacro, RViz, XML
Chapter 30: SLAM
Chapter 31: EKF
Chapter 32: Navigation2/Nav2
Chapter 33: RRT
Chapter 34: OpenCV, cv_bridge
Chapter 36: KCF, AR Tag
```

Nodes/topics/services/actions remain owned by Chapter 5; Chapter 24 adds engineering compatibility without repeating their full definitions. LiDAR, camera, IMU, and encoder remain owned by Chapter 8.

- [ ] **Step 2: Run scoped audit red**

```powershell
python tools/terminology_audit.py --root . --terms metadata/terminology.csv --paths docs/05-ros2-development docs/06-sensors-navigation
```

Expected: current duplicate full forms and inline bold are reported.

- [ ] **Step 3: Rewrite conceptual flow without definition patches**

- Chapter 22 explains environment selection and Docker boundaries.
- Chapter 23 explains workspace/package/build relationships.
- Chapter 24 begins from running nodes and adds DDS/QoS/Domain checks.
- Chapter 25 explains Launch/parameter precedence before source tracing.
- Chapter 26 uses the sequence model description → TF publication → RViz display.
- Chapters 29–36 use device → driver/node → topic → time/frame → algorithm.

Remove duplicate hardware definitions and replace them with at most one prerequisite link per chapter.

- [ ] **Step 4: Remove all inline bold from Parts 5–6**

Run `rg -n '\*\*[^*]+\*\*' docs/05-ros2-development docs/06-sensors-navigation` and rewrite every hit using headings, tables, or plain prose.

- [ ] **Step 5: Run scoped and concept-placement tests**

```powershell
python tools/terminology_audit.py --root . --terms metadata/terminology.csv --paths docs/05-ros2-development docs/06-sensors-navigation
python -m pytest tests/test_concept_placement.py tests/test_ros2_examples.py tests/test_source_walkthrough.py tests/test_workflows.py -q
python tools/quality.py check --root . --paths docs/05-ros2-development docs/06-sensors-navigation
```

Expected: all pass with no audit findings.

- [ ] **Step 6: Commit Parts 5–6 cleanup**

```powershell
git add -- metadata/terminology.csv docs/glossary.md docs/05-ros2-development docs/06-sensors-navigation tests
git diff --cached --check
git commit -m "docs: centralize ROS and navigation terminology"
```

Before committing, verify `git diff --cached --name-only` includes only tests actually changed for this task; unstage an unrelated test with `git restore --staged -- tests/test_unrelated.py`.

---

### Task 7: Assign remaining terms, clean Parts 7–10, and enable the global gate

**Files:**
- Modify: `metadata/terminology.csv`
- Modify: `docs/glossary.md`
- Modify: `docs/07-stm32-firmware/*.md`
- Modify: `docs/08-advanced-applications/*.md`
- Modify: `docs/09-r680-platform/*.md`
- Modify: `docs/10-deployment-maintenance/*.md`
- Modify: `docs/appendices/*.md`
- Modify: `docs/index.md`
- Modify: `docs/reading-paths.md`
- Modify: `tools/quality.py`
- Modify: `tests/test_editorial_style.py`
- Modify: `tests/test_terminology_ownership.py`

**Interfaces:**
- Consumes: Tasks 5–6 canonical ownership and Task 1 audit.
- Produces: complete 83-term ownership, no public inline bold, and a full-tree terminology gate in normal quality checks.

- [ ] **Step 1: Assign exact remaining owner groups**

```text
Chapter 37: RTOS, FreeRTOS, DMA, interrupt
Chapter 38: board-level GPIO/UART/PWM/encoder implementation details only;
            full general definitions remain in Chapters 7–9
Chapter 42: Gazebo, World, Plugin
Chapter 43: Qt
Chapter 44: deep learning, inference, confidence score;
            CPU and GPU remain owned by Chapter 6
Chapter 45: AI, TTS, API, multimodal large language model
Chapter 46: R680 platform names only; OLED/GMR/Hall remain owned by Chapter 8
Chapter 48: NFS; Docker remains owned by Chapter 22
Chapter 49: Hash Value, System Image
```

Add AI and TTS to the CSV because they recur across the advanced-application and navigation prose. Keep deep learning, inference, confidence score, interrupt, and multimodal large language model as local full-name explanations without new abbreviations unless the final occurrence count shows reuse outside their owner chapter.

Framework names without stable Chinese translations use `English Full Name（ABBR）` exactly as specified in the CSV.

- [ ] **Step 2: Remove repeated definitions and inline bold from Parts 7–10 and appendices**

Task chapters must use the established term directly or link its owner. Preserve all safety admonitions and code-resource anchors. Remove every public double-asterisk inline-emphasis hit, including homepage and part indexes.

- [ ] **Step 3: Enable full terminology checking in quality.py**

At the end of `check_all()` add:

```python
issues.extend(check_terminology(root, paths))
```

Ensure `paths=None` audits all public docs and a scoped `--paths` run audits only those pages while still validating the referenced canonical pages.

- [ ] **Step 4: Add regression tests for the originally reported failures**

Add exact tests:

```python
def test_can_is_defined_once_before_task_use() -> None:
    rules = load_rules(ROOT / "metadata/terminology.csv")
    can = next(rule for rule in rules if rule.abbreviation == "CAN")
    assert can.canonical_path == "docs/02-hardware-basics/07-electrical-interfaces-communication.md"
    assert audit_rules(ROOT, rules) == []


def test_firmware_full_form_is_not_reintroduced() -> None:
    full = "固件（Firmware）"
    occurrences = []
    for path in find_public_pages(ROOT):
        if path.as_posix().endswith("docs/glossary.md"):
            continue
        occurrences.extend([path] * path.read_text(encoding="utf-8").count(full))
    assert occurrences == [ROOT / "docs/02-hardware-basics/06-controller-and-firmware.md"]


def test_public_reader_pages_have_no_inline_bold() -> None:
    offenders = []
    for path in find_public_pages(ROOT):
        if "**" in path.read_text(encoding="utf-8"):
            offenders.append(path.relative_to(ROOT).as_posix())
    assert offenders == []
```

- [ ] **Step 5: Run the full terminology and quality gates**

```powershell
$env:PYTHONUTF8='1'
python tools/terminology_audit.py --root . --terms metadata/terminology.csv
python tools/quality.py check --root . --editorial-strict
python -m pytest tests/test_terminology_ownership.py tests/test_editorial_style.py -q
git diff --check
```

Expected: zero issues and all tests pass.

- [ ] **Step 6: Commit remaining content and global gate**

```powershell
git add -- metadata/terminology.csv docs/glossary.md docs/07-stm32-firmware docs/08-advanced-applications docs/09-r680-platform docs/10-deployment-maintenance docs/appendices docs/index.md docs/reading-paths.md tools/quality.py tests/test_editorial_style.py tests/test_terminology_ownership.py
git diff --cached --check
git commit -m "docs: enforce canonical terminology ownership"
```

---

### Task 8: Refresh reader tests and perform final publication verification

**Files:**
- Modify: `tests/reader-tasks.md`
- Modify: `tests/reader-test-results.md`
- Modify: any final test files exposed by the full suite
- Review: all public Markdown, metadata, workflows, and build scripts

**Interfaces:**
- Consumes: final ten-part tree and global terminology audit.
- Produces: reader evidence that Chapters 1–9 close prerequisites before Chapter 10 and publication evidence for the final tree.

- [ ] **Step 1: Replace reader questions with the final learning dependencies**

Keep ten questions, including these exact checks:

```text
6. 主控、控制板、STM32 和固件分别是什么？
7. USB、串口、UART 与 CAN 有什么区别？
8. 编码器、IMU、OLED、GMR 和霍尔编码器分别提供什么信息？
9. 运动学、里程计、PWM 与 PI/PID 如何组成底盘闭环？
10. 进入第 10 章前，读者还缺少哪些硬件或控制概念？
```

The expected result for Question 10 is “none of the concepts required by the real-robot entry checklist.”

- [ ] **Step 2: Run a fresh-reader review against only the final public docs**

Use a context-isolated reviewer. Give it `tests/reader-tasks.md` and the public docs, but not this conversation, spec, plan, or prior reader results. Require PASS/UNCLEAR, cited pages, and assumed prior knowledge for each question.

Record the result in `tests/reader-test-results.md`. Any UNCLEAR result about a required prerequisite returns to the responsible chapter; do not add definitions to downstream task pages.

- [ ] **Step 3: Run the full repository test and audit suite**

```powershell
$env:PYTHONUTF8='1'
python -m pytest tests -q
python tools/terminology_audit.py --root . --terms metadata/terminology.csv
python tools/quality.py check --root . --editorial-strict
$report=Join-Path $env:TEMP 'wheeltec-final-editorial.json'
python tools/editorial_audit.py scan --paths docs --report $report
git diff --check
```

Expected: pytest has zero failures; terminology, quality, and editorial audits report zero findings.

- [ ] **Step 4: Run strict site build and inspect the rendered navigation**

```powershell
powershell -ExecutionPolicy Bypass -File tools/build_site.ps1
```

Expected: MkDocs strict build succeeds, the log contains no unlisted public chapter, and no redirect count is printed.

Open the built site and verify desktop/mobile navigation shows ten parts and Chapters 1–50. Inspect Chapters 6–10, 22–26, 29–32, and 37–41 for readable paragraph flow and absence of inline bold.

- [ ] **Step 5: Prove old paths and redirect infrastructure are absent**

```powershell
rg -n '02-bringup|03-chassis-control|04-ros2-development|05-sensors-navigation|06-stm32-firmware|07-advanced-applications|08-r680-platform|09-deployment-maintenance|legacy-redirect|generate_redirects' .github docs metadata tests tools README.md mkdocs.yml --glob '!docs/superpowers/**' --glob '!site/**'
```

Expected: no output.

- [ ] **Step 6: Commit final reader evidence and integration fixes**

```powershell
git add -- tests/reader-tasks.md tests/reader-test-results.md
git add -- tools/quality.py tests/test_terminology_ownership.py tests/test_navigation.py
git diff --cached --check
git commit -m "test: verify restructured textbook reading paths"
```

The second staging command is harmless when those integration files are unchanged. If a different integration file changed, add its explicit path only after reviewing `git diff --name-only`.

- [ ] **Step 7: Final clean-tree and commit-range review**

```powershell
git status --short --branch
git log --oneline --decorate -10
git diff 5dde304..HEAD --check
```

Expected: clean worktree; commit range contains one scoped commit per task; no whitespace errors.

Do not push or publish until the user explicitly requests publication after reviewing the final result.
