# 医学监查 P10：旧版 Schema 多重记录身份与 Source Binding 复核

**复核日期：** 2026-07-30  
**范围：** 医学监查后端的 listing 行身份、批次入库、跨批次 diff，以及相邻的来源绑定诊断  
**边界：** 未修改前端、医学写作、运行数据库或来源文件；运行数据库仅以只读连接核对事实  

## 1. 执行结论

1. RUX-03-002 2025-04-16 文件确有 179,565 条临床记录，不是“54 域、0 记录”。
   0 记录是整批事务因重复 `business_key` 失败后回滚的表象。
2. 重复仅有 2 组，共 4 行、2 条超额记录，全部位于 `SUBJ`：
   - 每组均为同一受试者、同一表单和相同重复键；
   - 不是完全重复；两行的 `SUBJSTA` 和 `PAGELMDT` 不同；
   - 后续 2025-06-12 快照只保留“完成试验”记录。
3. 物理行号不能作为跨批次身份。两组中“完成试验”记录在一组排第二、另一组排第一，
   且后续快照物理行位置发生变化。
4. 单纯在重复键后加行号或顺序号也不能解决问题。旧文件缺 `VISTOID/FORMOID`，新文件
   新增这些字段，旧、新两批原 `business_key` 的交集为 **0**；只修导入会把全部记录
   错报为新增/删除。
5. 本轮采用“稳定存储键 + EDC 显示语义别名 + 多重记录内容变体 + 失败关闭”的受控方案，
   无需改数据库表结构：
   - 原主键继续作为存储身份；
   - 同一基础键有多条记录时，按完整内容哈希生成记录实例键，完全相同行仅用 copy
     ordinal 表达数量，不使用物理行号；
   - EDC 行同时保存不依赖 OID 的显示语义别名；
   - diff 先按原主键匹配，再按唯一别名、共同字段完全一致、单一剩余项的顺序匹配；
   - 多对多仍无法唯一配对时不猜测，并阻止相关 removed 行自动判为“已解决”。
6. diff 算法升级为 `monitoring_batch_diff.v3`。跨 schema 配对只比较两批共同字段；
   新增 `VISTOID/FORMOID` 或编码列作为 schema 变化单列，不再仅因字段新增把每行判成变化。

## 2. 来源与复现证据

### 2.1 历史文件

- 文件：
  `/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/2-RUX-03-002-现场核查项目层面文件目录-20260424/21.医学监查计划/21.2-医学监查报告/9-第九次/附件1：RUX-03-002_data listing_20250416_附量表间评分变化比较.xlsx`
- SHA-256：
  `376a299e8c01617371b26d9d6dd59bd42cbb642304b2c1d440faedd9fbfc2ea8`
- 来源等级：B 级处理后项目级全量快照。
- 物理结构：54 sheets，其中 53 个核心 EDC sheets + `Code_List`。
- 解析结果：179,565 条临床记录、240 名受试者、20 个中心。

### 2.2 重复键量化

| 指标 | 结果 |
|---|---:|
| 解析记录 | 179,565 |
| 原唯一键 | 179,563 |
| 重复键组 | 2 |
| 重复组内记录 | 4 |
| 超额记录 | 2 |
| 最大组大小 | 2 |
| 涉及域 | `SUBJ` |
| 完全重复组 | 0 |
| 同基础实体但内容不同 | 2 |

两组均只在 `SUBJSTA`、`PAGELMDT` 上不同。2025-06-12 当前快照中，相同受试者均只保留
与历史快照完全一致的“完成试验”行，因此这两条“筛选中”行应作为真实移除记录保留，
不能在导入阶段静默去重。

### 2.3 旧、新 schema 身份差异

| 指标 | 修复前 | `v3` |
|---|---:|---:|
| 历史记录 / 唯一实例键 | 179,565 / 179,563 | 179,565 / 179,565 |
| 当前记录 / 唯一实例键 | 180,113 / 180,113 | 180,113 / 180,113 |
| 原主键直接交集 | 0 | 保留为主键快速路径 |
| 跨 schema 别名配对 | 不支持 | 179,446 |
| 新增 | 180,113（错误） | 667 |
| 删除 | 179,565（错误） | 119 |
| 共同字段变化 | 无法判断 | 55,331 |
| 共同字段不变 | 无法判断 | 124,115 |
| 缺失域 | 不适用 | 0 |

179,446 个别名配对中：

- 179,444 个由唯一显示语义别名直接配对；
- 2 个多重记录组通过共同字段完全一致配对到“完成试验”行；
- 剩余 2 条旧“筛选中”行计入 119 条移除记录。

## 3. 身份与 Diff 契约

### 3.1 存储身份

`business_key` 仍是批次内唯一、可索引的存储键。无碰撞时保持既有键不变。碰撞时：

```text
<identity_base_key>|instance:<content_variant_sha256_prefix>:<copy_ordinal>
```

- `content_variant_sha256` 来自域和完整行数据的规范化 JSON；
- 物理行号只保留在 `source_locator`，不进入业务身份；
- 内容完全相同的多份记录用 `copy_ordinal` 保留数量。它们彼此不可区分，因此 ordinal
  只表示多重性，不声称对应特定物理行。

### 3.2 EDC 显示语义别名

别名只用于主键不一致后的受控匹配，组成包括：

`domain + sheet 语义 + STUDYID + SITEID + SUBJID + VISIT + VISTREP + FORMNM + FORMREP + RECREP`

当两批均有 OID 时，原主键优先，可抵抗显示标签变化；仅一批缺 OID 时，显示别名提供
兼容路径。若旧批缺 OID且显示名称也变化，系统不会猜测匹配，相关记录保留为新增/删除。

### 3.3 匹配顺序

1. 完全相同 `business_key`；
2. 一对一的版本化身份别名；
3. 同一别名组中，在两批共同字段上完全一致的记录；
4. 共同字段完全匹配后仅剩一对记录；
5. 仍为多对多时停止自动配对，removed 行加入 `removal_resolution_blocked_keys`。

API 不返回十几万条匹配日志，只返回按匹配依据的完整计数和最多 50 条有界样本。

### 3.4 字段变化

配对行的 `changed/persisting` 只比较两批共同字段；新增或删除字段由 schema diff 单列。
这避免 `VISTOID/FORMOID` 或 CM 编码列新增污染每条记录的医学变化判断。共同字段中的
`PAGELMDT` 等技术字段仍会被如实记录；是否进入医学风险由后续已冻结字段映射和规则决定，
本轮不在原始 diff 层静默删除。

## 4. Source Binding 相邻诊断

### 4.1 实际运行态事实

只读查询固定 SHA 对应的 `monitoring_sources`，存在两条不可变来源记录：

1. `raw_full_snapshot_candidate`，首次旧分类；
2. `processed_full_snapshot`，分类器升级后产生，医学说明仍为首次 B 级说明。

二者指向同一内容对象，但 `source_id` 不同。因此旧 raw 分类本身不会阻止新 processed
分类；当前唯一索引已包含 `source_class`。

页面再次提交新的医学说明时报
`source validation binding was reused with different metadata`，直接原因是：

- 第一次 processed 导入先成功提交了 source registration；
- 后续批次行物化因重复键失败，但已登记的 processed source 不回滚；
- 再次提交同一 `source_entry_id + validation_id + source_class` 且医学说明变化，
  命中既有 processed binding；
- 仓储把医学说明、warnings、parser/validator metadata 的任何变化视为完整性冲突。

### 4.2 最小安全建议

该问题与行身份修复相邻但属于独立的来源版本模型和数据库迁移，本轮未混改。建议下一切片：

1. 内容对象继续按 SHA-256 去重且不可变；
2. 内容校验记录继续按 validation revision 复用，不重新消耗；
3. source binding 增加：
   - `binding_revision`；
   - `classification_version`；
   - `binding_sha256`；
   - `supersedes_source_id`；
4. 相同内容、相同全部 metadata 的请求重放原 source；
5. 相同内容但分类器版本、source class、医学说明或 warning 集发生变化时，新建
   source binding revision，旧记录保持不变；
6. 新 revision 必须显式指向所复用的 `validation_id + validation_revision`；
7. 内容字节变化仍必须使用新的 source entry/内容对象，不得借“修订说明”覆盖。

这能同时满足“旧错误分类可追溯”“新分类可继续使用”“医学说明可修订”“内容校验不重复”
四项要求。实施时应迁移唯一索引，不得简单放宽或删除唯一约束。

## 5. 代码变更

| 文件 | 变更 |
|---|---|
| `services/api/app/monitoring_batch_diff.py` | 行身份 v2、多重记录保全、EDC 别名、受控匹配、diff v3、歧义失败关闭、匹配计数/有界样本 |
| `services/api/app/monitoring_batch_repository.py` | 仓储级 diff 复用统一 v3 算法，避免与详细 diff 语义分叉 |
| `services/api/app/monitoring_batch_service.py` | 对外返回身份匹配计数和有界样本 |
| `tests/test_monitoring_batch_diff.py` | 多重记录、顺序不变、OID schema 扩展、歧义关闭及真实 RUX 回归 |
| `tests/test_monitoring_batch_repository.py` | 冻结批次仓储级别名对齐回归 |
| `tests/test_monitoring_batch_service.py` | diff 算法版本契约更新 |

## 6. 验证

### 6.1 聚焦回归

- 非真实文件聚焦回归：58 passed，5 deselected。
- 完整批次/diff/repository/service/lifecycle 回归：修复测试数据后 63 passed；
  首轮唯一失败是测试把 `business_key` 自身写入业务字段，修正为相同业务字段后通过。
- 下游 daily-run、router、analysis、rule runner、field profiler 回归：44 passed。
- Python 编译检查：通过。
- `black --check`：本机 Python 环境未安装 Black，未执行；未引入该依赖。

### 6.2 真实文件回归

- RUX 2025-04-16 旧 schema → 2025-06-12 新 schema：通过。
- RUX 2025-06-12 当前全量 listing 唯一键回归：通过。
- MG-K10 148,727 行全量 listing 访视 fallback 唯一键回归：通过。
- 三项真实文件测试：3 passed，71.37 秒。

## 7. 残余边界与后续动作

1. 现有已冻结的 v2 批次没有 `identity_aliases`，不会被追溯改写。跨 OID schema 的
   v3 验证应重新从固定来源创建批次；不能直接修改旧批次行。
2. 旧批缺 OID且显示名称也变化时，只凭 listing 无法证明同一实体；系统按新增/删除
   保守处理。若业务必须自动对齐，需要冻结字段映射或 EDC 数据字典提供显式别名。
3. 55,331 条共同字段变化是原始事实层结果，其中包含技术更新时间变化；医学风险层应
   依赖字段角色映射过滤，不能在本切片删除原始字段。
4. source binding revision 尚未实现；在完成该迁移前，同一 processed binding 修改
   医学说明仍会冲突。临时绕过不能修改旧行或删除唯一索引。
5. 本切片没有重启 API、没有重新导入运行批次，也没有触发独立 AI。需在主 P10 LOOP
   重启载入代码后，通过真实页面使用新幂等键重新导入并核对 179,565 行。
