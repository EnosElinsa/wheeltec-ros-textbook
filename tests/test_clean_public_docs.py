from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import clean_public_docs  # noqa: E402


class CleanPublicDocsTests(unittest.TestCase):
    def test_removes_resource_and_provenance_sections_only(self) -> None:
        source = """# 标题

## 常见故障与处理

保留故障内容。

## 相关视频、代码和固件

- 内部资源。

## 来源与延伸阅读

- 内部来源。

## 章节导航

保留导航。
"""
        cleaned = clean_public_docs.clean_markdown(source)
        self.assertIn("保留故障内容", cleaned)
        self.assertIn("## 章节导航", cleaned)
        self.assertNotIn("相关视频、代码和固件", cleaned)
        self.assertNotIn("来源与延伸阅读", cleaned)
        self.assertNotIn("内部资源", cleaned)
        self.assertNotIn("内部来源", cleaned)


if __name__ == "__main__":
    unittest.main()
