# 医学监查 P10：字段映射语义质量用户态

## 目标与边界

本切片只调整医学监查字段映射面板的前端展示与确定性状态模型，不修改后端、
`main.py`、医学写作或方案准备。正式合同包括：

- `blocked + reject`：存在全局阻断，不能确认；
- `pass_with_warnings + activate_restricted`：允许用户确认，但部分分析能力受限；
- `pass_with_warnings + activate_full`：可完整启用，仍有非阻断建议；
- `passed + activate_full`：全部已登记能力可用。

用户确认即批准，不增加“待医学批准”状态。字段列表仍默认只显示待关注字段。

## 实现

- 新增 `medicalMonitoringFieldMappingState.mjs`，将后端质量报告转换为稳定的用户态；
- `activate_restricted` 明确显示“可启用，但以下分析将受限”，优先列出最多 3 项受影响
  能力，例如受试者时间线、实验室异常与 CTCAE 分级、量表复算；
- 若能力标识尚无前端中文名称，则降级显示最多 3 个医学问题主题，不暴露内部 ID；
- `blocked/reject` 明确显示全局阻断并禁用确认；
- restricted、`activate_full` 警告态均保持确认可用；
- 只有 `passed + activate_full` 显示“字段语义校验完全通过”；
- 样式仅增加 blocked、restricted、warning 的最小区分，不增加日志、内部标识或常驻说明。

## 验证

- 确定性状态模型：`6 passed`；
- 医学监查前端 API 合同：`94 passed`；
- Vite 生产构建：通过，1,906 个模块完成转换；
- 只读运行态检查：RUX V13 当前为 60 completed、2 running、113 queued，尚无 draft，
  因而没有可用于真实 restricted 页面验收的状态。本轮未伪造浏览器证据；待正式 draft
  组装后，应分别复核 blocker、restricted 与 full 的真实页面、按钮状态和能力摘要。

## 文件

- `frontend/src/features/medical-monitoring/MedicalMonitoringFieldMappingPanel.jsx`
- `frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingState.mjs`
- `frontend/src/features/medical-monitoring/medicalMonitoringFieldMappingState.test.mjs`
- `frontend/src/styles.css`

