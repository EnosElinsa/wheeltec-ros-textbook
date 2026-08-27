from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB_PATH = "06-stm32-firmware/stm32-peripheral-labs.md"
LAB_LINK = "stm32-peripheral-labs.md"


class Stm32PeripheralLabTests(unittest.TestCase):
    def test_lab_page_is_published_and_linked_from_related_chapters(self) -> None:
        lab = ROOT / "docs" / LAB_PATH
        self.assertTrue(lab.is_file())
        self.assertIn(LAB_PATH, (ROOT / "mkdocs.yml").read_text(encoding="utf-8"))

        related_pages = (
            "docs/06-stm32-firmware/33-firmware-architecture-freertos.md",
            "docs/06-stm32-firmware/34-hardware-init-model-interfaces.md",
            "docs/06-stm32-firmware/35-motor-control-pid.md",
        )
        missing = [
            path
            for path in related_pages
            if LAB_LINK not in (ROOT / path).read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [])

    def test_each_lab_has_an_observation_and_stop_condition(self) -> None:
        lab = ROOT / "docs" / LAB_PATH
        self.assertTrue(lab.is_file(), "STM32 peripheral lab page is missing")
        text = lab.read_text(encoding="utf-8")
        for heading in (
            "## 实验一：串口收发与回环",
            "## 实验二：PWM 频率与占空比",
            "## 实验三：编码器计数与方向",
        ):
            start = text.index(heading)
            next_heading = text.find("\n## ", start + len(heading))
            section = text[start:] if next_heading == -1 else text[start:next_heading]
            self.assertIn("### 预期观察", section)
            self.assertIn("### 停止条件", section)

    def test_page_does_not_present_local_examples_as_portable_firmware(self) -> None:
        lab = ROOT / "docs" / LAB_PATH
        self.assertTrue(lab.is_file(), "STM32 peripheral lab page is missing")
        text = lab.read_text(encoding="utf-8")
        for phrase in (
            "STM32F103C8T6",
            "不能据此形成烧录建议",
            "不提供原始归档或固件下载",
            "待实机验证",
        ):
            self.assertIn(phrase, text)

    def test_lab_instructions_cover_electrical_and_measurement_edge_cases(self) -> None:
        text = (ROOT / "docs" / LAB_PATH).read_text(encoding="utf-8")
        for phrase in (
            "不连接 USB-TTL 的 VCC",
            "十六进制发送",
            "PWM2 为其补值",
            "端点只验收直流电平",
            "按 `int16_t` 解释",
            "PC 端把各窗口的有符号增量求和",
            "实测时间窗",
            "断电后交换 A/B 相",
            "静态校对",
            "历史构建",
            "当前构建",
            "实机验证",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
