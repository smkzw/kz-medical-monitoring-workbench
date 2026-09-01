# R7 Slice-05 合同勘误：进度读取时的过期租约重建

日期：2026-08-28  
适用合同：`FROZEN_R7_SLICE_05_BACKGROUND_RECOVERY_V0_2`  
性质：仅澄清第 1、5 节的重建边界，不扩大 Slice-05 功能范围

## 澄清

`GET progress` 可以先把已经过期的 `running` 或 `cancelling` 租约持久化为
`interrupted`：generation 加 1，并清空 owner 与 lease。该动作只用于让进程重建后的
用户看到“已停止，可继续”，不得启动或继续 worker，也不得改变 R1 的进度计数、工作项状态或
分母。

过期租约持久化提交后，再用一个 deferred SQLite 读事务读取 R1 audience progress 与 control
overlay，形成一致的本次响应快照。这里是“先完成受限的过期状态重建，再读取一致快照”，不是把
写入与读取虚称为同一个事务。

## 接受边界

- 无过期租约时，进度读取不写 control。
- 进度读取从不自动 resume，也不创建新 worker。
- 该澄清不改变真实模型、capability attempt、retry/continuation 属于 Slice-06 的边界。
