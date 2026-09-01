# 医学监查真实项目可见性边界 — 2026-08-02

## 结论

当前 15174/18911/18913 表面属于医学写作隔离运行时，进程环境明确设置
`WORKBENCH_INCLUDE_REFERENCE_PROJECTS=false`。因此 `/api/projects` 只展示用户项目，
浏览器进入该用户项目的“医学监查”会安全地显示“功能未配置”；这不是 MY009/RUX
适配器未注册，而是当前运行模式刻意不暴露参考/真实项目。

源码侧 `ProjectSourceManifestService` 默认目录包含八个规范项目，`main.py` 也已注册
RUX 与 MY009 监查服务；`scripts/start_stable_backend.zsh` 不强制关闭参考项目，说明
生产样式运行时与医学写作隔离运行时是两个不同的验收前提。

本切片不改变运行时或源码，不启动 8911/5174，不调用真实项目、不写 SQLite，也不触碰
并行医学写作。要获得真实 UI/科学性证据，必须先完成 B6 正式 reviewer outcome、
source-token lineage 与 aggregate/CAS 复核，再在单独的 reference-enabled 运行时做只读
approved-input 接线和三项目浏览器验收。

详细记录：
`records/active_slices/medical_monitoring_reference_visibility_boundary_20260802/`。
