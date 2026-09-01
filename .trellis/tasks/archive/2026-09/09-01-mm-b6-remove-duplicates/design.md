# B6 技术设计：删除 POC 工作副本

## 目标与边界

把 `packages/medical_monitoring` 固化为唯一 Python 权威，删除七棵 R1–R7 POC 与独立的 R3 rule-ai POC。删除是迁移收尾，不改变路由、payload、中文医学语义、模型配置或用户界面；旧产品链 `services/api/app/monitoring_*` 保持冻结。

## 删除前依赖闭合

1. 产品包内四处残余兼容 import 必须先归一：
   - `runtime/continuity_bridge.py` 改用相邻 `continuity`、`launch_registry`；
   - `runtime/profile_store.py` 与 `runtime/background_recovery.py` 改用已迁移的 `runtime.agent_harness`；
   - `projections/publication/s2_authority_builder.py` 的合成 D10 构造不得再依赖 `mm_r4.d10_adapter`。仅迁移其纯结构化 mapping→typed-object 转换，不迁移冻结 SHA、catalog、oracle、registry 或 quota。
2. 产品路由测试改用 `packages.medical_monitoring`；R7 的确定性 fake harness 移至 `tests/medical_monitoring/fake_harness.py`，不得为测试修改运行时 `sys.path`。
3. 删除只验证旧兼容模块身份的 `tests/medical_monitoring/test_domain_compatibility.py`。已迁移 authority 的行为由 package-native 产品/领域测试承担。
4. `services/api/app/__main__.py` 删除临时 `_ensure_r6_poc_importable`，合成启动不再认识 POC 路径。

## 删除与验证策略

- 先完成并提交依赖归一；运行产品路由、fixture、合成启动及 package-native 领域测试。
- 再用 `git rm -r` 删除八棵 POC；每棵文件均可从 git 历史恢复。
- 删除后以 `rg` 分开判定：`packages/`、`services/`、`frontend/src/`、当前产品测试不得有可执行 POC import；历史注释和 B7 待清理的冻结脚本只记录，不作为运行时阻断。
- 运行医学监查聚焦回归、前端医学监查 node 测试、Vite build 和医学写作保护性子集。预先存在的医学写作失败只做复现归因，不跨边界修复。

## 风险控制

- 不把测试 fixture、药物/疾病/量表/列名规则迁入产品权威。
- 不以删除 POC 为理由重写算法；只做 import、结构转换和测试辅助位置变更。
- 若删除后出现行为失败，优先补 package-native 测试或修正 import；不得恢复产品对 POC 的依赖。
