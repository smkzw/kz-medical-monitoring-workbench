# B7 技术设计：测试与冻结门归一

## 判定原则

- 删除“文件内容必须等于某个历史 SHA”“必须在 -O/-OO 与多个 `PYTHONHASHSEED` 下重复跑”“先刷新 digest 才能继续”的代际验收门。
- 保留运行时真正需要的内容地址、来源 SHA、CAS、identity/lifecycle、快照可比性、结构校验与确定性结果断言。64 位十六进制本身不是删除理由，必须按语义分类。
- 删除只服务于已删 POC/G6 的一次性 generator/verifier；不改医学写作生产代码，不把医学写作现存失败混入本工单。

## 当前清理面

1. 删除 B6 已确认的 30 个未被当前 gate 调用、且路径指向已删 POC 的 R5 S3–S6 slice-era generator/verifier。
2. 审查 `tests/test_d08_artifact_generator.py`、`test_d09_artifact_generator.py`、`test_d10_artifact_generator.py` 及相邻 D07 文件：移除整文件 SHA/固定源路径 pin；保留生成输出结构、字段闭合、确定性与领域行为覆盖。
3. 删除或收敛 optimizer/hash-seed 矩阵入口，正常解释器下保留一次确定性行为验证。
4. 不清理普通来源内容 SHA、fixture identity、CAS 或真实 listing 完整性断言；不改 `mm_r7:project_audit:genesis:v1` 等运行时 digest 域分隔常量。

## 验收

- 当前医学监查测试与构建无需 digest refresh、POC 路径或优化矩阵即可通过。
- `rg` 不再发现面向已删 POC 的可执行脚本或 whole-file migrated-source SHA pin。
- 产品路由、风险/Journey/Query 语义、候选/事实分离和中文用户文案的既有行为测试仍在并通过。
