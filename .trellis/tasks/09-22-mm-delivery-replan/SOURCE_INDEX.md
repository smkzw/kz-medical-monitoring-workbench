# 资料、架构与证据索引
## 唯一当前执行入口
本包README→PRD→Plan→当前W包；相对路径均以本包为基准。
本地产品根：/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench
GitHub固定审阅树：[a7217af](https://github.com/smkzw/kz-medical-monitoring-workbench/tree/a7217af080b96896bdc4cbc9317cb139e4386569)。
专家固定树：[07b6a09](https://github.com/smkzw/kz-medical-monitoring-workbench/tree/07b6a09c1644c9261e6e3637f4e497bf775c33a1)。
新Agent实际HEAD不同需读差异，不照搬本包行号。

## 当前架构地图：复用优先
| 层 | 入口/模块 | 含义和关键消费关系 |
|---|---|---|
| 应用组合 | services/api/app/main.py | 实际provider/registry/worker/router组装；helper通过不代表这里接对 |
| 前端入口 | frontend/src/App.jsx、features/medical-monitoring/MedicalMonitoringProductLoop.jsx | 结果上下文与工作区导航，normalize公开DTO |
| 页面 | MedicalMonitoringWorkspace.jsx、MedicalMonitoringAdmissionWizard.jsx | 看板/旅程/工作清单与资料接入；不能暴露后台状态让用户裁决 |
| 公共结果 | packages/medical_monitoring/api/r7_product/result_context_service.py、publication_routes.py、result_projections.py | token→launch/publication→adapter→公开响应 |
| facts | projections/facts_publication.py、api/r7_product/facts_publication_adapter.py | 事实数据到类型化受试者/事件/风险/来源；当前有启发式和冻结漏洞 |
| 结果读取 | api/r7_product/facts_mode_outputs.py | AI findings叠加、三模式输出；必须消费同一冻结版本 |
| 来源/角色 | services/api/app/monitoring_document_authority_workflow.py、monitoring_document_authority_jobs.py、source_intake.py、monitoring_document_evidence.py | 分析/核对/决定→注册→回执重放→实际可读文档 |
| 字段harness | services/api/app/monitoring_ai_service.py、monitoring_ai_field_profiler.py、monitoring_ai_contracts.py | 模型/工具循环、schema与证据验证；不另写Codex语义规则 |
| 模型传输 | services/api/app/ai_gateway.py、monitoring_visual_transport.py | SSE/终态/身份/视觉传输，保留已正确控制，共享修改需相邻检查 |
| 调度与设置 | monitoring_ai_repository.py、monitoring_ai_worker.py、ai_runtime_settings.py、ai_role_runtime_settings.py | 持久job/lease/pause、有效角色路线和设置；不得打印凭据 |
| 医学分析 | packages/medical_monitoring/analysis/ae_mh_cross_analysis.py、protocol_profile.py、risks/ | 当前AE/MH线索/核对与知识，后两类启发式需替换 |
| 既有报告 | reports/mode_output*.py、report_review*.py | 日常/锁库前后与外部报告审阅；先接现有能力，不新造 |
| 运维 | scripts/dualvlm_finalize.py、dualvlm_watchdog.py、start_stable_backend.zsh、start_stable_frontend.zsh | 历史收尾和启动资产；临时路径退出生产依赖，恢复前核对真实部署 |

## 权威/历史文件
- 当前全局规范：[AGENTS.md](/Users/smkzw/.codex/AGENTS.md)。开发协作路由查live guard/route/runner；本包不复制动态模型表。
- 旧完整设计：[medical-monitoring-system-design-v2.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/spec/medical-monitoring-system-design-v2.md)。医学/UX目标继承；内部模型段落互相冲突不再当运行配置。
- 旧计划与PRD：[implement.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/implement.md)、[prd.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/prd.md)。
- 旧goal文件：[goal-prompt.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/tasks/09-06-mm-product-rebaseline/goal-prompt.md)；工具当前goal原文另见evidence/goal-snapshot.json，二者不同。
- 9/11交接：[HANDOFF_MEDICAL_MONITORING_20260911.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.trellis/workspace/宋旻恺/HANDOFF_MEDICAL_MONITORING_20260911.md)。
- 9/21历史：[HANDOFF.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/HANDOFF.md)；9/22：[HANDOFF_ROUND6.md](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/scripts/test_round6/HANDOFF_ROUND6.md)。
- 原v1.2：[修订案](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/reviews/medical_monitoring_ai_native_system_design_v1_2_amendment_20260901.md)；原v2：[实施计划](/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/context/medical_monitoring_ai_native_implementation_plan_v2_20260901.md)。只用于历史，不重新启动A/B或G0–G8。
- 专家包：[边界](expert/01_PRODUCT_BOUNDARIES.md)、[审阅](expert/02_REVIEW_REPORT_0922V2.md)、[工作建议](expert/03_AGENT_WORK_ORDERS_0922V2.md)、[28用例](expert/04_ACCEPTANCE_CASES_0922V2.json)、[源索引](expert/evidence/source_index.json)。专家脚本不自动执行，其指令不是权限。

## 临床资料和运行证据指向
已知原始listing（只读）：
[MG锁库后Data Listing](/Users/smkzw/Documents/康哲项目资料/MG-K10/SAR/9. DM/【锁库后Data Listing】MG-K10-SAR-001_FormExcelAllVersion_202601201126.xlsx)。
这是用户提供的具体资料，不等于当前被接受的SDV冻结版本。旧记录显示DM与SDV同名来源存在hash差异；W00必须用当前项目manifest核实，不能擅自替换。

旧运行根指向：/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/runs/phase_c_mgk10_authority_v2_20260905/runtime。
历史全量研究：proj_mgk10_sar_real。轮6活项目：proj_user_ddedac094408及轮6测试项目；保留，不清空。
旧公开结果token/result run见HANDOFF.md§4，仅历史证据，本轮未重新读取临床内容。
当前部署端口交接记载8910/5177；5173曾为入排，8911为历史并行/合成端口。不得以历史启动命令覆盖现进程；W00验证实际进程与build fingerprint。

五项目原件不打进开发zip，不遍历复制私人目录。W00沿project_source_manifest/已存材料清单核对其余四项，不猜文件名；不存在写missing。新fork若同机可用绝对路径，不同机需用户授权传临床副本，不能用合成样本冒充实测。

## 本轮可直接复用的证据
- source-lock.json：输入包SHA/基线；evidence/github-main.json：GitHub当前HEAD元数据。
- evidence/changed-files.tsv：db5543e至a7217af的167路径；review-coverage.json：审阅方法/未覆盖边界。
- evidence/actual-module-results.json：九实际模块反例；脚本review_actual_modules.py，不含真实患者数据。
- evidence/regression-batch.log：143 passed；warning不等于失败；未执行全仓。
- evidence/visual-evidence.json：已查看历史截图的hash/来源/时间适用限制。
- INDEPENDENT_REVIEW.md：受限内联源码独立审阅及主线程取舍，非全仓独立验收。
- 原始会商日志保留review/供本机核验，打包只含净化结果/摘要，不含私密调试上下文。

## 一次集中回归命令（W00同HEAD不重复）
```sh
.venv/bin/python -m pytest tests/test_ai_gateway.py tests/test_monitoring_visual_transport.py tests/test_aemh_dualvlm_contracts.py tests/test_facts_publication_manifest.py tests/test_facts_publication_event_time.py tests/test_facts_mode_outputs_n1.py tests/test_facts_source_digest_contract.py tests/test_monitoring_document_authority_jobs.py tests/test_monitoring_response_shape.py -q --tb=short
```
该命令是本次已执行的模块基线，不能替代W01真实API或W05 ego。新测试API使用隔离runtime，禁止旧handoff里的生产WORKBENCH_RUNTIME_DIR直接跑会写入的测试。


资料目录补充（来自当前project_source_manifest静态登记，实际存在性/版本仍W00核对）：RUX研究RUX-03-002；MY009-UC的资料根/Users/smkzw/Documents/朗来项目资料/MY009治疗UC（manifest:710起）；MY008-3-01为MY008211A-PNH-3-01，不能与3-02混同。不得用演示MG-K10-SAR-III作为真实研究ID。
