# 阶段 F：本地交付、演练与清理

## Goal

工作台一键启动、真实备份恢复、通知确认、性能基线及经确认后的磁盘清理。

## Requirements

- Deliver medical monitoring inside the existing local workbench with one-click start/stop and no manual port management.
- Exercise one full backup → restore → validation flow on real project data.
- Confirm one real local notification manually.
- Record real full/incremental run duration and storage use.
- Archive or delete August monitoring artifacts only after explicit user confirmation.

## Acceptance Criteria

- [ ] One-click local launch works and medical monitoring shares the workbench shell.
- [ ] Backup/restore validation passes and local notification is confirmed.
- [ ] User confirms closure; tag `mm-v1` exists.

## Constraints

- No standalone MedicalMonitoring.app; no destructive archive/database cleanup without a separate explicit confirmation.
