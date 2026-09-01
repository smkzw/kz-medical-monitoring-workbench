# R5-S5 统一时间投影权威增补接受记录

- 日期：2026-08-20
- 接受标记：`ACCEPT_R5_S5_TEMPORAL_PROJECTION_AUTHORITY_DELTA_V0_1`
- 唯一对象：`artifacts/medical_monitoring_r5_s5_temporal_projection_authority_delta_v0_1/manifest.json`
- manifest raw SHA-256：`e606e517c07dcb499657b418dbd16e4dacd98c7e7010770845dbccb91af59f97`

## 接受范围

仅接受 append-only、synthetic/offline、non-clinical 的统一时间投影权威机制，用于为后续 implementation-contract v0.3 提供：

- 截止日、时间轴、日期端点与 study-day 权威；
- 访视/事件/阶段/风险精确绑定，受控阶段中文词典与待补成员 recipe；
- 可见性 node 到 stable member/site 的 typed bridge；
- locator-revision 完整消费；
- AE/MH append-decision、evidence 与 thread membership authority；
- 上述根权威到依赖 hash/container/projection/receipt/packet 的确定性 DAG。

## 决定性证据

- 272/272 叶 exact bijection，169 个 former-D 叶均有权威 emitter 或 executable recipe，nominal mapping=0。
- 119/119 权威映射按精确 op 执行，消费 trace 与声明的最小 dependency slice 一致；90+ 个不同切片，无全类依赖闭包。
- 6 种权威 op 分支独立，跨-op 互换、fixture 循环重分配、同类记录互换、成员增删/重排、自授权与 schema 漂移均 fail-closed。
- manifest 固定 accepted record、18 accepted recipes、authority-output registry 与 recipe-authority binding registry。
- normal/O/O2、多个 `PYTHONHASHSEED`、两次字节级生成、exact no-cache Ruff、accepted/rejected pins、542 医学写作保护聚合、producer/runtime absence 与 8911 stopped 通过。
- 独立 reviewer 对最终 SHA 返回接受标记。

## 未接受

本标记只解锁 implementation-contract v0.3 的生成与审阅，不接受或解锁：

- subject-temporal / AE-MH producer 及其 tests/evidence；
- R5-S5 runtime、UI、浏览器；
- 真实项目、真实模型、临床权威规则包；
- 产品、生产或医学写作子系统状态。

任何 manifest 字节变化都使本接受失效。
