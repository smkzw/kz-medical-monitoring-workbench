# R1 后台运行与中文进度界面切片证据

日期：2026-08-10  
结论：**本隔离 synthetic R1 子切片通过；不代表 R1 总体验收或产品可用。**

## 1. 本切片证明了什么

- `BackgroundProgressFacade` 在应用进程内独立于浏览器页面运行；关闭轮询、离开页面、刷新或重新构造 facade 后，界面均从同一 SQLite 权威状态恢复。
- 受众数字只由 `project_audience_progress(store, run_id)` 投影生成。facade 和前端均不保存第二套 `completed / total / percent` 状态。
- `/progress` 仅返回受众白名单字段，且使用 `Cache-Control: no-store`；页面不展示 provider、model、attempt、backend、manifest、hash、log 等内部身份。
- 页面以中文显示总进度、六阶段进度、当前工作、最新动态及“可离开此页面”的后台运行提示；失败和受阻不会伪装成完成。
- HTTP 仅绑定自动分配的 `127.0.0.1:0` 临时端口。测试与验收结束后端口均已关闭，8911 始终未启动。

## 2. 执行与恢复语义

正常路径中，进程内按数据库、运行、manifest revision 和工作项建立互斥；三个并发 facade 的 8 个工作项实际回调总数为 8，每项一次，审计同为 8 个开始与 8 个终态。

故障路径不夸大为 exactly-once：若真实动作已返回、但其后的 SQLite 终态写入失败，恢复后该工作项可能再次调用。facade 会：

1. 记录后台 worker 错误而不静默死亡；
2. 自动继续 sweep；
3. 把稳定键 `background-progress:{revision}:{work_unit_id}` 传给动作回调；
4. 要求实际副作用使用该键实现幂等。

故障注入测试让一次终态写入失败，最终仍自动达到 8/8；首项被调用两次但两次收到同一幂等键，权威审计仍只有 8 个终态。这证明的是**至少一次调用＋稳定幂等键**，不是跨进程或故障窗口下的无条件只执行一次。

## 3. 用户界面合同

- 主标题、阶段名称和状态均采用医学监查人员可直接理解的中文；删除了“权威进度”“隔离演示”等工程视角表达，改为“最新进度”和自然说明。
- 主进度条和阶段进度条直接使用当前投影比率，取消会让颜色条短暂落后数字的动画。
- 受阻使用琥珀色，失败使用红棕色；二者在结构和颜色上可区分。
- 1440×900 和 900×700 两个视口均无横向溢出或隐藏文本；总进度与六阶段数字/条形比例一致。
- Chromium 控制台为 0 error、0 warning；离开、返回和刷新后均恢复为 SQLite 的 8/8 终态。

## 4. 决定性验证

| 检查 | 当前结果 |
|---|---|
| 聚焦后台进度测试 | `12 passed` |
| R1 核心测试 | `285 passed in 7.93s` |
| AE/MH 相邻界面测试 | `18 passed in 28.73s` |
| Patient Journey 相邻界面测试 | `16 passed in 21.47s` |
| Ruff correctness gate | `--select E9,F63,F7,F82` 全部通过 |
| 隔离 compileall | 通过；项目树未产生 `__pycache__` |
| 真实 Chromium | 两视口、离页/返回/刷新、进度比率、console 与溢出均通过 |
| 服务边界 | 临时服务关闭；8911 无监听 |

补充说明：一次未配置规则集的最新版 Ruff 全规则运行报告 38 个导入排序、现代类型注解和格式类建议；它不是本仓库已声明的门禁，也不涉及运行正确性。为保持独立审阅所冻结的源文件不漂移，本切片未在验收后做无关格式改写。

## 5. 独立审阅闭环

- Kimi/K3-256K 首轮给出 `VETO`：发现动作完成后 SQLite 终态写入失败会导致 worker 静默退出，并可在重建时重复真实动作。
- 主会场增加 worker 级异常捕获和续跑、稳定幂等键、故障注入回归，并把合同改正为故障窗口内 at-least-once；同时修复进度条滞后和失败/受阻颜色过近。
- 同一 reviewer session 第二轮复核冻结哈希和 12 项聚焦测试后给出 `ACCEPT`。

## 6. 冻结工件

| 工件 | SHA-256 |
|---|---|
| `src/mm_r1/background_progress.py` | `fe1be09bbef31d21251757f72704c20d7ba04b18ad5da2c50dc5476efa886132` |
| `slices/background_progress_shell/server.py` | `e7e562d3570c2d6851705821c4bad3019179e3d594522163c96cc7eb16a0438b` |
| `index.html` | `ae4ad511de53a25ee3bc8cc1bac3c7c4729104abb41d27660e6d67e15df61492` |
| `styles.css` | `2718e165478ec51806827d62bc07f662bd3ffdfeead4d866b0de3d76501794c9` |
| `app.js` | `14debe5439b72fbcaa005ed152beb2c2d1b23dad9c2f903c5df0651007bad76b` |
| `tests/test_background_progress.py` | `b2c8caa383b7ddec24bee7852b761498060101ea6b9d2fa3117b851ef4dafeb9` |
| `docs/DATA_CONTRACT.md` | `92fb2ad12da03ecb59512a825ea865195e74d2a765518ab380faa0561fdc5967` |
| `evidence/final_state.png` | `b1c7e6d47da8ba742b0618729b4182a3450d2dfbc16faf0c5f4434e6d092d0db` |
| `output/playwright/.../desktop_1440x900.png` | `e3b4ff54956f7735d4a85293009c19f99dbcd0393f6eca8b611cf00c8bf0c431` |
| `output/playwright/.../narrow_900x700.png` | `e0722c9a16044122ef9fdd28b9a9683b38a5d80fe0b0f242f3a1759ff499f3d8` |

## 7. 仍未证明

- 未证明应用整体退出、设备重启或多进程/多设备条件下后台工作继续。
- 持续性 Store 故障目前会无限重试并积累内存错误记录；产品宿主需要重试上限、退避和受众可见的降级状态。
- 进程级 `_UNIT_LOCKS` 尚无淘汰；后续长期宿主需要生命周期管理。
- `audience_snapshot` 目前借用 Store 私有连接开启一致性读事务；后续应提供公开的 read-snapshot helper。
- 未运行真实 harness、provider、研究资料或临床判断，不得据此宣称 R1 总体或产品完成。
