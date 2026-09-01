# 医学监查 R4-D10 authority 修订与 runtime Worker-01 验收记录

日期：2026-08-18  
结论：`ACCEPT_WORKER01`  
范围：修订后的 D10 synthetic/offline artifact authority chain，以及 runtime
Worker-01 typed contract、test-only adapter 与 deterministic evaluator。此结论不
接受 Worker-02/03、整个 D10 runtime、R4 总体、R5/UI、8911/服务、真实项目/模型、
产品、正式临床结论或医学写作。

## 为什么重开

原 2026-08-17 artifact freeze 把 D10-CASE-078/093/107/295 中故意注入的
`SRC-REV-EXTERNAL-001` 同时写入 fixture authority 的 accepted set，导致来源攻击
与权威镜像一致。runtime Worker-01 独立审阅同时发现：authority gate 晚于
`project_facts`，且删除 ModelEvidence 可绕过已有 model pins。原验收记录保留为历史
证据，但上述结论被本记录显式取代，不是静默改写。

## 修订结果

- fixture authority 312/312 entries 各只含一个真正 accepted source pair；catalog
  中四个 extra pair 仍保留为攻击输入。
- artifact conformance 证明全部 authority anchors 出现在 fixture；runtime 与独立
  semantic verifier 按“submitted 是 accepted 的闭集子集”判断，不强制错误的集合相等。
- authority missing、identity、source、ModelEvidence 缺失或 pin 不一致均在
  `project_facts` 前返回零医学 unit gate。
- runtime 不读取 artifact/oracle/registry/quota/generator/verifier/test，不依据 case id、
  mutation metadata、`SYN`/prefix 或自由文本推断来源权威。

## 当前 SHA-256 锚点

- frozen contract `c613bb7cad82caa6fa477ee2dd28bfca48b805b73503c646401a0aa237deff95`
- authority generator `4faa1317eb184fc91b2d934f944a25c484788469fb5cd1dc6221b875272f9e1d`
- catalog generator `84c43a81952a1b33fbfcaf6cf244b13cf6eeda5625a501f0bc76b369a6df3dfe`
- oracle generator `1a98ea1948001dd72d5069a8418fa12cc7b5018c456d5b886e62a56cd0ffd1c5`
- independent verifier `ed126ddb4344e87be6ee51086db5ec21326766086669bcc7575b15904e0c9f99`
- artifact test `f2eed9f905655ed7866d92339abf446c5e64fecdd8bc3a5b7a3c49cd5760c5df`
- authority `191f4b4fcddfebfbc29d48111bf8b45477d435ae62def0199bed0edd587fa7f0`
- catalog `40ce96b2e5c188167cacbe03a8b5a80260886276cbacd1edbd1261f9b7927939`
- oracle `435492cd2c86ef0e3a6b6061f9cd992d12396579a07b8f186c3c533fd9260ec3`
- challenge registry `2f2763c5b351331ab103882dab72d996f10ede08e45d627a4baacb3fdb3709d6`
- quota `7041cd4167ba5c604d20bfefbbe9c6aaa136ed3d0d933d064f80cf819ba88ffa`
- external verifier anchor `c7a2a6be26c46185c2a84a806ec2b6ebda3f81d354844e8ec884a1e185166499`
- D10 contracts `19a3b278e3d2e587be0dab5411827eaa32611e2ff95a1424cbc83c27194bdd78`
- D10 adapter `d4e81606e660089166f89a4c87584e8d2d728679897f93c4b0eac60e8d1c3db7`
- D10 evaluator `204fe88f3b4a5aeeaa8205e57e841f594974767785612eeeff655e7482af96af`
- adapter test `cde15796351db460d92098447498b6c52118024ce6b2a2a7db1cac43b7e8604f`
- runtime test `21808659a85bbda82a4219ec33ed83dc420a5e201d494857c0e438e69cc74a2f`

## 决定性验证

- 三个 generator check、独立 verifier `0 problems / 0 cases failing`。
- D10 artifact `107 passed`；D10 runtime `30 passed`；312/312 disposition/core/
  trace/source parity 为零差异。
- D09 artifact `99 passed`、D09 runtime adjacency `145 passed`。
- compile/static closure、外部 verifier SHA anchor 均通过；anchor 为 `0444 uchg`；
  8911 无监听。
- 独立 Luna/max verifier 对稳定 17-file snapshot 首尾 SHA 零漂移并返回
  `ACCEPT_WORKER01`。

## 下一安全动作

只解锁 D10 runtime Worker-02：renderer-neutral 投影、中文原生 audience text、
风险标记/hotspot、跨中心与历时 count surface、完整 Query、visibility/deep-link 与
R2 handoff authoritative rebuild。Worker-03 及其余冻结面继续锁定。
