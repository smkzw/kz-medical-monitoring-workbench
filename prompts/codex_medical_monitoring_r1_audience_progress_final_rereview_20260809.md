请继续同一审阅 Session，再次只读复核当前最新文件。你的第二次 VETO 基于上一版 SHA：

- audience_progress.py `4ef124...`
- test_audience_progress.py `a1d45f...`

该 VETO 后两文件已再次修订，当前候选 SHA：

- audience_progress.py `d2335130b5498233197bacd2597f17e30c68a077a0ada03868f283c230a3b7c5`
- test_audience_progress.py `682c1883516ccdfa7808c399ca32c861a06ff58a5e1ee985df84e807455f646b`

请先核对 SHA 并重新读取，不能沿用旧版结论。针对第二次 VETO，纯 ASCII target 现在除格式外还必须：

1. 含至少一个真实编号数字；
2. 不含受控技术目录词段；
3. 中文临床名称仍可直接使用。

新增 fail-closed 用例：`SRC/MM_R1`、`DATA/PRIVATE`、`FOO/BAR`、`A/B`、
`SRC/CONFIG`、`README/SETUP`、`R1/POC`；新增允许用例：`S001/AE`、`MG-K10`、
`SITE01`、`001-001`、`01/PD`、`受试者 S001`。当前主进程 focused 为 46 passed，
但不替代你的独立复核。

请复跑第二次 VETO 的真实 Store probe、全部此前 probe、允许用例、聚焦与相邻测试、
只读探针，并确认起止 SHA 稳定。输出新的 ACCEPT/VETO；若 ACCEPT，明确 P0-P4=0，
同时把无法从任意字符串绝对判定“技术含义”的边界作为残余风险，而不是继续把任意合法
临床编号构造成无限 path 变体。仍不得修改文件、启动服务或访问真实项目/provider/harness。
