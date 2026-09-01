/** @typedef {"ae"|"mh"|"cm"|"ip"|"lab_exam"|"hospital_procedure"|"symptom_efficacy"|"protocol_compliance"} MedicalDomainKey */

/** @type {Readonly<Record<MedicalDomainKey, string>>} */
export const DOMAIN_ICON_NAMES = Object.freeze({
  ae: "ShieldAlert",
  mh: "BookOpenText",
  cm: "Pill",
  ip: "Syringe",
  lab_exam: "TestTube2",
  hospital_procedure: "Hospital",
  symptom_efficacy: "TrendingUp",
  protocol_compliance: "ClipboardCheck",
});

/** @type {Readonly<MedicalDomainKey[]>} */
export const MEDICAL_DOMAIN_KEYS = Object.freeze(Object.keys(DOMAIN_ICON_NAMES));

/**
 * @param {string | null | undefined} domain
 * @returns {string}
 */
export function domainIconName(domain) {
  return DOMAIN_ICON_NAMES[/** @type {MedicalDomainKey} */ (domain)] || "CircleHelp";
}

/**
 * @param {string | null | undefined} domain
 * @returns {boolean}
 */
export function isKnownMedicalDomain(domain) {
  return Boolean(domain && Object.prototype.hasOwnProperty.call(DOMAIN_ICON_NAMES, domain));
}
