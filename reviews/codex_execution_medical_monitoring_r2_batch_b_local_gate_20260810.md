# R2 Batch B Codex 本地硬门

日期：2026-08-10

状态：`LOCAL_GATE_PASS / PENDING_INDEPENDENT_REVIEW`

范围仅限 `poc/medical_monitoring_ai_native_r2/` 的 synthetic/offline Batch B：风险候选与风险生命周期、裁决证据绑定、数据基线与医学判断版本、三种监查运行模式、全量/增量差异。它不接受 Batch C、真实模型或端点、真实项目、产品接线或生产隔离。

## 本轮封口

- 权威对象签发器只存在于封装闭包；模块、类和服务实例均不暴露构造入口。
- AcceptanceService、BaselineService、ListingSnapshot、DataBaseline、RiskCandidate、RiskInstance、AdjudicationRecord 与裁决证据在权威边界使用精确类型，拒绝 duck type 与恶意子类覆盖。
- 医学判断版本引用的数据基线必须由同一 BaselineService 已签发且属于同一项目。
- 增量差异必须使用同一 BaselineService 已登记的数据基线，并重新核对当前 AcceptanceService 中未阻断、仍为 baseline eligible 的完整绑定。
- 锁库后至 CFDI 核查前仅允许全量运行，后续运行必须复用同一锁定快照且不能退回其他模式。
- 风险候选只能建立一次；候选证据逐项绑定 snapshot/rule/mapping/knowledge；裁决在使用时核对 action、outcome、生命周期与完整目标集合。
- 拆分裁决绑定完整 child specs；合并/拆分先构造全部结果后一次提交，失败不改变风险实例或项目链头。
- 项目风险链按 `prev_hash` 拓扑校验并核对当前链头，不依赖时间戳排序。

## 决定性证据

- Batch B：`172 passed in 0.16s`。
- R2 全量：`408 passed in 0.29s`。
- 独立攻击脚本：9/9 路径均被阻断，`attack_gate=PASS`；覆盖模块签发器、恶意 AcceptanceService 子类、阻断后的 live baseline、重复候选建立、任意用户确认、拆分 payload 替换及失败原子性。
- 内存语法编译：`in_memory_compile_ok=21`。
- R2 cache directory：0。
- TCP 8911 listener：无。

## 冻结快照

树摘要算法：对 `poc/medical_monitoring_ai_native_r2/` 内除 `__pycache__`、`.pytest_cache` 外的文件按相对路径排序，形成 `sha256(file-bytes) + two spaces + relative-path + newline` 清单，再对清单做 SHA-256。

- files：22
- tree digest：`0eac705392adf7235d3efe3f48c7a99e769c4c9fa6e52c6e1d9f36816dc3108d`
- `src/mm_r2/baselines.py`：`6a489e7e40004382c5684e7e005e6715e263da25611500cfd2e4f7d3f7b089fd`
- `src/mm_r2/modes.py`：`0f53854d94f6c77d2d4ac9a21ea5e79b21145b513b11a10d732cb54b25b6bdf5`
- `src/mm_r2/diff.py`：`7a652d789f2c5b75fab68ab7abf6ecf4475a77fde6febd892fbaa6839cf2d658`
- `src/mm_r2/risk.py`：`65b9a8573cc46998098b98d1d09dfc51d9ceb67d90617a8fa747e147a308772a`
- `tests/test_r2_b_baselines.py`：`c0b1047e143f432f0f388508a2aba5f47bcdeef87553b959ebb7dda3a6ca2354`
- `tests/test_r2_b_modes.py`：`c35cafd064c0f7a24e1ca6d011fe54feff13d0b5428c8db1f4754696f0145d51`
- `tests/test_r2_b_diff.py`：`cd577fd226cbab111a20141d3cdfa10269764010a4ac187345dd3ac7ba234b1c`
- `tests/test_r2_b_risk.py`：`42708005564a10b848641e3a6a485578f10e42050a61fe42f32b1a154c8921cc`

## 独立验收要求

独立验收者须从冻结快照重新读取源码与测试、首尾复核 SHA、运行 Batch B 与 R2 全量测试，并自行设计负向攻击。任何可从普通调用面伪造权威对象、跨项目/跨服务替换基线、绕过锁库后固定总量、用不匹配证据改变风险、或在合并/拆分失败后留下部分状态的路径均为 VETO。Batch C 在独立 ACCEPT 前保持冻结。

