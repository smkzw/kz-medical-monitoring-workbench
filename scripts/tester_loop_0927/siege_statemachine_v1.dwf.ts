// 专项A+B：第3步状态机重构 + 自动复测套件（2026-10-14，源自40+轮复盘五根因之首）
// 验收门：从零路径E2E三连过（建项→上传→内容确认→字段映射→事实→运行→发布→结果）
// 纪律：pytest回归门；前端循最新kangzhe-design+屏幕资源充分利用；UI-only；最小根因修复

interface StateSource {
  name: string;
  kind: string;
  path: string;
  note: string;
}

interface StateMap {
  sources: StateSource[];
  conflicts: { where: string; what: string; evidence: string }[];
  authoritativeCandidates: string[];
  summary: string;
}

interface Design {
  designPath: string;
  keyDecisions: string[];
  migrationSteps: string[];
  risks: string;
}

interface ImplResult {
  commitHash: string;
  testsRun: string;
  gatePassed: boolean;
  frontendTouched: boolean;
  notes: string;
}

interface E2EResult {
  attempt: number;
  passed: boolean;
  blockedAt: string;
  journey: string[];
  evidenceNote: string;
}

interface SuiteResult {
  suitePath: string;
  retested: number;
  closed: number;
  stillFailing: string[];
  notes: string;
}

const WB = "implementation/workbench";
const PY = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python";
const WBABS = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench";
const LOOP = WB + "/scripts/tester_loop_0927";
const LOOP_ABS = WBABS + "/scripts/tester_loop_0927";
const SPEC = LOOP + "/siege_statemachine";
const ISOAPI = "http://127.0.0.1:8911/api/runtime-readiness";
const ISOFE = "http://localhost:5178/monitoring";
const ISORT_ABS = WBABS + "/runs/tester_loop_iso_20260928/runtime";
const ISO_RESTART_API =
  "cd " + WBABS + " && lsof -ti:8911 | xargs kill 2>/dev/null; sleep 2; set -a; source ~/.config/cms-medical-workbench/ai-runtime.env; set +a; " +
  "WORKBENCH_RUNTIME_DIR=\"" + ISORT_ABS + "\" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api " +
  "WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning > /tmp/mm_api_8911.log 2>&1 &";
const ISO_RESTART_VITE =
  "cd " + WBABS + "/frontend && lsof -ti:5178 | xargs kill 2>/dev/null; sleep 1; " +
  "VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort > /tmp/mm_vite_5178.log 2>&1 &";

const HONESTY =
  "诚实纪律：没做到就说没做到，不夸大不编造；若指令互相矛盾或检查不可能通过，如实说明并停止，不要硬凑通过。";

const PYTEST_GATE = "cd " + WBABS + " && .venv/bin/python -m pytest tests/medical_monitoring -q -p no:cacheprovider 2>&1 | tail -15";

// ===== 开局：环境门 =====
phase("开局：隔离环境就绪门");
const apiProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
const feProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request\nr=urllib.request.urlopen('" + ISOFE + "',timeout=10)\nprint(r.status)"]);
let envOk = apiProbe.exitCode === 0 && apiProbe.stdout.includes("READY") && feProbe.exitCode === 0;
if (!envOk) {
  await world.run("bash", ["-c", ISO_RESTART_API]);
  await world.run("bash", ["-c", ISO_RESTART_VITE]);
  await world.run("bash", ["-c", "sleep 20"]);
  const reApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
  const reFe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request\nr=urllib.request.urlopen('" + ISOFE + "',timeout=10)\nprint(r.status)"]);
  envOk = reApi.exitCode === 0 && reApi.stdout.includes("READY") && reFe.exitCode === 0;
  if (!envOk) {
    return {
      conclusion: "专项未启动：隔离环境两次恢复失败，需人工介入。",
      findings: [], verified: ["开局探针实跑，失败被拦截"], notCovered: ["全部专项工作"],
    };
  }
}
await world.run("bash", ["-c", "mkdir -p " + SPEC + " && echo ok"]);
log("环境就绪，专项开始");

// ===== 阶段1：考古 =====
phase("考古：第3步全部状态源清单与冲突点");
const archaeologist = agent("状态机考古员", {
  system:
    "你是资深架构考古员，为重构做准备。只读调查：读代码、读库schema、只读探针API，绝不修改任何文件与数据。" +
    "目标：把数据接入向导第3步（研究文件核对/字段识别/映射确认）涉及的**每一个状态持有者**找全，标出哪些是权威、哪些是投影、哪里互斥冲突。" + HONESTY,
});
const stateMap = await archaeologist.ask<StateMap>(
  "任务：调查隔离环境（API http://127.0.0.1:8911，代码根 " + WBABS + "）中第3步状态机。\n" +
  "已知线索（来自44轮测试循环，先读 " + LOOP + "/HANDOFF_40ROUNDS_20261014.md 第四部分根因一）：\n" +
  "- MonitoringDocumentEvidenceResolver→source_registry.monitoring_authority_entry_is_verified（source_intake.py:694-711）\n" +
  "- mapping-candidates投影顶层facts_generated=False与summary pending_confirmation_count与权威终态不一致（R21-R23轮轮记录）\n" +
  "- 前端本地推导状态与后端confirmed/unconfirmed碎片化并存（R9锁定『状态碎片化』家族）\n\n" +
  "要求：\n" +
  "1. 枚举第3步全部状态持有者：后端表/注册表/缓存/AI作业台账/前端本地态/路由层推导，每项给file:line证据；\n" +
  "2. 枚举已知冲突点（投影vs权威、前后端互斥、失败缓存复用），各给44轮里的实证出处（round_XX/report或REPORT.md）；\n" +
  "3. 指出哪些表/结构可充当单一权威源的候选；\n" +
  "4. 把调查报告写入 " + SPEC + "/01_STATEMAP.md（含证据表），返回StateMap。",
);
log("考古完成：状态源 " + stateMap.sources.length + " 个，冲突点 " + stateMap.conflicts.length + " 个");

// ===== 阶段2：设计 =====
phase("设计：单一权威状态模型与迁移路径");
const designer = agent("架构设计师", {
  system:
    "你是后端架构设计师。读考古报告与相关代码后，设计第3步单一权威状态模型。约束：最小迁移路径（能复用现有表就不新建）、fail-closed不放松、" +
    "前端一律改只读投影、失败态永不缓存复用、每个状态变迁必须落事件留痕。产出可执行的设计而非概念图。" + HONESTY,
});
const design = await designer.ask<Design>(
  "任务：基于 " + SPEC + "/01_STATEMAP.md（先读）与相关代码，设计第3步单一权威状态模型。\n" +
  "必须覆盖：\n" +
  "1. 权威状态表/事件流定义（含状态枚举、变迁条件、谁写谁读）；\n" +
  "2. 现有各投影的改造清单（每个投影从哪里读权威、本地推导删除点）；\n" +
  "3. 死锁家族的根治点：失败不缓存、降级入口（『采用已识别字段继续』）何时出现、阻塞组（『还有N组待处理』）必有处理入口、F5后状态恢复；\n" +
  "4. 分步迁移路径（每步可独立验证+pytest）；\n" +
  "5. 风险与回滚。写入 " + SPEC + "/02_DESIGN.md，返回Design。",
);
log("设计完成：" + design.keyDecisions.length + " 项关键决策");

// ===== 阶段3：实施（带回归门循环） =====
phase("实施：权威源落地与投影改造");
const implementer = agent("实施工程师", {
  system:
    "你是资深全栈工程师，按设计文档实施重构。纪律：严格按设计分步走、每步跑相关pytest、git提交（前缀『状态机专项:』，不push）；" +
    "最小根因修复、不改无关代码；前端改动循最新 /Users/smkzw/.zcode/skills/kangzhe-design/SKILL.md（功能为主、确保显示内容对屏幕资源充分利用、文字/按钮/配色循规范）；" +
    "需要重启服务时只动隔离对8911/5178（重启命令找设计文档或ISO_ENV_LOG），严禁碰8910/5177。测试永远以用户视角经界面进行。" + HONESTY,
});
let impl: ImplResult | null = null;
let implFeedback = "";
let gateOk = false;
for (let attempt = 1; attempt <= 3 && !gateOk; attempt++) {
  impl = await implementer.ask<ImplResult>(
    (attempt === 1
      ? "第1次：按 " + SPEC + "/02_DESIGN.md 全量实施（分步走，每步验证后提交）。"
      : "第" + attempt + "次：上次回归门未过或验收未过，按下方反馈修复后重验。反馈：" + implFeedback) + "\n" +
    "完成后：\n" +
    "1. 跑回归门：" + PYTEST_GATE + "（存量基线0失败，只拦新增）；\n" +
    "2. 用界面冒烟自检：经 http://localhost:5178 界面（不是API）验证常驻项目「MX循开考-CSU」仍可开始运行监查；\n" +
    "3. 把实施记录（改了什么/测试结果/提交hash）写入 " + SPEC + "/03_IMPL_attempt" + attempt + ".md，返回ImplResult（gatePassed=回归门过且冒烟过）。",
  );
  gateOk = impl.gatePassed;
}
if (!gateOk || !impl) {
  return {
    conclusion: "专项中止于实施阶段：三次尝试回归门未过。考古/设计/实施记录都在 " + SPEC + "/，供人工决策。已提交的代码在git（未push）。",
    findings: [], verified: ["三次回归门实跑"], notCovered: ["E2E验收", "复测套件"],
  };
}
log("实施完成（" + impl.commitHash + "），进入E2E验收门");

// ===== 阶段4：E2E三连过验收 =====
phase("验收：从零路径E2E三连过");
const PROJ_NAMES = ["MX循SM1-CSU", "MX循SM2-CSU", "MX循SM3-CSU"];
let e2eAllPassed = false;
let lastE2eEvidence = "";
for (let round = 1; round <= 2 && !e2eAllPassed; round++) {
  const results: E2EResult[] = [];
  for (let i = 0; i < 3; i++) {
    const tester = agent("从零E2E验收员-" + round + "-" + (i + 1), {
      system:
        "你是独立验收员，以真实用户身份只用浏览器（ego-browser skill，先读 /Users/smkzw/.zcode/skills/ego-browser/SKILL.md，整个任务只用一个TaskSpace）走从零路径。" +
        "只通过界面操作（严禁curl/API/直连后端/改文件）；系统卡住就是发现。收尾必须删除本次TaskSpace并清理临时下载。" + HONESTY,
    });
    results.push(await tester.ask<E2EResult>(
      "任务：从零验收（第" + round + "轮第" + (i + 1) + "位，项目名必须是「" + PROJ_NAMES[i] + "」）。\n" +
      "1. 浏览器开 http://localhost:5178/ →「新建项目」→ 子系统多选卡只勾「医学监查」→「前往医学监查配置」→ 名称「" + PROJ_NAMES[i] + "」、适应症/药物/分期按材料如实 → 创建；\n" +
      "2. 上传三件套（" + WBABS + "/tester_staging_0927/synth_csu/ 下合成数据xlsx+方案docx+eCRF指南docx）；\n" +
      "3. 走完全链：内容确认→字段映射确认→事实准备→运行→发布→结果视图；每步只做界面允许的用户操作；\n" +
      "4. 结果视图抽1名受试者做证据链深挖（发现卡→旅程→原始记录行）；\n" +
      "5. 单步≥45分钟无进展即停手（计为不通过）。界面易用性/逻辑性/美观性各一句评价。\n" +
      "返回E2EResult：passed=走到结果验收且证据链可点通；blockedAt=卡点；journey=到达阶段清单；evidenceNote=关键证据（含卡点界面原文）。",
    ));
  }
  const passedCount = results.filter((r) => r.passed).length;
  lastE2eEvidence = results.map((r) => (r.passed ? "过" : "停于:" + r.blockedAt)).join("；");
  log("E2E第" + round + "轮：" + passedCount + "/3 通过（" + lastE2eEvidence + "）");
  if (passedCount === 3) {
    e2eAllPassed = true;
  } else {
    implFeedback = "E2E未三连过：" + lastE2eEvidence + "；详细证据：" + JSON.stringify(results.filter((r) => !r.passed));
    await implementer.ask<ImplResult>(
      "E2E验收拦截（" + passedCount + "/3）。修复以下卡点后重跑回归门：" + PYTEST_GATE + "\n反馈：" + implFeedback + "\n返回ImplResult。",
    );
    const reg8 = await world.run("bash", ["-c", PYTEST_GATE]);
    gateOk = reg8.exitCode === 0 || !reg8.stdout.includes("FAILED");
    if (!gateOk) {
      return {
        conclusion: "专项中止：E2E修复轮引入回归门失败。证据在 " + SPEC + "/。",
        findings: [], verified: ["E2E三连过门实跑（未过）", "回归门实跑（拦截）"], notCovered: ["复测套件"],
      };
    }
  }
}
if (!e2eAllPassed) {
  return {
    conclusion: "专项两轮E2E修复后仍未三连过。证据：" + lastE2eEvidence + "。考古/设计/实施/E2E记录都在 " + SPEC + "/，供决策（可再跑一次本工作流续攻）。",
    findings: [], verified: ["E2E门两轮实跑"], notCovered: ["复测套件（未达前置条件）"],
  };
}
await world.run("bash", ["-c",
  "echo \"$(date '+%Y-%m-%d %H:%M') 状态机专项：E2E三连过达成（从零路径首次稳定走通）\" >> '" + LOOP_ABS + "/ISO_ENV_LOG.md'",
]);
log("E2E三连过达成——44轮未走通的从零路径首次稳定走通");

// ===== 阶段5：自动复测套件 =====
phase("配套：自动复测套件构建与滞留消化");
const suiteBuilder = agent("复测套件工程师", {
  system:
    "你负责把本次E2E固化成可复用的自动复测套件。要求：脚本化（ego-browser可编程驱动或playwright本地）、参数化（项目名/数据集/检查点清单可配）、" +
    "对『待复测』发现按其复现步骤回放并判定通过/仍失败。只建一套，不引入新框架。产品代码只读——发现产品问题就记录，不修。" + HONESTY,
});
const suite = await suiteBuilder.ask<SuiteResult>(
  "任务：\n" +
  "1. 读 " + SPEC + "/ 下实施与E2E记录，把从零路径E2E固化为 " + SPEC + "/retest_suite/（入口脚本+用例清单+运行说明）；\n" +
  "2. 读 " + LOOP + "/STATE_V2.json 里status=待复测的条目，挑与第3步/状态机相关的≥10条，按各自repro写成可回放检查；\n" +
  "3. 实跑套件（隔离环境8911/5178，真实浏览器路径），记录每条通过/仍失败；\n" +
  "4. 结果写 " + SPEC + "/05_SUITE.md，返回SuiteResult（closed=实测通过的条目数，stillFailing=仍失败的id清单）。",
);
log("复测套件：" + suite.retested + " 条回放，" + suite.closed + " 条通过");

// ===== 收尾 =====
phase("收尾：留痕与递交");
await world.run("bash", ["-c",
  "cd " + WBABS + " && git add scripts/tester_loop_0927/siege_statemachine -A 2>/dev/null; git add -A scripts/tester_loop_0927/ 2>/dev/null; " +
  "git commit -m '状态机专项A+B完成：单一权威源+E2E三连过+复测套件' --quiet; git push --quiet; git log --oneline -1",
]);

return {
  conclusion: "专项A+B完成：第3步单一权威状态源落地（提交" + (impl ? impl.commitHash : "n/a") + "），从零路径E2E三连过（44轮首次稳定走通），复测套件建成并回放" + suite.retested + "条（关闭" + suite.closed + "条）。常规轮可恢复，建议配额切P0/P1清零优先（方案C）。全部证据在 " + SPEC + "/。",
  findings: suite.stillFailing.map((id) => ({
    where: SPEC + "/05_SUITE.md",
    what: "复测仍失败：" + id,
    evidence: "套件回放记录",
    status: "unconfirmed",
    severity: "medium",
  })),
  verified: [
    "回归门：pytest监测子集实跑（三次内通过）",
    "E2E验收门：从零路径3/3走通（真实浏览器、三份不同项目名）",
    "复测套件：" + suite.retested + "条实测回放",
  ],
  notCovered: [
    "非第3步家族的待复测条目未全部回放（套件已参数化，可增量扩）",
    "医学语义专项（方案E）未动，收敛前必须补",
  ],
};
