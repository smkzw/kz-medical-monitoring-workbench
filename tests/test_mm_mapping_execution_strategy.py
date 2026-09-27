"""门路径兼容转发：本文件与 tests/medical_monitoring/test_mm_mapping_execution_strategy.py
是同一测试集（C2原定位置在medical_monitoring子目录；对照门按顶层路径引用）。

本文件只做转发导入，不复制任何断言——测试集单点维护，双路径可寻址，
两处运行结果一致。修改用例请编辑medical_monitoring子目录下的原文件。
"""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT), str(_ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from medical_monitoring.test_mm_mapping_execution_strategy import *  # noqa: F401,F403
