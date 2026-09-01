# Delegated mode — Conference follow-up

## Role

继续同一 `general_single_object` session，只读复核 R7 Slice-08C-3 合同修订版；不得重新开始任务或沿用旧文件内容。

## Hard boundaries

- 当前文件系统是真相。必须重新读取下列文件，不得从上一轮缓存判断它们仍为 TODO 或仍未修订。
- 只读；不得修改文件，不得启动服务、浏览器、模型或真实项目。
- 只评审合同与会商包是否已关闭上一轮 P0/P1/P2；不得声称实现或视觉验收完成。

Initial read set:

- `context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md`
- `context/mm_r7_slice08c3_contract_20260829_conference_context.md`
- `plans/codex_main_venue_mm_r7_slice08c3_contract_20260829.md`
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_1_20260829.md`
- `reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md`
- `frontend/src/features/medical-monitoring/r5/MedicalMonitoringR5Page.jsx`
- `frontend/src/features/medical-monitoring/r5/medicalMonitoringR5Timeline.mjs`
- `frontend/src/features/medical-monitoring/r7/MedicalMonitoringR7ProductLoop.jsx`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ContinuityFilter.mjs`
- `frontend/src/features/medical-monitoring/r7/medicalMonitoringR7ContinuityProjection.mjs`

## Required verification

逐项复核上一轮提出的：包内 Source Of Truth/Scope/Success Criteria、当前 packet 产物性质、轴窗来源与闭区间谓词、R7/legacy inspector 边界、未绑定变化呈现、truncation、Query 来源、多变化模型、Esc、阈值、push/overlay、固定缺值文案、七类 Lucide、aria-live/aria-labelledby 与测试门。

注意：`reviews/metrics/runs` 中同 task id 文件是本次 guard 初始化与前两轮 runner 的当前声明产物，不是会商前历史污染。不要再次把当前 runner 自己的输出文件存在视为 P0。

Runner-managed output file: `runs/conference/mm_r7_slice08c3_contract_20260829/general_single_object.md`

不得用工具写该路径；返回完整内容，由 runner 持久化。

返回完整 Markdown：首行明确 `ACCEPT` 或 `REVISE`。只有仍存在可定位的 P0/P1/P2 才 REVISE；若均关闭则 ACCEPT，并列出可定位证据和实现前提。
