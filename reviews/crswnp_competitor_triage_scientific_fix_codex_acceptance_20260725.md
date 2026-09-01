# CRSwNP竞品分诊科学性修复 Codex验收

## 结论

接受源码分支，进入统一重启后的真实新快照与独立AI复验。该结论仅覆盖确定性科学边界和回归，不代表旧快照、旧分诊结果或真实DeepSeek结果已被接受。

## 验收边界

- 中文“慢性鼻窦炎伴鼻息肉”、CRSwNP及受控英文同义词视为同一适应症。
- `Chronic Sinusitis/Chronic Rhinosinusitis + Nasal Polyps`可由登记条件组合成立。
- 泛化的`Sinusitis + Nasal Polyps`必须由正式标题或简短标题中的完整CRSwNP表述佐证。
- 急性鼻窦炎、孤立鼻息肉、无鼻息肉慢性鼻窦炎、哮喘合并鼻息肉等反例不得误匹配。
- 项目技术类型、给药途径或靶点未知时，阻断直接竞品判定并降低置信度，但不能替代医学排除。
- 同适应症药理性研究或具有可用公开Protocol/SAP的研究至少保留为间接参考候选。

## 主会场验证

- 聚焦及科学边界回归：`236 passed`
- D017、持久化和恢复相邻回归：`86 passed`
- 提示词版本：`competitor_triage_deepseek_v10_crswnp_chronicity`
- 保存的12项CRSwNP候选重放仍可全部进入受控匹配。

## 未完成门

- 旧快照字段稀疏，不得复用。
- 统一重启后须生成新的富化ClinicalTrials.gov快照。
- 必须由产品配置的独立`deepseek-v4-pro`重新分诊，并由Codex逐条做医学终审。
- CRSwNP项目中误混入的UC量表事实及无意义靶点值必须走正式版本化链路清理。
