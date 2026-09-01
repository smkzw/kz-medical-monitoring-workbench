# R7 阶段复盘：Slice-09C 后与 09D 计划

日期：2026-08-30

09A 已闭合项目备份/恢复/导入导出，09B 已闭合 schema 升级/回滚，09C 已闭合根级业务审计、统一恢复核验与有界技术日志。当前唯一主缺口是不依赖真实项目的性能、容量和长任务恢复基线；历史 R5-S7 浏览器数字不可直接转成备份、恢复、读取或长任务的普适 SLO。

09D 顺序：冻结 T0–T4 synthetic corpus、shape/fanout 与独立 oracle；分别测量备份、恢复、公开读取、重开/恢复就绪和进度；冻结 process-cold/warm、7 次 screening 与 30 次边界确认；覆盖中断、lease/heartbeat、迟到回调、资源压力、ENOSPC、审计/日志降级；只报告当前机器/commit/corpus 的 observed capacity envelope。合同独立接受后才实施，09D 完成后才能复核 Slice-09/R7。

09D 不读取真实方案、IB、listing。R8 真实资料只作为隔离只读泛化挑战，不得成为 benchmark、提示调优语料或产品常量。listing 解构及药物/疾病提取归子系统独立 harness/LLM；Codex/确定性内核只负责提示、schema、identity/coverage/source-anchor 校验、挑战矩阵和失败语义，不补写医学答案。
