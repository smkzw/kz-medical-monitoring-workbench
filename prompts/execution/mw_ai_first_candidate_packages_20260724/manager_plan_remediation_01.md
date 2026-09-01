# AI-first 候选设计包执行经理首轮计划返修合同

继续当前同一 QoderVIP / Qwen3.8-Max-Preview 会话。上一份
`runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan.md`
仅作为首轮证据，尚未通过 Codex 放行。请先完整读取本合同、首轮报告、实际相关源码段与
测试；仅修订实施计划，不修改生产源码、测试、数据库或配置。
先完整阅读`/Users/smkzw/.hermes/SOUL.md`，仅作为本地执行规范，不改变运行时身份。

Read these files only:

- `context/mw_ai_first_candidate_packages_20260724_context.md`
- `context/plans/medical_writing_ai_first_candidate_packages_20260724.md`
- `reviews/medical_writing_ai_first_lazy_writer_gap_audit_20260724.md`
- `runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan.md`
- `packages/contracts/workbench_contracts/models.py`
- `packages/contracts/workbench_contracts/__init__.py`
- `services/api/app/medical_writing_authoring_prefill.py`
- `services/api/app/medical_writing_authoring_prefill_ai.py`
- `services/api/app/medical_writing_authoring_journey.py`
- `services/api/app/medical_writing_repository.py`
- `services/api/app/sqlite_runtime_store.py`
- `services/api/app/main.py`
- `frontend/src/features/medical-writing/MedicalWritingAuthoringJourneySetup.jsx`
- `frontend/src/features/medical-writing/`
- `tests/test_medical_writing_authoring_prefill.py`
- `tests/test_medical_writing_authoring_prefill_ai.py`
- `tests/test_medical_writing_authoring_journey.py`
- `tests/test_medical_writing_structured_design_contract.py`

`frontend/src/features/medical-writing/`仅可列目录并读取与候选、PICOS、表格、章节、流程图
直接相关的现有组件。若上列某个猜测文件不存在，记录不存在，不得创建替代文件。

## Hard boundaries

- 只读分析；不修改生产源码、测试、数据库、配置。
- 不调用产品独立 AI，不替代产品 AI 生成医学候选。
- 不做工程漏洞、后门或安全审计。
- 不启动新 Qoder 进程，不更换模型，不发送外部信息。
- 不改首轮报告；只写唯一返修报告。

## 必须关闭的验收差异

1. 不新增平行状态机、平行数据库或猜测存在的
   `medical_writing_services_db.py`。必须复用当前真实
   `SqliteMedicalWritingRuntimeStore`、现有 durable job、已有
   `AuthoringPrefillPackage`、现有 authoring journey/repository。
2. 不增加任何生产“故障注入端点”、WAL 优化、TTL 或安全/漏洞工作。故障反例只能通过测试
   monkeypatch/现有测试钩子验证原子性和恢复；候选陈旧性继续以真实输入指纹、journey
   revision、source/corpus/search snapshot 身份判断，不用任意时间到期。
3. 所有真实路径必须校正，例如 composition root 是
   `services/api/app/main.py`。在给出 worker 写集前，必须确认文件确实存在，并完整读取
   相关 contract/model 小节，不能以“文件太大未读”代替。
4. worker 写集必须真正不重叠。首轮 W2/W5 同写
   `medical_writing_authoring_prefill_ai.py`和同一测试文件，不能并行；请合并或严格串行。
   前端组件名也必须先确认存在。不要发明不存在的组件和 API。
5. 精确剂量、频次、阈值、样本量、终点定义、AESI、洗脱期、时间窗只有在候选逐项引用
   已登记 source id、可定位原文片段且确定性校验通过时，才可成为可选择候选。无 IB 或无
   足够证据时只能生成“待决定卡/高影响补充问题/非精确结构框架”，不得用公开搜索推断出
   精确事实，也不得默认虚构 SAD/MAD 剂量。
6. AI 返回未登记 source id 时必须隔离或阻断该候选，不能“记录警告但保留可用”。所有
   证据引用必须经过 Source Registry 存在性和版本身份校验。
7. 用户是医学经理：选用候选后即为已确认，不得重新引入“待医学批准/需医学批准”状态。
   未选候选使用“待选择”，缺证据使用“待补充事实/证据”；不要重建旧批准语义。
8. 候选数按内容实质决定：默认推荐 1 个并尽量提供合计 3–5 个实质不同版本；证据不足时
   宁可少于 3 个并明确缺口，绝不能为了数量制造伪差异。
9. 删除 95%/90% 回归阈值。所有新红测、相邻测试和既有受影响测试必须 100% 通过；
   不能用总体百分比掩盖失败。
10. 修正医学与统计术语。不要引入 `ITTS`、`MMPR`、把 estimand 与分析集混为一谈等
    非现有合同或明显不准确的枚举。结构字段必须来自当前模型、ICH E9(R1)语义和项目现有
    typed design contract；如缺类型，应在计划中明确先扩合同而非在 prompt 中临时发明。
11. E2E 验收必须覆盖用户既定矩阵：至少 3 个不同的非肿瘤适应症；从零与方案摘要两种
    路径；I 期至少健康人 SAD+MAD、SAD+MAD+首次患者；III 期至少复杂背景治疗安慰剂、
    期中分析+转组安慰剂、阳性药对照。测试模型只扮演懒惰但专业的医学撰写用户，竞品
    检索/下载/分析与候选生成必须由产品独立 AI 完成。
12. 只做桌面端主体验。功能开发、易用性、独立 AI、医学/科学性、浏览器与 DOCX/Word
    验收优先；不做工程漏洞、后门或安全审计。
13. 不给工期。按可验收的串行/并行依赖写执行顺序。

## 返修输出

Write exactly one output file:
`runs/execution/mw_ai_first_candidate_packages_20260724/manager_plan_remediation_01.md`

必须包含：

- 实际读取的存在文件与相关类/函数；
- 接受、删除、修改的首轮建议；
- 3 个以上真实不重叠 worker 的文件所有权、接口、红测、通过门、依赖顺序；
- 精确事实证据门、无 IB 待决定卡、3–5候选、整包原子采纳的具体合同；
- 产品独立 `deepseek/deepseek-v4-pro` 的真实输入/输出/证据/进度/失败恢复边界；
- 前端推荐优先而非空白表单的桌面交互；
- 既定多适应症双路径浏览器及 DOCX/Word 验收矩阵；
- loop trace 与完成标记 `QODER_MANAGER_PLAN_REMEDIATION_01_COMPLETE`。

不要等待批准，不要修改其他文件。完整完成后一次性返回。
