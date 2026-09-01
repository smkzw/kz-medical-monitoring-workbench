# B6 实施计划

1. 记录八棵树的文件/测试数量及当前 live-import 清单，锁定删除集合。
2. 迁移四类产品残余依赖：R7 相邻 runtime import、R6 harness import、D10 纯结构化转换、合成启动临时 POC path bridge。
3. 将 R7 fake harness 移到 `tests/medical_monitoring/`，机械替换 `tests/test_medical_monitoring_r7_product_router.py` 和合成启动测试中的 POC import；删除兼容身份测试。
4. 运行删除前 gate：相关模块 `py_compile`；R5/R7 产品路由、合成启动、fixture 与受影响领域测试全绿；`rg` 确认产品运行路径无 POC import。
5. `git rm -r` 删除 `poc/medical_monitoring_ai_native_r1`、`r2`、`r3`、`r3_rule_ai`、`r4`、`r5`、`r6`、`r7`，单独 commit。
6. 运行删除后 gate：医学监查聚焦回归、全部 package-native 医学监查测试、62 个前端 node 测试、Vite build、医学写作保护性子集、`git diff --check`。
7. 把数量、验证结果、保留给 B7 的冻结脚本引用和下一安全动作写入 Trellis journal；完成并归档 B6。
