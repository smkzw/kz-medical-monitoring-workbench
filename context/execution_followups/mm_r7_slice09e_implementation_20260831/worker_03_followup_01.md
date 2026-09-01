同一 worker_03 session 补充回归，只改 `tests/test_medical_monitoring_local_distribution.py` 与本切 artifact evidence。

在 worker_01/02 定向修复后，新增并运行至少以下聚焦测试：
1. `stop --root` 无合法 runtime config 时返回 2 且不会调用 kill；
2. 默认 aux 未启用时 8911+5174 owned 即为已启动，8984 foreign 仍阻断；aux_enabled=true 时要求三端口；
3. 两个绝对根末级同名时 root_identity_digest 与 plan_sha256 必须不同，JSON 不含绝对路径；
4. 两个真实并发 prepare-upgrade 调用：第一仍活跃时第二返回 5，不能删除第一 staging；死 PID marker 可回收。

随后重跑 36 项（加新项后总数应增加）、normal/-O/-OO × 三 hash seeds，并刷新 evidence manifest。不得改产品源码、医学写作、真实项目或启动端口。
