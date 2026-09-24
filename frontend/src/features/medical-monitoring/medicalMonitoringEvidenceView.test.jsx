import { renderToStaticMarkup } from "react-dom/server";
import { EvidenceView } from "./MedicalMonitoringWorkspace.jsx";

const baseRoute = { view: "evidence", snapshot_ref: "snap-1" };

function renderEvidence(sourceRefs, sourceLocatorRef, canonicalLocation = "") {
  const payload = {
    publicResultContext: true,
    projection: {
      sourceEvidence: {
        sourceLocatorRef,
        canonical_location: canonicalLocation,
        excerpt: "样本引文",
      },
    },
    source_refs: sourceRefs,
  };
  return renderToStaticMarkup(
    <EvidenceView payload={payload} route={baseRoute} onBack={() => {}} />
  );
}

export function testEvidenceNoLocatorNoFirstRefFallback() {
  // A23：目标locator在source_refs中无匹配（且evidence无canonical_location）
  // 时不得回退到第一条来源冒充定位成功。
  const html = renderEvidence(
    [
      { locator_ref: "loc-A", record_ref: "R-A", excerpt: "A来源" },
      { locator_ref: "loc-B", record_ref: "R-B", excerpt: "B来源" },
    ],
    "loc-missing",
  );
  const ok =
    html.includes("未能精确匹配目标来源定位") &&
    !html.includes("已完成来源一跳定位") &&
    !html.includes("R-A") && // 不得把第一条来源的记录号冒充本次定位
    !html.includes("A来源");
  if (!ok) throw new Error("A23: missing locator fell back to first source");
}

export function testEvidenceExactMatchStillBinds() {
  // 精确命中时仍正常绑定并显示已完成定位。
  const html = renderEvidence(
    [
      { locator_ref: "loc-A", record_ref: "R-A", excerpt: "A来源" },
      { locator_ref: "loc-B", record_ref: "R-B", excerpt: "B来源" },
    ],
    "loc-B",
  );
  const ok =
    html.includes("已完成来源一跳定位") &&
    html.includes("R-B") &&
    !html.includes("未能精确匹配");
  if (!ok) throw new Error("A23: exact match did not bind");
}

export function testEvidenceCanonicalLocationStandsAlone() {
  // evidence自带canonical_location（无source_refs匹配）时按自身定位展示，
  // 不视为失败也不借用他条来源。
  const html = renderEvidence(
    [{ locator_ref: "loc-A", record_ref: "R-A", excerpt: "A来源" }],
    "loc-other",
    "自定义定位说明",
  );
  const ok =
    html.includes("已完成来源一跳定位") &&
    html.includes("自定义定位说明") &&
    !html.includes("R-A");
  if (!ok) throw new Error("A23: canonical_location standalone broken");
}
