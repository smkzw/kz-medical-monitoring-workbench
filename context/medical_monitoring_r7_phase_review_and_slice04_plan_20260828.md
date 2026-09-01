# R7 阶段复盘与 Slice-04 计划

日期：2026-08-28  
阶段状态：R7 进行中，Slice-01 至 Slice-04 已受限接受，R7 未完成

2026-08-28 更新：Slice-04 已按
`context/medical_monitoring_r7_slice_04_durable_progress_acceptance_record_20260828.md`
完成有限验收。当前下一片段为 Slice-05“后台执行与可恢复状态机”合同冻结；以下 Slice-04
章节保留为已执行计划与阶段审计记录。

## 1. 已落地能力

- Slice-01：ExecutionProfile 四层持久化，以及 Monitoring Run 对已冻结 harness profile
  身份的不可变绑定。
- Slice-02：隔离 API/运行入口，覆盖显式项目引导、配置读取、默认 MTPLX medium、显式
  DeepSeek V4 Flash max、三模式身份和全量/增量 Run 重放冲突。
- Slice-03：把上述能力以最小方式挂载到产品 `main.py`，建立 canonical 项目工作区、每请求
  连接生命周期和 R7 局部中文错误边界。

这些成果是必要的产品接缝，但对用户仍基本不可见：目前还不能在后台真正推进一轮监查，不能
精确显示各细节节点进度，也不能在中断后恢复。因此不得把“路由已挂载”描述为系统可用。

## 2. 当前主要缺口

1. Run 尚未绑定版本化 execution manifest 和权威 work-unit ledger。
2. 没有只从权威账本重建的中文进度投影，刷新或重启后的显示尚无事实来源。
3. 后台执行、checkpoint、失败注入、继续/重试/取消尚未接入产品。
4. harness preflight 与真实 MTPLX/DeepSeek 调用尚未进入产品 Run 生命周期。
5. 用户还看不到 ExecutionProfile、运行进度、工作播报、恢复入口和本地通知。
6. 三模式 common core/carry-forward、备份迁移、审计验证、性能与安装边界仍待完成。
7. 新增的项目/中心“受试者阶段流向”看板与表格尚未进入 UI；需求见
   `context/medical_monitoring_subject_flow_dashboard_requirement_20260828.md`。

Slice-04 已关闭第 1、2 项：Run 已绑定版本化 manifest/work-unit ledger，中文进度可从
SQLite 权威事实重建。第 3 项成为 Slice-05 的主阻断，第 4 至第 7 项仍按原顺序保留。

## 3. 后续纵切顺序

1. **Slice-04：持久化 Run 进度事实面。** 只做 synthetic/offline 的 manifest、work-unit
   ledger、产品中文只读投影和显式准备；不启动后台线程或真实模型。
2. **Slice-05：后台执行与可恢复状态机。** 接入 checkpoint、重建、幂等回调、失败/中断
   注入及继续/重试/取消的真实状态语义。
3. **Slice-06：Harness 运行纵切。** 在 synthetic 输入上接入 preflight 和实际 adapter
   调用，分别证明默认 MTPLX medium 与显式 DeepSeek V4 Flash max，不允许自动替换身份。
4. **Slice-07：面向用户的产品界面。** ExecutionProfile、启动监查、真实进度条、结构化中文
   工作播报、后台离页与恢复入口；用 ego(lite) 做真实浏览器验收。
5. **Slice-08：三模式与增量延续。** 闭合日常、锁库前、核查前三种模式，验证基线、数据修订
   全量 listing 的增量语义、医学决定版本和 carry-forward，并接入本地通知。
6. **Slice-09：本地产品韧性。** 备份、恢复、迁移、升级、回滚、审计链、日志轮转、性能、
   存储和长任务基准。
7. **产品视觉补强。** 在相关 UI 纵切中加入项目/中心受试者阶段流向看板与表格；它与受试者
   Journey 的时间轴是不同层级，二者通过受试者深链和相同截止点联动。

## 4. Slice-04 的用户价值与停止线

用户价值不是“多一个接口”，而是后续真实进度条可依赖的可信底座：刷新页面后数字不跳变，
完成数和总数对应具体工作明细，运行范围改变时明确产生新版本，用户只看到易懂中文。

Slice-04 完成时仍不得声称后台监查已可用；只接受显式准备和只读进度事实面。任何后台线程、
真实模型、真实项目、服务启动、前端修改、医学写作修改或安全功能扩展均越界。
