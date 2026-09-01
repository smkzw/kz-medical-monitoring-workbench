// R7 Slice-08C-2/08C-3 product-loop integration contract (contract §6.4 and
// §7.4): the continuity read lives in MedicalMonitoringProductLoop and is a
// React effect, so without a DOM renderer the deterministic contract checks
// read the shipped component source and assert the exact control flow: guard,
// AbortController + cancelled flag + cleanup abort, stale-response guards,
// identity-scoped effect dependencies, board gate excluding continuity state
// (error non-blocking), error degrade text, panel placement + re-mount key,
// same-identity journey/source routing, the 08C-3 subject-view full-identity
// read gate (site/subject/spine/axis window next to project and result
// context), cancel + stale-clear on subject/spine/window/view switches, and
// the continuity props plumbed into SubjectWorkspaceView beside the
// drawer-close route patch. Whitespace is normalized so the assertions are
// token-sequence pins, not formatting pins.
//
// Contract sources:
// - context/medical_monitoring_r7_slice08c2_frontend_vertical_contract_20260829.md §2.3/§2.4/§2.5/§5/§6.4
// - context/medical_monitoring_r7_slice08c3_journey_changes_drawer_contract_20260829.md §3/§5.1/§7.4
// - reviews/medical_monitoring_r7_slice08c_chinese_continuity_visual_contract_v0_2_20260829.md (v0.2 wins)

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
const source = fs.readFileSync(path.join(here, "MedicalMonitoringProductLoop.jsx"), "utf8");
const compact = (text) => text.replace(/\s+/g, "");
const src = compact(source);
const needle = (text) => compact(text);

// --- imports: the continuity surface is wired into the loop ---
{
  check(
    src.includes(needle(`import {\n  projectR7ContinuityError,\n  safeVerifyR7ContinuityEnvelope,\n} from "./medicalMonitoringContinuityProjection.mjs";`)),
    "loop imports the continuity error projection and strict verifier",
  );
  check(
    src.includes(needle(`import {\n  r7ContinuityRowJourneyTarget,\n  r7ContinuityRowSourceTarget,\n} from "./medicalMonitoringContinuityFilter.mjs";`)),
    "loop imports the same-identity routing gates",
  );
  check(
    src.includes(needle(`import { MedicalMonitoringContinuityPanel } from "./MedicalMonitoringContinuityPanel.jsx";`)),
    "loop imports the continuity panel",
  );
  passed += 3;
}

// --- state: declared beside the result state, never part of the board gate ---
{
  check(
    src.includes(needle(`// Slice-08C-2 continuity read: never blocks the existing result boards.`)),
    "continuity state declares the non-blocking intent",
  );
  check(src.includes(needle(`const [continuityResult, setContinuityResult] = useState(null);`)), "continuity result state declared");
  check(src.includes(needle(`const [continuityLoading, setContinuityLoading] = useState(false);`)), "continuity loading state declared");
  check(
    src.includes(needle(`const loadingBody = setupHistoryLoading || resultLoading || entryLoading;`)),
    "loadingBody excludes continuityLoading",
  );
  check(
    src.includes(needle(`const unavailableText = resultError?.text || setupHistoryError?.text || "本次结果暂不可查看，请返回进度页";`)),
    "page unavailable text excludes continuity errors",
  );
  check(
    src.includes(needle(`const productStatus = resultError || setupHistoryError ? "unavailable" : loadingBody ? "loading" : productState.kind;`)),
    "page status derivation excludes continuity state",
  );
  check(
    src.includes(needle(`{!loadingBody && !resultError && !setupHistoryError && resultLoaded ? (`)),
    "board render gate is project/result-scoped only",
  );
  passed += 7;
}

// --- continuity effect: extracted block, exact control flow ---
{
  const startMarker = needle(`// Slice-08C-2/08C-3: project/site and subject continuity reads.`);
  const endMarker = needle(`}, [api, normalizedProjectId, resultToken, route.site_ref, route.subject_ref, route.spine_ref, route.window_start, route.window_end, routeView]);`);
  const startIndex = src.indexOf(startMarker);
  const endIndex = src.indexOf(endMarker, startIndex + startMarker.length);
  check(startIndex !== -1 && endIndex !== -1, "continuity effect block is present in the loop");
  const effect = src.slice(startIndex, endIndex + endMarker.length);

  check(
    effect.includes(needle(`const subjectViewIdentityReady = PRODUCT_RESULT_SUBJECT_VIEWS.has(routeView)\n      && Boolean(route.site_ref && route.subject_ref && route.spine_ref && route.window_start && route.window_end);`)),
    "subject views read only with the full public identity (site+subject+spine+axis window)",
  );
  check(
    effect.includes(needle(`if (!normalizedProjectId || !resultToken || ((routeView !== "overview" && routeView !== "site_overview") && !subjectViewIdentityReady)) {`)),
    "effect guard runs on project/center dashboards and full-identity subject views with a result context",
  );
  check(
    effect.includes(needle(`setContinuityResult(null);\n      setContinuityLoading(false);\n      return undefined;`)),
    "guard clears continuity state and skips the fetch off-dashboard",
  );
  check(effect.includes("constcontroller=newAbortController();"), "effect creates a fresh AbortController per run");
  check(effect.includes("letcancelled=false;"), "effect owns a per-run cancelled flag");
  check(
    effect.includes(needle(`api.getResultContinuity(normalizedProjectId, resultToken, {\n      siteRef: route.site_ref,\n      signal: controller.signal,\n    })`)),
    "fetch passes the project/result identity, optional site_ref and the abort signal",
  );
  check(
    (effect.match(/if\(cancelled\)return;/g) || []).length === 2,
    "both then-branches (before and after verification) refuse stale writes",
  );
  check(
    effect.includes(needle(`const expected = { projectId: normalizedProjectId, resultContextToken: resultToken };`)),
    "verification binds the expected project and result context",
  );
  check(
    effect.includes(needle(`if (route.site_ref) expected.siteRef = route.site_ref;`)),
    "site-scoped responses must match the active center identity",
  );
  check(effect.includes("safeVerifyR7ContinuityEnvelope(payload,expected);"), "payload passes the strict digest+identity verifier");
  check(
    effect.includes(needle(`if (cancelled || error?.name === "AbortError") return;`)),
    "catch ignores aborted requests instead of projecting errors",
  );
  check(effect.includes("setContinuityResult(projectR7ContinuityError(error));"), "real failures degrade through the frozen unavailable error");
  check(effect.includes("return()=>{cancelled=true;controller.abort();};"), "cleanup cancels the flag and aborts the in-flight request");
  check(
    effect.includes(needle(`}, [api, normalizedProjectId, resultToken, route.site_ref, route.subject_ref, route.spine_ref, route.window_start, route.window_end, routeView]);`)),
    "effect identity deps cover project, result context, site, subject, spine, axis window and view",
  );
  check(
    (effect.match(/newAbortController\(\)/g) || []).length === 1 && (effect.match(/controller\.abort\(\)/g) || []).length === 1,
    "exactly one controller and one abort per effect run",
  );
  passed += 14;
}

// --- panel wiring: error degrades to the unavailable placeholder, boards stay ---
{
  check(src.includes("MedicalMonitoringContinuityPanel"), "panel is rendered by the loop");
  check(
    src.includes(needle(`continuity={continuityResult?.ok ? continuityResult.value : null}`)),
    "panel receives the verified value only",
  );
  check(
    src.includes(needle(`unavailable={continuityUnavailableText}`)),
    "panel receives the degrade text on verification/request failure",
  );
  check(src.includes(needle(`loading={continuityLoading}`)), "panel receives the loading flag");
  check(
    src.includes("routeView===\"overview\"") && src.includes("site_overview"),
    "panel renders only on the project/center dashboards",
  );
  check(
    src.includes(needle(`key={\`\${resultToken}:\${route.site_ref || ""}\`}`)),
    "panel key remounts on result-context/site switch so filters reset",
  );
  check(
    (src.match(/MedicalMonitoringContinuityPanel/g) || []).length >= 3,
    "continuity panel remains wired (import + tamper-lead + comparable-follow)",
  );
  check(
    src.lastIndexOf("MedicalMonitoringContinuityPanel") > src.indexOf(needle(`{currentResultView}`)),
    "result boards (incl. four-stage flow) sit before continuity so the first screen shows the flow",
  );
  passed += 8;
}

// --- 08C-3 subject-view wiring: verified continuity props reach the journey ---
{
  const subjectViewIndex = src.indexOf("continuityResult={continuityResult}");
  check(subjectViewIndex !== -1, "SubjectWorkspaceView receives the continuity result on subject views");
  const subjectViewWindow = src.slice(Math.max(0, subjectViewIndex - 500), subjectViewIndex + 700);
  check(
    subjectViewWindow.includes(needle(`continuityUnavailable={continuityUnavailableText}`)),
    "SubjectWorkspaceView receives the degrade text on verification/request failure",
  );
  check(
    subjectViewWindow.includes(needle(`continuityLoading={continuityLoading}`)),
    "SubjectWorkspaceView receives the loading flag",
  );
  check(
    subjectViewWindow.includes(needle(`onDrawerClose={() => onRouteChange?.(r7JourneyDrawerClosePatch(route))}`)),
    "subject-view drawer close applies the route-close patch that keeps journey identity",
  );
  check(
    subjectViewWindow.includes(needle(`onJourneyRowSelect={selectResultContinuityRow}`)),
    "subject-view drawer switches continuity rows through the identity-preserving route callback",
  );
  check(
    src.includes(needle(`import { r7JourneyDrawerClosePatch } from "./medicalMonitoringJourneyChanges.mjs";`)),
    "loop imports the drawer close patch",
  );
  check(
    src.includes(needle(`onDrawerClose={() => onRouteChange?.(r7JourneyDrawerClosePatch(route))}`)),
    "the subject workspace never gets an empty close handler",
  );
  check(
    src.includes(needle(`const selectResultContinuityRow = useCallback((row) => {`)),
    "continuity row switching is implemented as a ProductLoop route callback",
  );
  passed += 8;
}

// --- same-identity routing: gates refuse empty jumps, reuse public routes ---
{
  check(
    src.includes(needle(`const selectContinuityJourney = useCallback((row) => {\n    const target = r7ContinuityRowJourneyTarget(row, resultPayload);\n    if (!target) return;\n    navigate("journey", target);\n  }, [navigate, resultPayload]);`)),
    "journey click re-runs the gate and refuses a null target",
  );
  check(
    src.includes(needle(`const selectContinuitySource = useCallback((row) => {\n    const target = r7ContinuityRowSourceTarget(row);\n    if (!target) return;\n    navigate("evidence", target);\n  }, [navigate]);`)),
    "source click re-runs the gate and refuses a null target",
  );
  passed += 2;
}

// --- same-identity contract cross-check against the pure gates ---
{
  const { r7ContinuityRowJourneyTarget, r7ContinuityRowSourceTarget } = await import("./medicalMonitoringContinuityFilter.mjs");
  const riskRow = {
    object_type: "risk",
    subject_ref: "S/01",
    site_ref: "site/01",
    window_start: "2026-01-01",
    window_end: "2026-03-31",
    risk_instance_ref: "r-i-1",
    risk_anchor_ref: "r-a-1",
    event_ref: "e-1",
    source_locator_ref: "s-1",
  };
  const target = r7ContinuityRowJourneyTarget(riskRow, {
    projection: {
      subjects: [{ subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01" }],
      subjectFlow: {
        availability: "available",
        reconciliation: { state: "matched" },
        subjects: [{ subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01", journey_jump_enabled: true, jump_window_start: "2025-12-01", jump_window_end: "2026-04-30" }],
      },
    },
  });
  check(
    target && target.subject_ref === "S/01" && target.site_ref === "site/01" && target.spine_ref === "spine/01",
    "journey target carries the same identity the route will consume",
  );
  check(
    r7ContinuityRowJourneyTarget({ ...riskRow, subject_ref: "S/99" }, { projection: { subjects: [{ subject_ref: "S/01", site_ref: "site/01", spine_ref: "spine/01" }], subjectFlow: { availability: "available", reconciliation: { state: "matched" }, subjects: [] } } }) === null,
    "cross-identity rows never reach the journey route",
  );
  check(
    r7ContinuityRowSourceTarget(riskRow) && r7ContinuityRowSourceTarget(riskRow).risk_instance_ref === "r-i-1",
    "source target reuses the existing evidence route identity",
  );
  check(r7ContinuityRowSourceTarget({ ...riskRow, source_locator_ref: "" }) === null, "empty source rows never jump",
  );
  passed += 4;
}

console.log(`medicalMonitoringContinuityIntegration: ${passed} passed`);
