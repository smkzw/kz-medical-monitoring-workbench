# E2E失败诊断（2026-10-15 主代理直查）

## 结论：桥已通，E2E失败=上游AI流瞬断（非重构缺陷）

## 证据
1. **直查SM2-r2（proj_user_2b125f77bd3c）**：24个listing_field_mapping job全部completed、每job候选=1、digest跨job唯一一致（blob展开验证full_profile_sha256存在）；GET mapping-candidates返回HTTP 200（state=candidates_ready，60字段/58系统采纳/2用户问题）。
2. **直查SM3-r2（proj_user_4f262469d486）**：28 job中2 failed（provider_runtime_error=上游AI流错误事件）、1 queued、2 running、23 completed；GET mapping-candidates同样返回HTTP 200——桥在有失败作业时也能投影（部分采纳口径）。
3. **payload blob结构核验**：field_profile.$section_blob展开后含full_profile_sha256（blob表4352行健康），桥的digest推导链完整。
4. **E2E当时失败模式**："6次尝试全部失败、失败即时返回"——与provider_runtime_error即时返回一致（非卡顿）；实施工程师的500兜底留真栈修复（0db80701）在位。

## 判定
- 重构代码（S1-S7+verifier死锁修复）**功能正确**——桥的四个raise条件均未命中（digest存在且一致/候选=1/白名单合规）。
- E2E门失败根因=**生成窗口期撞上cms-router上游流瞬断**→识别job failed→测试者点击重试时新一批job又撞上→45分钟内反复。
- 处置：retry-failed清失败作业后，**重开专项续攻E2E门**（上游通道当前实测3.6秒健通）。
