from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

EXPECTED = {
    "docs/02-hardware-basics/06-controller-and-firmware.md": (
        "中央处理器（Central Processing Unit, CPU）",
        "微控制器（Microcontroller Unit, MCU）",
        "STM32",
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


def test_four_foundation_chapters_exist_with_numbered_h1() -> None:
    for relative in EXPECTED:
        path = ROOT / relative
        assert path.is_file(), relative
        h1 = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("# "))
        number = relative.split("/")[-1][:2]
        assert re.match(rf"^# {int(number)}\.\s+", h1), h1


def test_foundation_pages_cover_canonical_term_groups_without_inline_bold() -> None:
    for relative, terms in EXPECTED.items():
        text = (ROOT / relative).read_text(encoding="utf-8")
        for term in terms:
            assert term in text, f"{relative} is missing {term}"
        assert "**" not in text, relative


def test_foundation_part_index_links_only_to_chapters_six_through_nine() -> None:
    index = ROOT / "docs/02-hardware-basics/index.md"
    text = index.read_text(encoding="utf-8")
    for slug in (
        "06-controller-and-firmware.md",
        "07-electrical-interfaces-communication.md",
        "08-sensors-and-feedback.md",
        "09-chassis-motion-control.md",
    ):
        assert slug in text


def test_hardware_chapters_form_a_progressive_system_model() -> None:
    chapter_7 = (ROOT / "docs/02-hardware-basics/07-electrical-interfaces-communication.md").read_text(
        encoding="utf-8"
    )
    chapter_8 = (ROOT / "docs/02-hardware-basics/08-sensors-and-feedback.md").read_text(
        encoding="utf-8"
    )
    chapter_9 = (ROOT / "docs/02-hardware-basics/09-chassis-motion-control.md").read_text(
        encoding="utf-8"
    )
    assert "第 6 章" in chapter_7
    assert "第 7 章" in chapter_8
    assert "第 8 章" in chapter_9
    forbidden = ("不等于", "不能单独", "不代表")
    for text in (chapter_7, chapter_8, chapter_9):
        for phrase in forbidden:
            assert phrase not in text, phrase
