// R32-06 contract: the public result read effect in
// MedicalMonitoringProductLoop must keep stale-request aborts silent and
// auto-retry real failures with bounded backoff instead of rendering a
// terminal 「当前内容暂不可用」 panel that only a manual 「重新读取」 can
// clear (R32实测单轮5次暂不可用、其中一次滞留>5分钟，report_D.md发现#1).
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
    src.includes(needle(`if (failures <= 3) {\n          const backoff = monitoringRefreshBackoffMs(failures);`)),
    "auto-retry is bounded to 3 attempts with shared backoff",
  );
  check(
    src.includes(needle(`retryTimer = setTimeout(() => {\n            if (cancelled) return;\n            setResultLoading(true);\n            startRead();\n          }, backoff);`)),
    "auto-retry re-enters the same identity-scoped read",
  );
  check(
    src.includes(needle(`failures = 0;\n        setResultContext(projected);`)),
    "success resets the retry counter",
  );
  check(
    src.includes(needle(`cancelled = true;\n      controller.abort();\n      if (retryTimer) clearTimeout(retryTimer);`)),
    "cleanup aborts the read and clears the retry timer",
  );
}

// --- the unavailable panel is honest about the auto-retry ---
{
  check(
    src.includes(needle("系统会自动重试（最多3次，间隔递增）；若持续失败请点击「重新读取」或返回进度页。")),
    "unavailable panel explains the auto-retry",
  );
  check(
    src.includes(needle('onClick={retryPage}>重新读取')),
    "manual recovery entry stays available",
  );
}

console.log(`medicalMonitoringResultReadRetry: ${passed} passed`);
