# 医学监查规则发布链缺口审计

## P0

1. 前端在“规则已编译”后没有规则包草稿、影子验证、显式发布和进入 daily run 的可用
   产品链；后端影子验证仍要求医学经理填写工程字段。
2. Checklist 空状态仍可调用旧 `/modules/medical-monitoring/runs` 内置风险引擎，
   绕过已发布规则包、当前 mapping、capability snapshot 和 daily-run 状态机。

## P1

1. 直接方案事实确认接口允许客户端提交任意 deterministic template，未复用规则建议的
   mapping/capability/hash 质量门。
2. 规则采用时验证的 mapping revision、mapping content hash 与 capability hash 未贯穿
   到事实、规则、规则包、影子、发布和 daily run。
3. 用户采用规则建议已是医学决定，但编译规则仍为 candidate，规则包前又要求逐条确认，
   形成无意义二次医学批准。

## P2

- 项目切换时方案准备和批次面板未同步清空旧项目状态，后端虽多能拒绝，但界面可能短暂
  以新项目 ID 携带旧方案版本或批次发起请求。

## 最小实施顺序

1. 先关闭旧风险运行旁路，并修复项目切换清场。
2. 建立不可变的规则来源合同，将事实、候选、mapping、capability 身份贯穿全生命周期。
3. recommendation 采用直接形成已确认规则；保留“影子结果确认”和“发布”两个目的不同的
   显式动作，不再二次批准同一规则。
4. 后端自动从已冻结真实批次准备影子样本与 source row bindings，前端只展示规则、样本、
   命中/未命中、来源和差异。
5. 增加项目级规则发布抽屉，发布成功后才开放正式 daily run。

