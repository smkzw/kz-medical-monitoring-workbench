# R7 Slice-07C-2 “准备并开始”实现合同 v0.1

日期：2026-08-29  
状态：`FROZEN_R7_SLICE_07C2_PREPARE_START_V0_1`

本合同仅细化已冻结 Slice-07C v0.2 §11–15、§18–20，不改变业务设计。

## 1. 产品请求

`POST /runs/prepare-and-start` 只接受：

- `current_snapshot_token`
- `mode`
- `execution_basis`
- 可空 `baseline_token`
- 已确认的 `risk_rule_tokens[]`
- `idempotency_key`

客户端不得提交 run id、work-unit、source revision、profile、模型、provider 或内部图身份。

## 2. 服务端解析与冻结

服务端重新读取当前项目 options，逐项解析 snapshot、同模式已发布 baseline 和本项目已确认规则
token；任一 token 过期、跨项目或不再合格均失败关闭。日常增量必须有 baseline；日常全量不得
有 baseline；锁库前始终 full，可选已发布同模式 baseline；核查前始终 full 且不得有 baseline。

canonical diff、模式模板、规则版本共同生成一个 `WorkUnitManifest`。manifest 的 current、baseline、
规则 token、模板版本、分母和 digest 在创建时冻结。低层管理员 prepare 路由仍可接受显式 work-unit；
产品向导不得使用该入口。

## 3. 幂等与补偿

新增项目工作区内的 append-only launch registry，SQLite 使用 `busy_timeout`，并显式关闭连接。
`project + idempotency_key` 唯一；规范请求指纹覆盖 mode、basis、current、baseline、已排序规则 token。
同 key 同内容返回同一 public run；同 key 异内容返回 409。

首次请求先原子保留 public token、内部 run id 和规范请求，再依次完成 run binding、manifest prepare、
background start。每一步均使用既有幂等合同。start 未取得所有权或请求在已准备后中断时，不删除
运行、不另建运行，记录 `waiting_start` 并返回同一 public token；医学监察员重放只回到该运行，
不替代管理员继续/恢复。已成功启动的重放不得重复启动。

## 4. 公共历史

`GET /runs` 返回当前项目有界、按创建时间倒序的历史；只包含 public token、中文模式、数据截止、
比较范围、运行状态、结果是否可打开和主动作。不得返回内部 run id、snapshot/source/hash/profile、
provider/model/database/token 字段名。07C-2 结果始终不可打开；07C-3 发布成功后才可变为 true。

## 5. 长等待

产品启动只是把既有后台执行置为运行态，不同步等待模型文本。MTPLX 只要后台租约/心跳有效就
保持运行；浏览器请求超时不把运行标记失败。该规则沿用现有 background recovery，不新增短超时。

## 6. 本步验收

- 三模式首次创建、同请求重放、同 key 异请求 409。
- 日常全量/增量、锁库前多候选 baseline 显式选择、核查前固定范围。
- token 过期/跨项目/混合模式/未发布 baseline、跨项目规则均失败关闭。
- 规则 token 解析后 manifest 保留中文摘要与具体版本；分母稳定。
- prepare 后 start 失败保留同一 public run 和 `waiting_start`；历史可恢复读取。
- R7 全套、产品路由、医学写作聚合与保护端口通过。
- 只用 synthetic；不启动 8911/5174，不运行真实项目，不实现发布、result-entry 或前端。

