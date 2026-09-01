# 医学监查 R8 G2 synthetic runtime 接受记录

日期：2026-08-31  
状态：`ACCEPT_R8_G2_SYNTHETIC_RUNTIME`  
范围：`RUNTIME_LAUNCH_READY_SYNTHETIC`；不等于真实项目、真实模型、浏览器、医学质量、产品或生产接受

## 接受对象

- 共享 canonical evidence：`deploy/medical_monitoring_local/canonical_evidence.py`
- source/output manifest 与 revision replay：`deploy/medical_monitoring_local/synthetic_manifest.py`
- 目标 macOS synthetic source-access profile：`deploy/medical_monitoring_local/source_access_profile.py`
- synthetic/offline lifecycle：`deploy/medical_monitoring_local/synthetic_lifecycle.py`
- 一键管理入口与中文说明：`deploy/medical_monitoring_local/manage.py`、`deploy/medical_monitoring_local/README.md`
- 发布清单：`deploy/medical_monitoring_local/release_sources.json`

最终文件 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `canonical_evidence.py` | `84a0a7e4ba66e52b5ce9d16c5dcedef48376f0308a1392819d93f33e41cfa44e` |
| `synthetic_manifest.py` | `c7928ac0625e7acedc609321f8e33c25cd06423b989aeb8a17f655862aaae001` |
| `source_access_profile.py` | `c15a417a6731c025ade0f91453a091de8fb522af9de0e2101f796a92b6e9a19e` |
| `synthetic_lifecycle.py` | `60a2646b346562d7bc17476f2e74332a328fa1c72d758cd2372f3e907a92583e` |
| `manage.py` | `b36dc6eddc749fbd5008de2e3c08f75a1de870c39ca1890fec8d6a5c323bcc0a` |
| `README.md` | `278f95a1bc596b67b60a173fb979668df7a817df8b61ae477d9cdff443307c3a` |
| `release_sources.json` | `80970fa97376a563b43607215436a1ac0bacb28bb07031545c0391610a246440` |

发布清单为 16 个文件，manifest SHA-256：
`ea0a53f9f959412f97b89d1190576e71765e21e555e356d648a3c0ca3b5b3ded`。

## 执行与纠偏

1. Governed execution `mm_r8_gate2_synthetic_runtime_20260831`
   - 三个 worker 分别实现 manifest/replay、source-access profile 和 lifecycle/一键入口；
   - 均使用 `Pi/openai-codex/gpt-5.6-luna:max`，终态成功，无 fallback；
   - execution audit `ok=true`。
2. Independent conference `mm_r8_gate2_synthetic_runtime_review_20260831`
   - `Pi/cms-router/minimax-m3:xhigh`；
   - 同一 session `01a0560b-f3eb-7000-b42f-a374498556c5` 两轮，无 fallback；
   - Round 1 返回 `REVISE`，指出 canonical 漂移、manifest 证据未绑定、lifecycle 自证回放及 target-macOS 证据不足；
   - Codex 完成最小纠偏；Round 2 直接审阅当前源码并返回 `ACCEPT_R8_G2_SYNTHETIC_RUNTIME`；
   - conference review gate `ok=true`。

## 关闭的阻断

- 三模块统一导入同一 canonical JSON 实现，NFC、非有限浮点、规范化键冲突及 `-0.0` 规则一致。
- source manifest 的 `zero_write` 必须嵌入并重放有效 source-access evidence，绑定 profile/before-tree/after-tree digest 与 reasons；缺证据时 fail-closed。
- output manifest 必须包含并摘要绑定 `source_access_profile_digest`。
- lifecycle replay 使用独立静态 scenario expectation，不再调用同一 builder 自证；重签名篡改仍被拒绝。
- 默认 source-access drill 在真实临时 macOS filesystem 上创建锁定 shadow root，并执行实际被拒绝的写 syscall；memory fixture 只能得到 `not_evaluable`。
- synthetic 一键入口不解析分发根，也不读取 root/runtime 环境变量；不启动服务、模型或端口。

## 决定性验证

- 四个 G2 模块 `py_compile`：通过。
- 聚焦加发布分发相邻回归：`91 passed in 2.53s`。
- lifecycle 直接演练：`start-stop-restart → ready`，独立 replay 有效。
- source-access 直接演练：`evaluable`、`macos_filesystem`、source tree unchanged、独立 replay 有效。
- G2 产品模块真实项目/药物/疾病专有字面量扫描：无命中。
- 8911/5174/8984：均 `connect_ex=61`，保持停止。

## 明确未接受

- 未访问、列举、哈希或打开五个真实项目根；
- 未调用任何真实 VLM/LLM 或内置 harness；
- 未启动产品服务、产品浏览器、8911/5174/8984；
- 未验证真实通知、真实备份/迁移/恢复/回滚/卸载或 §15.4；
- 未验证真实项目医学质量、泛化、Patient Journey、中心/试验看板或视觉；
- 未修改医学写作子系统；
- 未接受 R8 总体、产品、生产、商业化或监管声明。

## 非阻断加固项

- 后续收紧 `contract_ref` 固定形状；
- 在进入更广运行环境前，让 macOS 临时目录原始 `OSError` 显式降级为 `not_evaluable`；
- G6 前明确 synthetic write-event monitor 与真实系统观察器的证据边界；
- 澄清 distribution release digest 与 contract-grade canonical digest 的命名边界。

## 下一安全动作

进入 G3 通知路径决定与合同冻结。G3 只定义 app-visible/background
notification 的目标系统能力、终态、失败关闭和用户语言；不得跳到 G4-G6，
不得启动浏览器、服务或真实模型，不得访问真实项目。G4 synthetic §15.4、G5
预真实联合门和 G6 synthetic ego(lite) 仍按顺序执行；G7/G8 真实来源与模型门继续关闭。
