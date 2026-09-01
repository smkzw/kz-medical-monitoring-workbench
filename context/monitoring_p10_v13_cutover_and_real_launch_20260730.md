# 医学监查 P10：V13 部署切换与双真实项目启动记录

## 1. 本轮问题

V12 的首批真实输出证明独立 AI 可调用、持久队列可恢复，但稳定技术元数据仍在跨域自由
命名。继续运行全部 325 个作业只会增加成本，不能形成可激活的项目级字段合同，因此按
早停原则停止 V12。

同时发现部署级边缘情况：如果服务在提示词升级后直接重启，数据库中的旧版本 queued 或
running 作业会被冷恢复 worker 继续执行。单靠用户再次提交新版本作业进行 supersede
不足以保护启动窗口。

## 2. 实施

1. 确定性元数据规则 v3 固定：
   - `SITENM -> source_metadata/site_name`
   - `SUBJINI -> source_metadata/subject_initials`
   - `VISIT -> source_metadata/visit_name`
   - `VISITNUM -> source_metadata/visit_sequence_number`
   - `Block顺序号 -> source_metadata/record_block_sequence`
   - `FORMNM__<n> -> source_metadata/form_name_duplicate`
2. 字段映射提示词升级为 V13，角色目录和语义质量目录同步。
3. 仓储新增 `supersede_prompt_versions_except()`：
   - 只按任务类型及当前提示词合同清退旧版本；
   - 覆盖 queued、running、completed、blocked、failed；
   - 清除 lease、关闭 retry、记录 `superseded_prompt_contract`；
   - 只把 proposed 候选转为 superseded，保留历史人工决定。
4. API 启动恢复顺序固定为：
   - 清退全部旧提示词合同；
   - 处理耗尽的过期 lease；
   - 唤醒当前持久队列。

## 3. 验证

- 聚焦及相邻联合回归：244 passed。
- 仓储、测试文件 lint：通过。
- 修改模块 Python 编译：通过。
- 真实运行库启动前 V12：10 completed、311 queued、4 running。
- 真实 API 启动后 V12：325 stale_input；无旧 lease；无 V12 再执行。
- 健康检查：runtime store integrity `ok`，外键违规 0。

## 4. 双真实项目 V13

### RUX-03-002

- 来源：2025-06-12 全量 listing；
- 批次：`monbatch_dffbfdc95d1e4ae7bbac6abb1227dbcb`；
- 180,113 条记录、54 个产品数据域；
- 从真实产品页面创建 175 个 V13 作业；
- 当前 4 个作业由全局独立 AI 配置领取。

### MG-K10-SAR

- 来源：2026-01-20 原始全量 listing；
- 批次：`monbatch_075b99489baf448a88b83c483ecf8eab`；
- 148,727 条记录、61 个产品数据域；
- 从真实产品页面创建 150 个 V13 作业；
- 与 RUX 共用持久队列和并发上限，等待释放槽位。

## 5. 下一验收点

只审阅最早完成的真实块：

1. 技术角色是否跨域稳定；
2. CM 与试验药物、给药和剂量变更是否分离；
3. 标准编码是否有同行术语-代码关系及独立字典版本血缘；
4. 部分日期是否被错误提升为精确日期；
5. 量表总分或派生结果是否具备可复算血缘。

出现通用合同漂移即早停并修复；通过后才允许全量队列继续并生成正式 mapping draft。
