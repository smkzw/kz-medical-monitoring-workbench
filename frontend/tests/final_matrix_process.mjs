// Process helpers for the disposable final-matrix harness.
// These helpers deliberately operate only on a child process group created by
// the harness; they are not used by the product runtime.
import { spawn } from "node:child_process";

export function terminateProcessGroup(pid, signal = "SIGTERM") {
  if (!pid) return false;
  try {
    if (process.platform === "win32") return process.kill(pid, signal);
    return process.kill(-pid, signal);
  } catch (error) {
    // ESRCH means the group has already exited. Other errors are still
    // fail-closed for cleanup: callers must not widen the target set.
    if (error?.code !== "ESRCH") return false;
    return false;
  }
}

/**
 * Run a disposable child in its own process group with an explicit wall-clock
 * ceiling. On timeout, terminate the group (TERM, then KILL after the grace
 * window) so nested uvicorn/Vite/Chrome processes cannot survive a child-only
 * timeout. The returned shape preserves spawnSync's status/signal fields and
 * adds auditable timeout metadata.
 *
 * E1修复（第2轮门）：SIGKILL之后进程组的死亡是异步的——直接子进程close
 * （或被收养）不等于组成员全部消失；此前立即resolve，调用方会看到"已超时
 * 杀死"却仍能以kill(pid,0)探活到残留组成员（负载下偶发假阳性）。现在对
 * 进程组做有界liveness轮询：整组ESRCH后才交付结果；到达上限仍存活则照常
 * 交付（保留"绝不无限等待坏子进程"的既有契约）。返回对象shape不变。
 */
export function runChildWithTimeout(command, args, options = {}, timeoutMs = 420000) {
  const { graceMs = 5000, ...spawnOptions } = options;
  const child = spawn(command, args, {
    ...spawnOptions,
    detached: true,
    stdio: ["ignore", "pipe", "pipe"],
  });
  const stdout = [];
  const stderr = [];
  child.stdout?.on("data", (chunk) => stdout.push(chunk.toString()));
  child.stderr?.on("data", (chunk) => stderr.push(chunk.toString()));

  return new Promise((resolve) => {
    let settled = false;
    let timedOut = false;
    let timeoutSignal = null;
    let closeResult = null;
    let forceCompleted = false;
    let timeoutTimer = null;
    let forceTimer = null;
    let finalTimer = null;
    let drainTimer = null;

    const groupHasLiveMembers = () => {
      if (!child.pid) return false;
      try {
        process.kill(-child.pid, 0);
        return true;
      } catch (error) {
        // ESRCH=整组（含被收养的残留成员）已不存在——可安全交付。
        return error?.code !== "ESRCH";
      }
    };

    const complete = (result) => {
      if (settled) return;
      if (timedOut && timeoutSignal === "SIGKILL") {
        // SIGKILL已发（无论直接子进程close是否先到）：等整组ESRCH
        // （有界），再交付。forceTimer随后仍会发SIGKILL并重入本路径，
        // settled守卫保证只交付一次。
        const deadline = Date.now() + 2000;
        const drain = () => {
          if (settled) return;
          if (!groupHasLiveMembers() || Date.now() >= deadline) {
            settled = true;
            if (timeoutTimer) clearTimeout(timeoutTimer);
            if (forceTimer) clearTimeout(forceTimer);
            if (finalTimer) clearTimeout(finalTimer);
            if (drainTimer) clearTimeout(drainTimer);
            resolve({
              ...result,
              stdout: stdout.join(""),
              stderr: stderr.join(""),
              timedOut,
              timeoutSignal,
              pid: child.pid ?? null,
            });
            return;
          }
          drainTimer = setTimeout(drain, 20);
        };
        drain();
        return;
      }
      settled = true;
      if (timeoutTimer) clearTimeout(timeoutTimer);
      if (forceTimer) clearTimeout(forceTimer);
      if (finalTimer) clearTimeout(finalTimer);
      if (drainTimer) clearTimeout(drainTimer);
      resolve({
        ...result,
        stdout: stdout.join(""),
        stderr: stderr.join(""),
        timedOut,
        timeoutSignal,
        pid: child.pid ?? null,
      });
    };

    const onClose = (status, signal) => {
      const result = { status, signal };
      if (!timedOut || forceCompleted) complete(result);
      else closeResult = result;
    };

    child.once("error", (error) => {
      // An error before a close event is terminal for this disposable child.
      onClose(null, error?.code || error?.name || "error");
    });
    child.once("close", onClose);

    timeoutTimer = setTimeout(() => {
      if (settled) return;
      timedOut = true;
      timeoutSignal = "SIGTERM";
      terminateProcessGroup(child.pid, "SIGTERM");
      forceTimer = setTimeout(() => {
        if (settled) return;
        timeoutSignal = "SIGKILL";
        terminateProcessGroup(child.pid, "SIGKILL");
        forceCompleted = true;
        if (closeResult) {
          complete(closeResult);
        } else {
          // Give the OS a short opportunity to deliver SIGKILL, but never
          // leave the controller waiting indefinitely for a broken child.
          finalTimer = setTimeout(() => complete({ status: null, signal: "SIGKILL" }), 250);
        }
      }, Math.max(250, Number(graceMs) || 5000));
    }, Math.max(1, Number(timeoutMs) || 420000));
  });
}
