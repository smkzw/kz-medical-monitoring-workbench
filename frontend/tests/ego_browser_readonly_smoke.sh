#!/usr/bin/env bash
set -uo pipefail

: "${APP_URL:?Set APP_URL to an isolated local workbench URL, for example http://127.0.0.1:5174/}"

host_and_port=${APP_URL#*://}
host_and_port=${host_and_port%%/*}
host=${host_and_port%%:*}
case "$host" in
  127.0.0.1|localhost) ;;
  *) echo "APP_URL must be a local isolated URL; got: $APP_URL" >&2; exit 2 ;;
esac

task_name=${EGO_TASK_NAME:-"workbench-readonly-smoke-$(date +%s)"}
app_url_json=$(node -p 'JSON.stringify(process.argv[1])' "$APP_URL")
task_name_json=$(node -p 'JSON.stringify(process.argv[1])' "$task_name")
set +e
result=$(ego-browser nodejs <<EOF
const task = await useOrCreateTaskSpace($task_name_json)
let report
try {
  await openOrReuseTab($app_url_json, { wait: true, timeout: 20 })
  const info = await pageInfo()
  const rootPresent = await js("Boolean(document.querySelector('#root'))")
  const bodyTextLength = await js("document.body.innerText.trim().length")
  const snapshot = await snapshotText()
  const screenshot = await captureScreenshot()
  report = { ok: Boolean(rootPresent && bodyTextLength && snapshot), taskId: task.id, url: info.url, rootPresent, bodyTextLength, screenshotCaptured: Boolean(screenshot) }
} catch (error) {
  report = { ok: false, taskId: task.id, error: String(error?.message || error) }
}
cliLog(JSON.stringify(report))
process.exitCode = report.ok ? 0 : 1
EOF
)
result_status=$?
completion=$(ego-browser nodejs <<EOF
cliLog(JSON.stringify(await completeTaskSpace($task_name_json, { keep: false })))
EOF
)
printf '%s\n%s\n' "$result" "$completion"
exit "$result_status"
