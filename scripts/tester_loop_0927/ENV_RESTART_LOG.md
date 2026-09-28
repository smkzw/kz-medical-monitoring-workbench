# 环境重启留痕（共享基础设施）

## 2026-09-28 10:5x（测试循环R1：缺陷修复后 API+vite 双重启）

- 操作者：修复员（测试循环R1）
- 原因：R1-01/02/03/04/05/06 修复涉及后端 Python（workflow/routes/main/schema_manifest/run_setup）与前端（App.jsx/向导/api client），API 与 vite 必须指纹配对双双重启。
- API：`lsof -ti:8910 | xargs kill` 后按标准命令以 `WORKBENCH_RUNTIME_DIR=runs/phase_c_mgk10_authority_v2_20260905/runtime` 启动（uvicorn 127.0.0.1:8910）。
- vite：`lsof -ti:5177 | xargs kill` 后 `npx vite --port 5177 --strictPort`。
- 自检：`curl http://127.0.0.1:8910/api/runtime-readiness` → `"ready": true`；`curl -o /dev/null -w %{http_code} http://localhost:5177/monitoring` → `200`。

## 2026-09-28 下午（测试循环R2：缺陷修复后 API+vite 双重启）

- 操作者：修复员（测试循环R2）
- 原因：R2-01/02/03/05/06 修复涉及后端 Python（document_authority_jobs/routes/source_content_validation）与前端（向导/mapping状态/项目下拉），API 与 vite 双双重启。
- API：`lsof -ti:8910 | xargs kill` 后按标准命令以 `WORKBENCH_RUNTIME_DIR=runs/phase_c_mgk10_authority_v2_20260905/runtime` 启动（uvicorn 127.0.0.1:8910）。
- vite：`lsof -ti:5177 | xargs kill` 后 `npx vite <frontend绝对路径> --port 5177 --strictPort`（注：须以 frontend 为 root 启动，从仓库根启动会 serve 错误目录返回 404）。
- 自检：runtime-readiness → `"ready": true`；`http://localhost:5177/monitoring` → 200；向导模块 vite 转换 200。
