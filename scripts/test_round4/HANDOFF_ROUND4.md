# 医学监查子系统 阶段Handoff（测试轮4收尾 · 2026-09-22）

基线提交：74b90d4（全部已推送 GitHub: smkzw/kz-medical-monitoring-workbench main）
运行环境：API=8910（.venv uvicorn，env 见 mm-workbench-takeover-state 记忆），前端 vite=5177（**API改码后必须同步重启vite**，写作闸门按前后端指纹配对）。清洁空间=0活跃项目。

## 一、本阶段做了什么

### 1. 找到并修复了"作业假活"的全链条根因（本阶段最重要成果）
此前文档权威/分析作业大量卡在 running 永不完成。五层根因全部修复：
- **worker 从不被唤醒**：文档权威双 worker 是 wake-only 设计却无人调用 wake → 补齐唤醒链（7603521）
- **runtime 解析器导入不存在的模块**：`monitoring_product_ai_transport` 不存在，异常被线程静默吞掉 → 改从 monitoring_ai_service 导入（7603521）。此 bug 自 0198c82 起使独立模型架构从未真正运行
- **完成登记因上游模型别名回报而永久挂起**：路由器以别名回报 served 模型名（请求 deepseek-latest-cloud 实际报 deepseek-flash；请求 glm-5.3 实际报 glm-5.3-flash），完成校验强制相等 → 异常被吞 → 作业既不失败也不完成、心跳还在（假活）。修复=不主张身份断言的 profile 完成登记以 requested_model 为准（3cf5fa7）
- **job_id 是身份列的确定性 hash**：SQLite 迁移身份列必须同步重推导 job_id；claim_next 对身份损坏行改为隔离成终端失败，不再击穿 worker 线程（b943ea0）
- **部署档缺失**：runtime 补 WORKBENCH_AI_DEPLOYMENT_PROFILE=local_private_clinical，修复 ai_not_configured 误判（68e7dff）

### 2. 模型路由迁移（用户意图的可达实现）
opencode-go 与 ollama-cloud 的全部存储密钥实测 401 失效（zhipu 仓内密钥也过期）。唯一可用通道=本机 OmniRoute(127.0.0.1:20128)。文档权威切换为：主=omp-router/glm-5.3-flash（high），盲核=omp-router/deepseek-latest-cloud（不同模型族，保持盲核独立性）。密钥经 workbench 凭据仓解析（cms_router_dsf 条目=35字符 router key）。用户原始指定 muse-spark+deepseek-v4.1 的意图保留在注释中，密钥恢复后改 mapping_gate 常量即可回切（468f07b/3dcc0a2）。

### 3. 文档权威状态机首次全线贯通
eCRF 验证批次真实跑通全部裁决阶段：主/盲核独立分析 → 匿名冲突盲核 review 对 → 内部 adjudication 对 → critique 复核对，六路作业全部真实模型完成、回执校验通过。收尾停在 evidence_incomplete 属数据性缺口（该批次只传了 eCRF，protocol 角色无法裁决）。

### 4. 测试轮4三测试者完成并出报告（本轮发现大幅前移）
三测试者（grok/RUX锁库前、cursor-grok/CSU日常、glm/PSO-CFDI）端到端实测：**建项勾选→监查工作区→Listing接入→结构识别全通**（54表/18万行秒级识别，多项目一致正确）。新阻断点收敛到一处：**研究文档核对无法收敛**——"还差一项关键信息"问句渲染空选项列表无路可走。报告+会商决议+修复计划已入库：`scripts/test_round4/`（70d7cdf）。

### 5. F7 用户裁决功能（针对轮4 P0 的修复，已实现+单测通过）
- 后端：needs_user_input/evidence_incomplete 状态返回结构化 `user_choices`（每未决角色×候选文件+缺失选项）；resolve 请求接受 `user_role_selections` 人工裁决，人作为医学权威收敛模型分歧；用户裁决可越过模型阶段 role_hypotheses 假设；evidence_incomplete 在有未决角色时改判 needs_user_input 并给出可作答的指引（74b90d4 及后续）
- 前端：向导第3步渲染逐角色单选+提交按钮，替换空列表死胡同
- 附带：非 selected 角色误带证据定位符的确定性归一（glm 输出质量缺陷的合规修复，selected 角色锚定证据仍严格必需）

## 二、没做什么（诚实清单）

1. **F7 全链浏览器实测未走完**：API 直驱验证到"模型对协议角色的分歧仍会触发完整AI链"这一步；user_choices 渲染与裁决提交的前端交互待下轮测试者实测
2. **promoted→mapping→facts 物化的端到端**：前置已全通，但"监查模块就绪"完整闭环待真实完整文件集（方案+eCRF+Listing）实测
3. **F7f 来源台账接线**：Listing 识别后台账仍 0 条（轮4 A-P0-2），未修
4. **F7e 向导第3步状态持久**：已有 readiness 恢复机制但测试者仍报状态丢失，需复核 GET 接口返回内容
5. **muse-spark/opencode 密钥恢复**：无从本机获取，需用户提供新密钥后回切
6. N6（96失败逐簇对账/哨兵持久化）、N5 双cohort重跑、F5性能实测：未动

## 三、踩过的坑（经验沉淀）

1. **API 改码重启后必须重启 vite**——前端按启动时指纹配对后端，失配即全屏 503 闸门盖住侧栏（测试者 P0 的真身）
2. **SQLite 作业表身份列迁移必须同步重推导 job_id**（hash 含 profile/provider/model），否则 claim 校验击穿线程
3. **失败作业一次 retry_terminal 后 max_attempts 增长会逃出 ≤2 的自动恢复窗口**——后续需人工干预
4. **模型名漂移是常态**：本机路由/上游会换 served 名；请求名=回执名 + expected 留空 + 身份对白名单三者组合才稳
5. **轮1R的教训复验**：测试者报告里的"卡死"背后可能是多个独立根因叠加——本轮"永远 analyzing"=wake缺失+坏import+别名挂起三层同时存在
6. py-spy 在 macOS 需 root；`sample` 命令可无 root 采样线程栈（但无 Python 符号）

## 四、下一步

1. 重派三测试者（清洁空间已就绪）验证 F7 裁决 UI→promoted→mapping→facts→监查就绪 全链
2. F7f 台账接线 + F7e 状态持久复核
3. 测试通过后：N6 集成验收 + 96 失败逐簇对账 + 哨兵入持久仓储
4. N5 剩余：证据扩容新分析版本双 cohort 重跑（804 条旧结果升级）
5. 向用户索取可用的 muse-spark(opencode-go) / deepseek-v4.1(ollama-cloud) 密钥以回切指定路由

## 五、关键操作速查

- 启API：`WORKBENCH_RUNTIME_DIR=...runtime WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --app-dir $PWD --host 127.0.0.1 --port 8910 &`（先 `lsof -ti:8910` 全杀僵尸）
- 启vite：`cd frontend && npx vite --port 5177 --strictPort`
- 唤醒队列：`POST /api/projects/{pid}/modules/medical-monitoring/ai/queue/resume`
- 派发测试者：`python3 ~/.codex/tools/conference_session_runner.py --agent X --provider Y --model Z --effort E --explicit-route --prompt <文件> --output ... --stdout ... --workdir ...`（--prompt 收文件路径！）
