// R32-06 contract: the public result read effect in
// MedicalMonitoringProductLoop must keep stale-request aborts silent and
// auto-retry real failures with bounded backoff instead of rendering a
// terminal 「当前内容暂不可用」 panel that only a manual 「重新读取」 can
// clear (R32实测单轮5次暂不可用、其中一次滞留>5分钟，report_D.md发现#1).
// R36轮（R36-04）契约升级：自动重试承诺必须兑现且可观察——旧实现3次重试
// 在前17秒内全部烧完，面板却持续宣称「系统会自动重试（最多3次）」，D位
// 实测等待300秒零重试动作只能手动自救。现改为前3次递增退避+30秒节奏
// 至10次（约覆盖5分钟窗口），并把「正在第N/10次自动重试」实时渲染在
// 暂不可看面板上；预算用尽如实改为完成时表述。
// Same source-token style as medicalMonitoringContinuityIntegration.test.mjs.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

let passed = 0;
function check(condition, message) {
  assert.equal(Boolean(condition), true, message);
  passed += 1;
}

const here = path.dirname(fileURLToPath(import.meta.url));
const source = fs.readFileSync(
  path.join(here, "MedicalMonitoringProductLoop.jsx"),
  "utf8",
);
const compact = (text) => text.replace(/\s+/g, "");
const src = compact(source);
const needle = (text) => compact(text);

// --- the result read effect owns a bounded auto-retry loop ---
{
  check(
    src.includes(needle(`let retryTimer = null;\n    let failures = 0;`)),
    "result read effect declares retry state",
  );
  check(
    src.includes(needle(`if (cancelled || error?.name === "AbortError") return;\n        failures += 1;`)),
    "abort stays silent and only real failures count",
  );
  check(
    src.includes(needle(`const RESULT_READ_AUTO_RETRY_LIMIT = 10;`)),
    "auto-retry bound is a named module constant (10 attempts ≈ 5分钟窗口)",
  );
  check(
    src.includes(needle(`if (failures <= RESULT_READ_AUTO_RETRY_LIMIT) {\n          const backoff = monitoringRefreshBackoffMs(failures);`)),
    "auto-retry uses the shared escalating backoff up to the bound",
  );
  check(
    src.includes(needle(`setResultRetryAttempt(failures);`)),
    "each scheduled retry is observable via the attempt counter",
  );
  check(
    src.includes(needle(`} else {\n          // R36轮（R36-04）：重试预算用尽也要如实说`)),
    "exhausted retry budget switches the panel copy to a completed-tense statement",
  );
  check(
    src.includes(needle(`retryTimer = setTimeout(() => {\n            if (cancelled) return;\n            setResultLoading(true);\n            startRead();\n          }, backoff);`)),
    "auto-retry re-enters the same identity-scoped read",
  );
  check(
    src.includes(needle(`failures = 0;\n        setResultRetryAttempt(0);\n        setResultContext(projected);`)),
    "success resets the retry counter and the visible attempt state",
  );
  check(
    src.includes(needle(`setResultError(null);\n    setResultRetryAttempt(0);`)),
    "identity change / manual re-read resets the visible attempt state",
  );
  check(
    src.includes(needle(`cancelled = true;\n      controller.abort();\n      if (retryTimer) clearTimeout(retryTimer);`)),
    "cleanup aborts the read and clears the retry timer",
  );
}

// --- the unavailable panel is honest about the auto-retry ---
{
  check(
    src.includes(needle("系统会自动重试（最多${RESULT_READ_AUTO_RETRY_LIMIT}次，间隔递增、约每半分钟一次）")),
    "unavailable panel explains the auto-retry promise with the real bound",
  );
  check(
    src.includes(needle("正在第 ${resultRetryAttempt}/${RESULT_READ_AUTO_RETRY_LIMIT} 次自动重试…")),
    "unavailable panel shows the live retry attempt",
  );
  check(
    src.includes(needle("自动重试已用完（${RESULT_READ_AUTO_RETRY_LIMIT}次）")),
    "unavailable panel states budget exhaustion honestly",
  );
  check(
    src.includes(needle('onClick={retryPage}>重新读取')),
    "manual recovery entry stays available",
  );
}

// --- R37轮（R37-06）：自动重试承诺与调度事实一致 ---
// public_result_target_incomplete 是客户端在请求发出前确定性抛出的
// （路由缺定位参数），从不调度自动重试；旧实现照样渲染「首次自动重试
// 即将开始/正在第N次自动重试」，D位实测70秒零推进且文案回退。
// 契约：重试承诺句必须收敛到 resultRetryPromiseText，且该句对
// target_incomplete 给出如实陈述而非重试承诺。
{
  check(
    src.includes(needle(`const resultRetryPromiseText = resultError?.code === "public_result_target_incomplete"`)),
    "retry promise copy is centralized with a target_incomplete branch",
  );
  check(
    src.includes(needle(`此错误自动重试无法恢复，请点击「返回结果概览」。`)),
    "target_incomplete states honestly that auto-retry cannot recover",
  );
  check(
    src.includes('${resultRetryPromiseText}请点击「重新读取」或返回进度页。'),
    "unavailable panel renders the centralized retry promise copy",
  );
}

// --- R39轮（R39-02）：两条读取失败路径都必须真实调度退避重试 ---
// D位实测（report_D:37-41）：旅程页「暂不可用」等待90/35秒零自动重试，
// 文案停在「首次自动重试即将开始」；手动「重新读取」5-8秒恢复。
// ①投影校验失败分支（请求成功但kind=invalid）旧实现只设错误态不调度
//   重试——承诺与行为脱节的主场景；
// ②setup/history读取失败路径旧实现完全无重试调度。
// 契约：两条路径共用同一退避调度，面板文案对两条路径都如实显示进度。
{
  check(
    src.includes(needle(`const scheduleRetryAfterFailure = () => {`)),
    "result read failures share one backoff scheduler",
  );
  check(
    src.includes(needle(`failures += 1;\n          setResultLoading(false);\n          setResultError(projectMonitoringPublicResultError({ code: projected.code, message: projected.error }));\n          scheduleRetryAfterFailure();`)),
    "projection-invalid failures enter the same auto-retry schedule",
  );
  check(
    src.includes(needle(`setResultError(projectMonitoringPublicResultError(error));\n        scheduleRetryAfterFailure();`)),
    "network failures enter the same auto-retry schedule",
  );
  check(
    src.includes(needle(`if (code !== "run_data_not_ready") {\n        setupReadFailuresRef.current += 1;`)),
    "setup/history real failures schedule auto-retry (business-ready state excluded)",
  );
  check(
    src.includes(needle(`setRefreshEpoch((value) => value + 1);\n          }, monitoringRefreshBackoffMs(attempt));`)),
    "setup retry re-enters the same read with the shared backoff",
  );
  check(
    src.includes(needle(`const setupRetryPromiseText = `)),
    "setup/history failure panel renders its own live retry progress copy",
  );
  check(
    src.includes(needle(`setupRetryPromiseText}也可点击「重新读取」立即重试。`)),
    "setup/history unavailable panel states the retry promise honestly",
  );
  check(
    src.includes(needle(`setupReadFailuresRef.current = 0;\n    setSetupRetryAttempt(0);`)),
    "explicit refresh resets the setup retry budget",
  );
}

console.log(`medicalMonitoringResultReadRetry: ${passed} passed`);
