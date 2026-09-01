import {
  CircleHelp,
  BookOpenText,
  ClipboardCheck,
  Hospital,
  Pill,
  ShieldAlert,
  Syringe,
  TestTube2,
  TrendingUp,
} from "lucide-react";
import { domainIconName } from "./domainIconCatalog.mjs";

const ICONS = Object.freeze({
  ShieldAlert,
  BookOpenText,
  Pill,
  Syringe,
  TestTube2,
  Hospital,
  TrendingUp,
  ClipboardCheck,
  CircleHelp,
});

const ICON_SIZES = Object.freeze({
  legend: 14,
  lane: 13,
  summary: 12,
  track: 10,
  row: 14,
  badge: 12,
});

/**
 * Unified lucide icon inside the existing shape/line encoding shell.
 * @param {{
 *   domain?: string;
 *   size?: keyof typeof ICON_SIZES;
 *   className?: string;
 *   title?: string;
 *   "aria-hidden"?: boolean | "true" | "false";
 * }} props
 */
export function DomainIcon({
  domain = "",
  size = "legend",
  className = "",
  title,
  "aria-hidden": ariaHidden = true,
}) {
  const Icon = ICONS[domainIconName(domain)] || CircleHelp;
  const iconSize = ICON_SIZES[size] || ICON_SIZES.legend;
  return (
    <span
      className={`monitoring-event-mark monitoring-domain-icon monitoring-domain-icon-${size} monitoring-domain-icon-${domain || "unknown"}${className ? ` ${className}` : ""}`}
      aria-hidden={ariaHidden}
      title={title}
    >
      <Icon size={iconSize} strokeWidth={2.25} aria-hidden="true" />
    </span>
  );
}

export default DomainIcon;
