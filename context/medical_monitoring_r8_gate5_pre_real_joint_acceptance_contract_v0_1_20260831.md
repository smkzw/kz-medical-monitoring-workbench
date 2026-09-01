# 医学监查 R8 G5 预真实联合独立接受合同 v0.1

状态：`FROZEN_FOR_INDEPENDENT_REVIEW`  
日期：2026-08-31  
上位依据：R8-0 联合准入合同 §8-§9，G2/G3/G4 权威接受记录  
范围：只做联合证据、依赖摘要、状态机顺序与禁止声明独立审阅；不改产品源码，不访问真实项目，不调模型，不启浏览器/服务

## 1. G5 的唯一目标

G5 不增加功能。它只独立判定：当前文件系统中的 G2 synthetic runtime、G3 Path A
通知决策与 G4 synthetic 通知/§15.4 程序是否在同一版本上共同有效，且没有被后续变更、过期摘要、隐式路由或越界声明污染。

G5 通过只解锁 G6 synthetic `ego(lite)`；它不解锁真实项目、真实模型、真实通知或真实 §15.4。

## 2. 五个必经检查

1. **顺序与状态**：G0/G1→G2→G3→G4 权威记录全部存在且未自我扩大；不得跳到 G6/G7/G8。
2. **依赖摘要**：`context/medical_monitoring_r8_gate5_pre_real_evidence_manifest_v0_1_20260831.json`
   中每个 path/SHA 必须与当前文件一致。任一不一致即 `stale/superseded`，不得继承通过。
3. **语义兼容**：G4 对 `manage.py`/README/发布清单的受控扩展会使 G2 的历史文件摘要过期；G5 必须以当前源码重跑 G2/G4 决定性回归，不得把 G2 历史 hash 冒充当前 hash。
4. **联合边界**：合成入口仍不得启动 8911/5174/8984、读取真实项目、调用产品 harness/VLM/LLM、启动任何浏览器或修改医学写作。
5. **禁止声明**：结论只能为 `PRE_REAL_INDEPENDENT_ACCEPTED`，并必须明确列出未接受的真实通知、真实 §15.4、真实项目/模型、产品浏览器、医学质量、G6-G15 及 R8 总体。

## 3. 决定性验证

- 重建并校验 G5 evidence manifest 的全部 path/SHA。
- 重跑 G4 聚焦套件与 G2/R7 相邻回归。
- 重跑 §15.4 normal/`-O`/`-OO` × 三 hash seed 确定性。
- 独立核对 8911/5174/8984 停止，并在审阅前后重建医学写作目录指纹。
- fresh-context 独立审阅按 P0-P4 给出 `ACCEPT|REVISE`；只有 P0/P1 关闭且无过期证据时才能写 G5 接受记录。

## 4. G6 解锁条件

G5 独立接受后，G6 仍需先冻结单独的 synthetic audience-facing 验收合同。G6 只允许实际本地应用 + synthetic fixture + mock/recorded adapter + synthetic binding digest，所有用户路径必须通过 `ego(lite)` 从真实入口操作。在 G6 合同冻结和实施前，不得启动应用或浏览器。
