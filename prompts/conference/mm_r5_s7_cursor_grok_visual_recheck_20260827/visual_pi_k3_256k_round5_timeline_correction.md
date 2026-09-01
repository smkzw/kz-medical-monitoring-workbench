同一会话补充复核。产品刚完成 Patient Journey 结构纠偏；之前关于卡片墙或旧截图的判断不得沿用。

角色仍为首次接触系统、视觉敏感且风险敏感的资深中文医学监察员。只读，不改文件，不读源码。请使用 Playwright 真实打开当前运行中的系统并复核以下两条深链，视口至少 1600x1000：

1. 普通受试者：
http://127.0.0.1:5174/monitoring?project_id=s7-synthetic-project-001&run_id=s7-run-current-001&snapshot_id=s7-snapshot-current-001&cutoff=2026-03-31&site_id=s7-site-010&subject_id=s7-subject-10008&risk_key=s7-risk-key-pd-10008&risk_instance_id=s7-risk-pd-10008&view=journey&spine_id=s7-spine-10008&axis_mode=calendar&start=2026-01-01&end=2026-03-31&risk_anchor_ref=s7-anchor-pd-10008&scope=subject

2. 高密度受试者：
http://127.0.0.1:5174/monitoring?project_id=s7-synthetic-project-001&run_id=s7-run-current-001&snapshot_id=s7-snapshot-density-001&cutoff=2026-12-31&site_id=s7-site-010&subject_id=s7-subject-density-001&risk_key=s7-risk-key-density-001&risk_instance_id=s7-risk-density-001&view=journey&spine_id=s7-spine-density-001&axis_mode=calendar&start=2026-01-01&end=2026-12-31&risk_anchor_ref=s7-anchor-density-001&scope=subject

必须实际滚动时间轴、点击至少一个点事件和一个区间事件、使用 + / 0 / - 缩放，并检查右侧事件详情是否对应所点事件。重点回答：

- 是否已经形成一条真正从左到右的共享访视/日期轴，而不是平铺卡片；
- 8 类事件是否位于同一时间坐标下的独立泳道；
- 点事件、区间事件、风险徽标是否能看出发生日期/持续时间及先后顺序；
- 日期缺失或冲突事件是否被放在时间轴外的“日期待确认记录”，且未虚构位置；
- 普通和 1000 事件密度下是否仍可定位中高风险；
- 是否残留内部 ID、后台术语或与所点事件不一致的详情。

请按 P0-P4 给出可复现发现。若无 P0-P4，明确写“本轮未发现 P0-P4”，但不要代表 Codex 做最终验收。只基于这次真实运行证据。
