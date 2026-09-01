# Codex Conference Review: medical_writing_ai_change_application_20260713

Date: 2026-07-13

## Verdict

通过会商并完成实现与独立验证。该切片只批准“医学已批准AI建议显式应用到版本化工作副本”的契约，不代表AI内容本身、工作副本终稿或整个医学写作子系统获得正式医学批准。

## Boundary Compliance

- Hermes参与者和主席仅执行只读审阅并输出建议；生产源码、测试、浏览器验收和最终写入均由Codex完成。
- 四个模型均完成同一各自session内的三轮，不以多个一次性回答替代续接。
- 会商范围限于研究方案工作副本批准应用，不外推到DOCX回写、正式导出、电子签名或其他文档类型。

## Participant Outputs Reviewed

- `aishuo/MiniMax-M3`: 接受原子事务、服务端取批准文本、锁定/状态门、幂等和源DOCX只读；不采用其脱离现有项目/章节路由的working-copy-id接口方案。
- `buddy/deepseek-v4-pro`: 接受与现有保存接口一致的body CAS、严格批准门、服务端建议绑定和富文本纯文一致性检查。
- `opencode-go/mimo-v2.5`: 接受跨项目绑定、结构化富文本合并、失败回滚和重复应用防护。
- `buddy/glm-5.2` chair: 确认四方共识并要求Codex以实际代码约定裁决路由、锁定和rich-text边界。

## Codex Decisions

1. 使用既有项目/章节/修订线程作用域路由，客户端只提交期望版本、actor和幂等键，不提交替换正文。
2. 同一事务完成前置条件、精确段落替换、revision递增、快照、workflow audit、runtime audit和幂等记录。
3. 同一幂等键重放不创建第二版本；同一线程的第二次业务应用拒绝。
4. rich-text仅在选择文本落于一个文本节点时保留marks并替换；跨节点或纯文不一致时回滚。
5. 前端dirty、锁定、非批准、无accepted suggestion或已应用状态均不能发起应用。

## Independent Verification

- 79项相关测试及775项全仓测试通过，含三真实方案、重启、CAS、快照稳定幂等回放、故障注入回滚、跨章节、文本漂移和rich-text破坏性测试。
- RUX、D001、PNH在2048x1024内置浏览器完成真实操作，均无横向溢出；原始章节不含新增句而工作副本含新增句。
- 三项目SQLite记录各为revision 1、一个不可变应用快照和一个应用审计，来源定位各不相同，未出现项目固定规则。
- 前端生产构建通过；保留既有bundle size警告。
- 主运行时SQLite schema 14且integrity check为`ok`；应用路由已出现在生产OpenAPI。

## Remaining Risk

- 身份仍为`unverified_client_claim`，不构成电子签名。
- 尚无DOCX round-trip、Word tracked changes/comments或正式导出。
- 未来文档类型必须使用同一契约重新做至少两个真实项目验证，不能因研究方案通过而外推为IB/ICF/CTD等已完成。

## Final Decision

当前切片可以并入持续构建基线。未发现需要参与者重跑的分歧；MCP event-loop关闭异常发生在三轮结果落盘之后，作为清理噪声保留记录。
