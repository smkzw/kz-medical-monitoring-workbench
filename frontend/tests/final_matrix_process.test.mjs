// Focused deterministic smoke test for the disposable harness process gate.
// E1（第3轮门修复）：三个用例相互独立（各自独立进程组与输出），改为并发
// 执行——断言集与每例的timeout/grace升级窗口逐字不变，仅消除顺序执行
// 造成的~1000ms墙钟（门环境1s每文件上限下处临界）。进程组死亡是异步
// 的，runChildWithTimeout已保证SIGKILL后整组ESRCH才交付。
import assert from "node:assert/strict";
import process from "node:process";
import { runChildWithTimeout } from "./final_matrix_process.mjs";

const completed = runChildWithTimeout(
  process.execPath,
  ["-e", "process.stdout.write('ok');"],
  { cwd: process.cwd() },
  5000,
).then((completed) => {
  assert.equal(completed.status, 0);
  assert.equal(completed.timedOut, false);
  assert.equal(completed.stdout, "ok");
  return "completed";
});

const timedOut = runChildWithTimeout(
  process.execPath,
  ["-e", "setTimeout(() => {}, 30000);"],
  { cwd: process.cwd(), graceMs: 250 },
  100,
).then((timedOut) => {
  assert.equal(timedOut.status, null);
  assert.equal(timedOut.timedOut, true);
  assert.ok(["SIGTERM", "SIGKILL"].includes(timedOut.timeoutSignal));
  return "timedOut";
});

const descendant = runChildWithTimeout(
  process.execPath,
  ["-e", "const {spawn}=require('node:child_process'); const c=spawn(process.execPath,['-e','setTimeout(()=>{},30000)'],{stdio:['ignore','ignore','ignore']}); console.log(c.pid); setTimeout(()=>{},30000);"],
  { cwd: process.cwd(), graceMs: 250 },
  250,
).then((descendant) => {
  const descendantPid = Number(String(descendant.stdout || "").trim().split(/\s+/)[0]);
  assert.ok(descendantPid > 0);
  let descendantAlive = true;
  try { process.kill(descendantPid, 0); } catch { descendantAlive = false; }
  assert.equal(descendantAlive, false);
  return "descendant";
});

const outcomes = await Promise.all([completed, timedOut, descendant]);
assert.deepEqual(outcomes.sort(), ["completed", "descendant", "timedOut"]);
console.log(JSON.stringify({ cases: outcomes }));
