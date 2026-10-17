#!/usr/bin/env python3
"""PII/机密扫描（pre-commit + CI）。检查工作区文件与git diff。

规则（08_EXECUTION_RULES §4）：
1. 二进制/办公文档扩展名出现在白名单目录外
2. 受试者号形态
3. /Users/ 绝对路径
4. 高熵字符串（gitleaks另跑，此处做轻量版）

用法：
  python3 scripts/ci/pii_scan.py [--staged]  # pre-commit模式
  python3 scripts/ci/pii_scan.py              # 全量扫描
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

# 白名单：这些目录下的文件不受二进制/文档扩展名限制
WHITELIST_DIRS = {
    "tests/fixtures/synthetic",
    "protocol-corpus/raw",  # M0期间先保留，filter-repo后再移除
    ".trellis",
}

BINARY_EXTS = {".xlsx", ".xls", ".pdf", ".docx", ".doc", ".pptx", ".zip", ".sqlite", ".db"}

SUBJECT_ID_PATTERNS = [
    re.compile(r"\bS0\d{4}\b"),  # S0xxxx
    re.compile(r"\b\d{3}-\d{3,4}\b"),  # 123-4567
]

ABS_PATH = re.compile(r"/Users/|C:\\Users\\")

# 高熵检测（简化版：连续44+的base62字符串）
HIGH_ENTROPY = re.compile(r"[A-Za-z0-9+/]{44,}={0,2}")


def is_whitelisted(path: str) -> bool:
    return any(path.startswith(w) or f"/{w}" in path for w in WHITELIST_DIRS)


def scan_file(path: Path, rel_path: str = "") -> list[str]:
    issues = []
    rel = rel_path or str(path.relative_to(path.parents[2]) if len(path.parents) > 2 else path)

    # 规则1：二进制/文档扩展名
    if path.suffix.lower() in BINARY_EXTS and not is_whitelisted(rel):
        issues.append(f"BLOCKED_EXT: {rel} (binary/document file outside whitelist)")

    # 文本文件内容检查
    if path.suffix.lower() in {".py", ".md", ".json", ".yaml", ".yml", ".txt", ".sh", ".ts", ".js", ".jsx", ".toml"}:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            return issues

        # 规则2：受试者号
        for pat in SUBJECT_ID_PATTERNS:
            for m in pat.finditer(content):
                issues.append(f"SUBJECT_ID: {rel}:{content[:m.start()].count(chr(10))+1} pattern={m.group()}")

        # 规则3：绝对路径
        for m in ABS_PATH.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            issues.append(f"ABS_PATH: {rel}:{line_no}")

        # 规则4：高熵字符串（只报，不阻止——可能误报base64 fixture）
        for m in HIGH_ENTROPY.finditer(content):
            line_no = content[:m.start()].count("\n") + 1
            token = m.group()[:20] + "..."
            issues.append(f"HIGH_ENTROPY: {rel}:{line_no} {token}")

    return issues


def main() -> int:
    root = Path(__file__).parent.parent.parent
    staged = "--staged" in sys.argv

    all_issues = []

    if staged:
        # pre-commit模式：只检查staged文件
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True, text=True, cwd=root
        )
        for line in result.stdout.strip().split("\n"):
            if line.strip():
                f = root / line.strip()
                if f.exists():
                    all_issues.extend(scan_file(f, line.strip()))
    else:
        # 全量模式：只扫git跟踪的文本文件（跳过venv/node_modules/runtime等）
        import subprocess
        result = subprocess.run(
            ["git", "ls-files"], capture_output=True, text=True, cwd=root
        )
        for line in result.stdout.strip().split("\n"):
            if not line.strip():
                continue
            f = root / line.strip()
            if f.exists():
                all_issues.extend(scan_file(f, line.strip()))

    if all_issues:
        # 分类：BLOCKED（阻止提交）vs WARN（警告）
        blocked = [i for i in all_issues if i.startswith("BLOCKED_EXT") or i.startswith("SUBJECT_ID") or i.startswith("ABS_PATH")]
        warns = [i for i in all_issues if i not in blocked]

        if blocked:
            print(f"❌ PII扫描发现 {len(blocked)} 个阻断性问题：")
            for i in blocked[:20]:
                print(f"  {i}")
            if len(blocked) > 20:
                print(f"  ...及另外 {len(blocked)-20} 个")
            print("\n修复方法：")
            print("  - BLOCKED_EXT: 将文件移入 tests/fixtures/synthetic/ 或 .gitignore")
            print("  - SUBJECT_ID: 替换为合成编号（如 SYN-001-0001）")
            print("  - ABS_PATH: 改用环境变量（MM_PROJECT_ROOT / MM_PRIVATE_ROOT）")
            return 1

        if warns:
            print(f"⚠️  PII扫描 {len(warns)} 个警告（不阻断）：")
            for i in warns[:5]:
                print(f"  {i}")

    print("✅ PII扫描通过" if not all_issues else f"✅ PII扫描通过（{len(warns)} 警告）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
