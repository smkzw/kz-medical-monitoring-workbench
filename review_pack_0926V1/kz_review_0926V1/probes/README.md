# 探针说明（必须先读）

这些是review中的**选定函数/表达式逻辑转录探针**，并非复制整个仓库，也并非产品pytest。source_excerpts省略原注释、格式和部分类型标注，保留本轮讨论的控制逻辑。原始文件版本/工具来源见source_manifest。转录文本自己的SHA只用于本包完整性，不能冒充仓库完整文件blob。

本轮默认模式实跑：28项，10项满足各自检查条件，18项未满足。多个反例可能属于同一缺陷。“criterion_met=true”不等于产品测试通过；false也不代表整个生产入口已动态复现。

```bash
python probes/backend_probes.py > backend_observations.json
node probes/timeline_probes.mjs > timeline_observations.json
```

本地已有完整repo时可用：

```bash
python probes/backend_probes.py --repo /absolute/path/to/repo
node probes/timeline_probes.mjs --repo /absolute/path/to/repo
```

Python --repo只抽取白名单AST函数/常量，避免启动main和访问运行库；Node只import纯时间轴模块。若后续代码重构导致额外依赖，应改写正式测试而不是削弱产品实现迁就摘录。B14与J14仍是明确标记的表达式探针，不会因为--repo而自动变为完整方法测试。

B03–B06实测发布helper返回值，并与已读求值器源码中indeterminate分支对照；没有在本轮调用完整引擎。B12是合成repository/provider使后台heartbeat抛错，检查该函数是否继续返回；不等于证明production complete提交成功。J系列未启动浏览器，DOM连接问题来自源码交叉核对。

只读、不联网、不含凭据或受试者资料，不调用模型、不操作真实数据库。结果写出通过shell重定向，不覆盖输入文件。
