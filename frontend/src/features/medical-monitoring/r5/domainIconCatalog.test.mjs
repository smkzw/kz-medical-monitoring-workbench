import assert from "node:assert/strict";
import test from "node:test";
import {
  DOMAIN_ICON_NAMES,
  MEDICAL_DOMAIN_KEYS,
  domainIconName,
  isKnownMedicalDomain,
} from "./domainIconCatalog.mjs";

test("maps all eight medical domains to distinct lucide icon names", () => {
  assert.equal(MEDICAL_DOMAIN_KEYS.length, 8);
  const iconNames = MEDICAL_DOMAIN_KEYS.map((domain) => domainIconName(domain));
  assert.equal(new Set(iconNames).size, 8, "each domain should have a unique icon");
});

test("preserves canonical domain-to-icon mapping", () => {
  assert.deepEqual(DOMAIN_ICON_NAMES, {
    ae: "ShieldAlert",
    mh: "BookOpenText",
    cm: "Pill",
    ip: "Syringe",
    lab_exam: "TestTube2",
    hospital_procedure: "Hospital",
    symptom_efficacy: "TrendingUp",
    protocol_compliance: "ClipboardCheck",
  });
});

test("falls back for unknown domains without throwing", () => {
  assert.equal(domainIconName("unknown_domain"), "CircleHelp");
  assert.equal(isKnownMedicalDomain("ae"), true);
  assert.equal(isKnownMedicalDomain("not-a-domain"), false);
});
