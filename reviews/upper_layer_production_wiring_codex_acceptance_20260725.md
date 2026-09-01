# Upper-layer 生产接线 Codex 验收

## 结论

源码与离线回归通过，可进入统一稳定服务重启后的真实模型验收；当前不等同于真实生产
运行通过。

## 接受范围

- direct 与 batch 共用同一个 `ChapterTranslationPipeline`。
- 两条路径共用同一个持久化
  `WritingReferenceUpperLayerExecutionService`。
- 服务器固定：
  - Flash：`deepseek-v4-flash`
  - Pro：`deepseek-v4-pro`
  - provider：`deepseek`
  - transport：`openai_compatible`
- 每次供应商调用后校验实际响应模型身份。
- Flash/Pro只做文档规划及Hy-MT2译后整合/QC；Hy-MT2仍是正文翻译唯一模型。
- direct历史callable入口通过`ContextVar`绑定持久owner，不绕过持久层。
- transient失败为`failed_retryable`且不升级Pro；确定性Flash结构失败才允许一次Pro升级。
- HTTP 400/401/403/404、路由身份错误、响应模型错误均失败关闭，不误触发Pro。
- Pro复用同一不可变Hy-MT2 target-map；hash、序号、字符串类型或内容变化均失败关闭。
- 启动恢复仅覆盖queued及租约过期running escalation，不自动重跑
  `failed_retryable` Pro。
- direct/batch公开请求合同不暴露provider、model、transport、base URL或API key。

## Codex实际检查

- 逐段读取：
  - `services/api/app/writing_reference_upper_layer_adapters.py`
  - `services/api/app/main.py`组合根
  - `tests/test_writing_reference_upper_layer_production_wiring.py`
- `py_compile`通过。
- 项目既有Python解释器组合回归：
  `172 passed, 1 deselected, 15 warnings`。
- deselected历史测试仍把异步`accepted`错误断言为同步`completed`，不属于本切片。
- Homebrew Python 3.12首次复跑因该解释器缺少`pymupdf`在collection阶段失败；
  这不是产品失败，也不作为通过证据。最终通过结果来自项目已有、依赖完整的Python。

## 未通过的真实运行门

1. 稳定服务尚未加载当前源码。
2. 尚未真实调用`deepseek-v4-flash`或`deepseek-v4-pro`。
3. 尚未在真实direct和batch中核对持久lineage、响应模型、Hy-MT2调用次数与target-map。
4. 尚未做真实进程重启后的queued/lease-expired escalation恢复。
5. corpus selection仍为`not_implemented`，不得宣称语料准入已自动完成。

