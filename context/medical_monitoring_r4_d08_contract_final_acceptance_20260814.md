# R4-D08 合同与冻结制品最终接受记录

日期：2026-08-14  
状态：`ACCEPT_D08_CONTRACT`

## 接受对象

- 合同 v0.6：`reviews/medical_monitoring_r4_d08_cross_domain_logic_slice_contract_v0_6_20260814.md`，SHA-256 `ff3d3a1bd9844ac8808ca7f9ada1466317763eb883e60d825f15bb3015ac4d64`。
- catalog：SHA-256 `d3cd694bcbe63d977d5ef332be3647fb1274293be6ec364021946ee610ffa82c`，233 cases。
- oracle：SHA-256 `a40cbb509df2378804fd513a79467cbbc4e208d3b2b5c6f1a2410a63a12b8ac9`，content hash `724b95cb0964a4bdb992ba08655a4aff30983cb8d7454038fdbe269588f0b3d1`。
- registry：SHA-256 `bf0142b36a60524d40d203e641c6fc0ef591c01069dd63caf6fc92da3ec96a9a`，content hash `55f1efbd7bfdb2ae7ea1e461b02eb732b792bba0140208ce4bfe3e6b4661ca9a`。
- generator：SHA-256 `63d610e82c385cbe906ecf8978622b9d534a64ef22b74a275832a0e07e8df100`。
- focused tests：SHA-256 `0b4e7c1db038a7b555e204f6a26ebf7216949c38f1daf08155b6673a60c5f906`。

## 决定性证据

- Codex 复现：D08 generator 双遍字节一致、14/14 负向变异 fail-closed；focused pytest `54 passed`；Ruff、compile 通过。
- 完整独立审计：233 个 case 的 expected/trace/source 共 16,881 个叶均由 typed input 与合同逻辑重建并精确相等；逐叶单点变异 16,881 次，逃逸 0。
- 相邻回归：D07 权威 generator check 通过；R1/R2/R3/R4 分别 `327/598/339/3657 passed`。
- 独立 Luna 同会话终审：`runs/review/medical_monitoring_r4_d08_contract_freeze_luna_followup2_20260814.md`，SHA-256 `c1fb0eb53ac3656dc044fb98db75402968ef56db9c4a85a5f7bfc65c6ace0811`，结论 `ACCEPT_D08_CONTRACT`。
- 8911 无监听；未运行服务、真实项目或患者数据，未触碰医学写作子系统。

## 纠偏轨迹

Luna 首轮和 follow-up1 两次返回 `REVISE_D08_CONTRACT`，分别发现负向用例假阳性及 oracle 叶审计不完整。修复后不是按字段补洞，而是建立完整逐叶独立重建与变异敏感性门。历史 REVISE 报告保留为证据，不得被最终 ACCEPT 覆盖或改写。

## 下一安全动作

只解锁 D08 synthetic/offline runtime 实施合同与定向测试；D09/D10、R5 UI、服务、8911、真实项目和产品集成仍未获接受。先定义 runtime 的 typed input/output、owner-routing、cutoff/temporal/identity/propagation/visibility 与 Query/Journey 投影边界，再按冻结 oracle 做实现和独立验证。
