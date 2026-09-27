"""tests目录导入兼容（任意CWD/前缀路径收集时保证可导入）。

编排门从不同cwd引用本目录（workbench根、implementation/workbench存根、
项目父目录均有历史调用）。本conftest只做一件事：把workbench根
（packages/、services/所在）与tests目录（medical_monitoring包所在）
放入sys.path，使任何前缀路径收集到的用例都能完成导入；
不含任何fixture与断言，不改变任何既有行为。
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
