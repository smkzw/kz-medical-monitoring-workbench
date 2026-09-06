"""Verify model citations against durable reads, without semantic arbitration."""
from packages.medical_monitoring.intelligence.primitives import canonical_json, content_hash


def verified_tool_evidence(evidence, reads, allowed_sources):
    result = {}
    for item in evidence:
        if item["locator"].startswith(("profile://", "field-profile://")):
            continue  # Rebuilt from deterministic field statistics by the caller.
        pair = (item["source_entry_id"], item["source_content_sha256"])
        if pair not in allowed_sources:
            raise ValueError("tool citation source is not bound")
        matched = None
        verified_value = None
        for read in reads:
            receipt = read["receipt"]
            source = receipt["result"]
            if source.get("status") == "unavailable":
                continue
            source_id = source.get("source_entry_id", source.get("source_revision_id"))
            digest = source.get("source_content_sha256", source.get("content_sha256"))
            units = list(source.get("units", ())) + list(source.get("excerpts", ()))
            if (source_id, digest) == pair:
                for unit in units:
                    if unit.get("locator") != item["locator"]:
                        continue
                    quote = item.get("quote", "")
                    if quote.strip() and quote in unit.get("text", ""):
                        matched = receipt
                        break
                    raw = item.get("raw_fields") or {}
                    for cell in unit.get("cells", ()):
                        if ("raw_value" in raw and raw.get("coordinate") == cell.get("coordinate")
                                and canonical_json(raw["raw_value"]) == canonical_json(cell.get("value"))):
                            matched, verified_value = receipt, {"coordinate": cell["coordinate"], "raw_value": cell["value"]}
                            break
            # Listing cell locators carry the frozen file digest themselves.
            for cell in source.get("data", {}).get("cells", ()):
                raw = item.get("raw_fields") or {}
                if ((source_id, cell.get("source_file_digest")) == pair
                        and item["locator"] in {cell.get("locator_id"), "source-cell://" + str(cell.get("locator_id"))}
                        and "raw_value" in raw
                        and canonical_json(raw["raw_value"]) == canonical_json(cell.get("raw_value"))):
                    matched, verified_value = receipt, {"locator_id": cell["locator_id"], "raw_value": cell["raw_value"]}
                    break
            if matched is not None:
                break
        if matched is None:
            raise ValueError("tool citation must match a read locator and exact quote or raw value")
        raw = {"evidence_tool_receipt_sha256": content_hash(matched),
               "coverage": matched["result"].get("coverage", matched["result"].get("data", {}).get("coverage", "partial")),
               **(verified_value or {})}
        if item["evidence_id"] in result:
            raise ValueError("tool citation evidence IDs must be unique")
        result[item["evidence_id"]] = {**item, "quote": item.get("quote", "") if verified_value is None else "", "raw_fields": raw}
    return result
