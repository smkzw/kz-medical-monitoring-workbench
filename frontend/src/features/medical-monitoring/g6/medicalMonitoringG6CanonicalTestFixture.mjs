import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

function findCanonicalSourceRoot() {
  const candidates = [
    path.resolve(process.cwd(), "deploy", "medical_monitoring_local"),
    path.resolve(process.cwd(), "..", "deploy", "medical_monitoring_local"),
  ];
  const sourceRoot = candidates.find((candidate) => fs.existsSync(path.join(candidate, "synthetic_ego.py")));
  if (!sourceRoot) {
    throw new Error("canonical_g6_source_root_not_found");
  }
  return sourceRoot;
}

const canonicalSourceRoot = findCanonicalSourceRoot();
const repoRoot = path.resolve(canonicalSourceRoot, "..", "..");
const PYTHON_SCRIPT = [
  "import json",
  "import synthetic_ego",
  "print(json.dumps(synthetic_ego.build_synthetic_audience_bundle(), ensure_ascii=False))",
].join("; ");

let cachedBundle = null;

export function loadCanonicalG6BundleForTest() {
  if (cachedBundle) return JSON.parse(JSON.stringify(cachedBundle));
  const result = spawnSync("python3", ["-c", PYTHON_SCRIPT], {
    cwd: repoRoot,
    env: { ...process.env, PYTHONPATH: canonicalSourceRoot },
    encoding: "utf8",
  });
  if (result.error || result.status !== 0) {
    const detail = result.error?.message || String(result.stderr || "python3 failed").trim();
    throw new Error(`canonical_g6_bundle_generation_failed:${detail}`);
  }
  try {
    cachedBundle = JSON.parse(result.stdout);
  } catch (error) {
    throw new Error(`canonical_g6_bundle_parse_failed:${error.message}`);
  }
  return JSON.parse(JSON.stringify(cachedBundle));
}
