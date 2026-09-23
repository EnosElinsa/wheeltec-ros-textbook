from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class Stm32PeripheralLabMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.architecture = (
            ROOT / "docs/07-stm32-firmware/40-firmware-architecture-freertos.md"
        ).read_text(encoding="utf-8")
        self.labs = (
            ROOT / "docs/07-stm32-firmware/41-hardware-init-model-interfaces.md"
        ).read_text(encoding="utf-8")
        self.control = (
            ROOT / "docs/07-stm32-firmware/42-motor-control-pid.md"
        ).read_text(encoding="utf-8")

    def test_each_lab_keeps_observation_and_stop_conditions(self) -> None:
        for heading in (
            "### 实验一：串口收发与回环",
            "### 实验二：PWM 频率与占空比",
            "### 实验三：编码器计数与方向",
        ):
            start = self.labs.index(heading)
            next_heading = self.labs.find("\n### ", start + len(heading))
            section = self.labs[start:] if next_heading == -1 else self.labs[start:next_heading]
            self.assertIn("#### 预期观察", section)
        self.assertGreaterEqual(self.control.count("停止条件"), 3)

    def test_labs_do_not_present_f103_examples_as_portable_firmware(self) -> None:
        combined = self.architecture + self.labs + self.control
        for phrase in (
            "STM32F103C8T6",
            "不能据此形成烧录建议",
            "不提供可直接烧录的固件文件",
            "待实机验证",
            "静态校对",
            "历史构建",
            "当前构建",
            "实机验证",
        ):
            self.assertIn(phrase, combined)

    def test_lab_instructions_keep_electrical_and_measurement_edge_cases(self) -> None:
        for phrase in (
            "不连接 USB-TTL 的 VCC",
            "十六进制发送",
            "PWM2 为其补值",
            "端点只验收直流电平",
            "按 `int16_t` 解释",
            "PC 端把各窗口的有符号增量求和",
            "实测时间窗",
            "断电后交换 A/B 相",
        ):
            self.assertIn(phrase, self.labs)

    def test_unified_record_is_retained_in_chapter_33(self) -> None:
        for phrase in ("统一实验记录", "板卡与 MCU", "验收门槛", "安全状态"):
            self.assertIn(phrase, self.architecture)


if __name__ == "__main__":
    unittest.main()
