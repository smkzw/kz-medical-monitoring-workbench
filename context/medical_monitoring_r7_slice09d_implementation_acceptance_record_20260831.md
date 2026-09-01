# R7 Slice-09D 实现接受记录

日期：2026-08-31  
状态：`ACCEPT_R7_SLICE_09D_SYNTHETIC_OFFLINE_CAPACITY_RECOVERY`

## 接受对象

按冻结合同 v0.2（SHA-256 `9026dae92ccb574841f783af3842da6be28f20a5a7d991857a1045808e4ba34f`）接受 Slice-09D synthetic/offline 性能、容量、确定性、长任务恢复与证据闭包。§3、§4 与既有 §5 均关闭；独立会商最终结论为 `ACCEPT_09D_CHECKPOINT_P0_P4_ZERO`。

## §3/§4 决定性证据

- 权威 full-run：`artifacts/mm_r7_slice09d_implementation_20260831/measurement_full_30cell_accepted_09a_09c_20260831_v4/`。
- 15 profiles × 2 modes = 30 cells；七个 workload；2450 条 raw：1470 screening、140 calibration、840 confirmation。
- C02 与 C05 依冻结策略完成 3 seeds × 10 repeats；三个 seed 为 20260831–20260833。
- 2450/2450 `observed_green`；correctness/identity/accepted-seam invocation/resource/terminal state 全部通过；无 `dependency_not_measured`、`child_output_incomplete`、yellow、red 或 inconclusive。
- 确定性 225/225：15 profiles × 5 hash seeds × `normal/-O/-OO`。
- raw SHA-256：`6ca8e9def7bf48090bfa34d7be052d972b4260df7e93fd14c1639852a934a7a3`。
- measurement manifest 文件 SHA-256：`8eaf5de1fcf81ae5de3a6c139929f077ac49eae307294e93ea4d0bea4492e62b`；其 6675 个声明文件的字节数与 SHA 全部复核匹配，自哈希匹配。

## 允许记录的窄容量表述

在本次记录的 macOS arm64 工作站、Python 3.9.6、SQLite 3.51.0、137 GiB 物理内存、measurement-time source-copy `2b771fb1…`（70/70、运行前后不变）及冻结 corpus manifest `043767ba…` 下，30 cells、七个 workloads、2450 trials 全部 `observed_green`。balanced 梯度 C01–C05 全绿，最后一个全绿 balanced profile 为 C05（T4，100,000 events）；未观察到非绿 balanced profile，也无未测相邻 profile。peak RSS 为 78,413,824..1,325,580,288 bytes，可用磁盘为 668,436,041,728..689,954,598,912 bytes，watchdog 为 300 秒 floor。

该表述只描述当前工作站、源码副本和冻结 corpus 的观测结果，不构成产品容量、系统支持范围、通用 SLO、医学质量、生产或商业化声明；`accepted_09a_09c_product_capacity=false` 继续作为范围护栏。

## 报告纠偏与身份分离

- full-run 最初误用 `adapter_readiness_bounded_only` 与 `bounded proof only`；独立会商定级为两个 P3 报告误标，raw evidence 不受影响。
- runner 已按 bounded/full 分流：full accepted run 使用 `contract_observation_complete_no_capacity_claim`；capacity statement 明确“记录环境内观察到 accepted seams，非一般容量/支持声明”。
- 报告只重建 `stat_summary.json`、`capacity_statement.md`、`measurement_manifest.json`，raw SHA 保持不变。
- measurement-time identity 以 `source_copy_identity_measurement_v4.json` 原样归档，文件 SHA-256 `8719fb1c6f9cafb741f30413f6b88d5d78c1dfcb9568051c53e1ce66f0e51815`，内部 source-copy SHA `2b771fb1…`。
- 当前报告/清单源码另以 70/70 verified source-copy `f8f14213a6fb88cbd706d9b1771eed1869e2271f49f455c51c5154c3dfbe8406` 记录，不冒充 measurement-time 源码。

## §5 与总证据入口

- §5 延续既有接受：18 个语义场景 + 82 个源码枚举 hooks，共 100/100 observed pass；mutation guard 23/23 killed。
- `consolidated_total_manifest_v0_2.json` 已将早期 bounded evidence 明确标为 `measurement_bounded_historical`，并以 `measurement_full_v4` 精确索引七个 v4 顶层证据文件；总计 7 sections、50 pinned files、0 missing，inventory SHA `26a8a20aa34f35958029a4dbe56245ae0a300924a4f7412cf5df69c6c3d65d0c`。
- 总清单文件 SHA-256：`89220a945f4053531f87aeb9f0a18fe4728f1b7051f2fe5f95928e6a1e7bc38e`。

## 最终门禁

- Slice-09D artifact suite：`56 passed`。
- 相邻 R1 + R7：`853 passed, 19 warnings`（R1 327 + R7 526）。
- 独立会商同一 session 完成 full-run、报告纠偏、总清单闭包三轮复核；最终 P0=P1=P2=P3=P4=0，无 fallback。
- 8911、5174、8984 均无监听；无 measurement 进程残留。
- 未运行真实项目、真实方案/IB/listing、真实模型、浏览器或 UI；未修改医学写作子系统。

## 排除证据

- v1：workspace collision，已失效。
- v2：confirmation seed/fixture mismatch，已失效。
- v3：在 determinism finalization 前中断，只作恢复证据。
- 只有 v4 可用于 §3/§4 接受。

## 范围边界与下一动作

本记录只接受 Slice-09D synthetic/offline 检查点，不等于 Slice-09/R7/R8 总体、真实来源、真实医学质量、视觉 E2E、生产或商业化接受。下一动作先完成 Slice-09 与 R7 大阶段总体复盘、共享回归/证据入口核对，并冻结 R8 source-admission 与反过拟合验收合同；在该合同接受前不得读取五个真实项目或调用真实模型/浏览器。
