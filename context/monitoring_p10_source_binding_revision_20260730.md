# 医学监查 P10：历史来源不可变修订与 Source Binding Revision

**完成日期：** 2026-07-30  
**范围：** 医学监查 data listing 来源绑定、批次导入、旧 SQLite 模式迁移及派生全量来源验证  
**边界：** 未修改字段映射仓储、字段映射激活、前端或医学写作；未清理、改写或迁移真实运行库

## 1. 执行结论

本切片已解决同一 `source_entry_id + validation_id` 在来源分类器版本、来源分类、
医学说明、warning 集或相邻解析/校验元数据变化后无法继续导入的问题。

新的来源模型将以下对象分开保存：

1. **内容对象：** 继续按文件 SHA-256 去重，字节不可变；
2. **内容校验：** 继续显式引用原 `validation_id + validation_revision`，不重复消耗校验；
3. **来源解释修订：** 每次解释变化创建新的 `source_id` 和 `binding_revision`，
   通过 `supersedes_source_id` 指向前一修订，旧行不更新、不删除。

完全相同的当前元数据仍幂等返回当前修订。若修订历史为 A→B→A，第三次 A 会创建
显式修订 3，而不是错误返回最早的修订 1，因此完整保留医学解释的先后顺序。

## 2. 不可变来源合同

每条 `monitoring_sources` 新增：

| 字段 | 含义 |
|---|---|
| `binding_revision` | 同一来源登记与校验谱系内，从 1 开始递增的来源解释修订 |
| `classification_version` | 生成该来源分类结论的分类器/验证流程版本 |
| `binding_sha256` | 来源内容、校验引用、分类、warning、医学说明等规范化元数据摘要 |
| `supersedes_source_id` | 前一来源解释修订；首修订为空 |

谱系键为：

```text
project_id + source_entry_id + validation_id
```

当前最新修订与请求的 `binding_sha256` 完全相同时幂等重放；不同时创建下一修订。
文件字节变化时，即使来源登记和校验 ID 相同，也失败关闭并要求创建新的来源登记，
不得借“修改医学说明”替换内容对象。

数据库新增 `BEFORE UPDATE` 和 `BEFORE DELETE` 触发器。旧来源绑定无法被 SQL 静默覆盖
或删除；修订只能通过插入新行表达。

核心实现：

- `monitoring_batch_repository.py:123`：来源修订返回合同；
- `monitoring_batch_repository.py:556`：旧库迁移与不可变约束；
- `monitoring_batch_repository.py:896`：幂等重放、修订创建和内容字节边界；
- `monitoring_batch_service.py:27`、`:168`：当前来源分类器版本显式绑定。

## 3. 医学来源等级边界

`processed_full_snapshot` 代表已经承认其为 **B 级处理后全量快照** 的来源。任一谱系曾出现
该分类后，仓储拒绝再创建 `raw_full_snapshot` 或
`raw_full_snapshot_candidate` 修订，防止通过改名把处理后文件伪装为 A 级原始 EDC 导出。

修改医学说明时，来源分类仍保持 `processed_full_snapshot`；既有 B 级基线完整性门仍要求：

- `source_authority_grade == "B"`；
- 用户明确确认处理后来源；
- 非空医学说明；
- 不得填写 A 级来源证明。

本切片没有改变或放宽上述基线门。

## 4. 派生全量来源兼容

原实现会把 `raw_snapshot_with_format_defect` 来源行直接 `UPDATE` 为
`verified_derived_full_snapshot`，与不可变来源合同冲突。现改为：

1. 原始父来源保持原 `source_id`、原分类和原始字节；
2. 派生守恒证明继续引用原始父来源；
3. 新建 `verified_derived_full_snapshot` 来源修订并指向原始父来源；
4. 批次的当前来源绑定切换到新修订；
5. 返回结果同时给出当前来源 ID、原始来源 ID、修订号和继承关系。

这样既能让后续批次完整性门读取已核实的派生分类，又不会修改原始来源事实。

## 5. 迁移兼容

SQLite 旧表的内联唯一约束

```text
project_id + source_entry_id + validation_id + source_class
```

无法通过 `ALTER TABLE` 安全移除，因此初始化过程执行受控表重建：

1. 在事务中读取全部旧来源行；
2. 按谱系及既有创建顺序分配 `binding_revision`；
3. 计算 `binding_sha256` 并补充 `legacy_unversioned` 分类版本；
4. 生成相邻 `supersedes_source_id`；
5. 原样保留旧 `source_id`；
6. 重建表、索引与不可变触发器；
7. 执行 `PRAGMA foreign_key_check`，有任何错误即回滚。

迁移同时识别曾短暂存在的“`binding_sha256` 唯一索引”中间模式，并将其改为普通查询索引，
以允许 A→B→A 的显式回退修订。

## 6. 真实运行库副本验证

为避免影响正在运行的工作台，使用 SQLite 在线备份创建临时副本，在副本上初始化新仓储。
未直接修改、删除或迁移真实运行库。

验证结果：

| 检查 | 结果 |
|---|---:|
| 迁移前/后来源数 | 6 / 6 |
| 旧 `source_id` 保留 | 100% |
| 批次来源引用 | 5 条，全部保持 |
| 派生证明来源引用 | 1 条，保持 |
| 新增修订字段 | 4/4 |
| `binding_sha256` 长度 | 全部 64 |
| 外键违规 | 0 |

副本中的同一来源已有一条旧 raw 分类和一条后续 processed 分类。迁移后形成：

```text
revision 1: raw_full_snapshot_candidate
revision 2: processed_full_snapshot
            supersedes revision 1
```

这与实际历史事实一致，也证明旧错误分类不会被删除或覆盖。

截至本报告落盘，真实运行库仍为旧 17 列模式，共 6 条来源记录，4 个新字段均未出现。
后续在主 P10 LOOP 的受控 API 重启时，仓储初始化会自动执行已验证的迁移；不需要也不允许
手工清理旧来源。

## 7. 测试与验证

### 7.1 定向回归

```text
tests/test_monitoring_batch_repository.py
tests/test_monitoring_batch_service.py
tests/test_monitoring_batch_api.py

49 passed
```

覆盖：

- 相同当前元数据幂等重放；
- 医学说明变化创建新修订；
- 分类器版本变化创建新修订；
- A→B→A 形成显式第三修订；
- 相同登记/校验下替换文件字节失败关闭；
- B 级处理后快照不得变更为 raw 来源；
- 旧来源 SQL 更新和删除被拒绝；
- 旧模式迁移；
- 中间唯一 hash 模式迁移；
- 派生全量验证生成新修订且保留原父来源；
- API 返回路径不泄露及幂等冲突合同。

### 7.2 相邻回归

```text
monitoring batch repository/service/API/diff/rule runner
daily monitoring router
source classifier/revision/approval gate

100 passed
```

运行时长约 3 分 44 秒。仅出现既有 FastAPI `on_event` 弃用提示，以及真实 Excel
页眉、样式解析提示；没有本切片新增失败。

### 7.3 静态检查

- Python 编译检查：通过；
- `ruff`：当前环境未提供该命令，未执行；
- 变更文件 SHA-256：

| 文件 | SHA-256 |
|---|---|
| `monitoring_batch_repository.py` | `67bfcad3a82a9ca1fc55d7948b769c224c5b26944ff7ed9009f58679458b03c1` |
| `monitoring_batch_service.py` | `12abbb2849985f84d16ae492cf1859561a8d0852eb90bfd3d07c16a6c041b325` |
| `test_monitoring_batch_repository.py` | `afff7ce5d275e482ff151266509ba675a9097d6251c2644ab3b4509da75a4bb4` |
| `test_monitoring_batch_service.py` | `8c3cf03620ece65caaf8264b208d88cf906f7b77d294f049ba1a36601043d460` |

## 8. 后续动作

1. 在主 P10 LOOP 的受控 API 重启中加载新代码并自动迁移真实运行库；
2. 重启后只读核对来源数、修订链、批次/证明引用及外键；
3. 通过真实页面重新提交 2025-04-16 历史 listing 的医学说明；
4. 确认创建新的 processed 来源修订并成功物化 179,565 条记录；
5. 保留此前失败批次和旧来源作为审计事实，待 P10 最终清理阶段按明确清单处理，
   不在本切片直接删除。

