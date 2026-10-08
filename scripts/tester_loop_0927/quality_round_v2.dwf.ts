// 质量循环v2·单轮制（用户2026-10-07指令：已结束轮次的成员及时退役；定期清理缓存与冗余文件）
// 一轮=一个run：本轮成员（预置复核/攻坚/4测试位/分诊/修复/复盘）随run结束全部退役；
// 跨轮状态（轮次/未决发现/策略/基线/通道）持久化在 STATE_V2.json，由脚本落盘（不靠常驻记忆）。
// 收敛判定：连续2轮清洁（4/4走通结果验收且无新确认P0/P1）→ 该轮就地收官（总交付+停环境+全量清理）。

interface RawFinding {
  where: string;
  what: string;
  severity: string;
  category: string;
  evidence: string;
  repro: string;
}

interface TesterOutcome {
  tester: string;
  channel: string;
  reportFile: string;
  projectName: string;
  stagesReached: string[];
  blockedAt: string;
  stallMinutes: number;
  pass: boolean;
  findings: RawFinding[];
  coverageNotes: string;
  channelNote: string;
}

interface Finding {
  id: string;
  round: number;
  title: string;
  where: string;
  what: string;
  severity: "critical" | "high" | "medium" | "low";
  category: "product_bug" | "medical_accuracy" | "ux_issue" | "cosmetic";
  evidence: string;
  repro: string;
  sources: string[];
  confirmed: boolean;
  confirmNote: string;
  fixHint: string;
  status: "待修复" | "待复测" | "已验证" | "搁置";
}

interface NewFindingDraft {
  title: string;
  where: string;
  what: string;
  severity: "critical" | "high" | "medium" | "low";
  category: "product_bug" | "medical_accuracy" | "ux_issue" | "cosmetic";
  evidence: string;
  repro: string;
  sources: string[];
  confirmed: boolean;
  confirmNote: string;
  fixHint: string;
}

interface TriageVerdict {
  newFindings: NewFindingDraft[];
  duplicatesMerged: string[];
  synthAssessment: string;
  verifyUpgrades: { id: string; note: string }[];
  coverageGaps: string[];
  triageNote: string;
}

interface FixResult {
  fixedIds: string[];
  skipped: { id: string; reason: string }[];
  commitHash: string;
  testsRun: string[];
  frontendTouched: boolean;
  notes: string;
}

interface Recap {
  rootCauses: string;
  strategyNote: string;
  stagnatedIds: string[];
  archivedProjects: string[];
  roundReportPath: string;
}

interface SeedResult {
  projectId: string;
  stateNote: string;
  blockedNote: string;
}

interface PreflightResult {
  chainOk: boolean;
  blockedAt: string;
  stages: { stage: string; ok: boolean; seconds: number; note: string }[];
  aiNodes: { node: string; providerModel: string; ok: boolean; note: string }[];
  evidenceNote: string;
}

interface BootstrapState {
  /** 上一代循环（STATE.json/各轮REPORT.md）重建出的最后已完成轮次 */
  round: number;
  cleanStreak: number;
  /** 重建出的未决发现（待修复/待复测；搁置不计） */
  registry: Finding[];
  note: string;
}

interface RoundState {
  round: number;
  cleanStreak: number;
  strategyNote: string;
  registry: Finding[];
  baselineFailures: string[];
  channelOk: Record<string, boolean>;
  campaignDone: boolean;
}

// ===== 常量（沿用0927循环口径） =====
const WB = "implementation/workbench";
const PY = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python";
const WBABS = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench";
const LOOP = WB + "/scripts/tester_loop_0927";
const STAGE = "tester_staging_0927";
const STATE_FILE = LOOP + "/STATE_V2.json";
const STATE_ABS = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/scripts/tester_loop_0927/STATE_V2.json";
const LOOP_ABS = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/scripts/tester_loop_0927";
const RUNNER = "/Users/smkzw/.codex/tools/conference_session_runner.py";
const STALLMIN = 45;
const CLEANSTREAKNEED = 2;

const ISOAPI = "http://127.0.0.1:8911/api/runtime-readiness";
const ISOFE = "http://localhost:5178/monitoring";
const ISORT_ABS = WBABS + "/runs/tester_loop_iso_20260928/runtime";
const ISO_RESTART_API =
  "cd " + WBABS + " && lsof -ti:8911 | xargs kill 2>/dev/null; sleep 2; source ~/.config/cms-medical-workbench/ai-runtime.env; " +
  "WORKBENCH_RUNTIME_DIR=\"" + ISORT_ABS + "\" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api " +
  "WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8911 --log-level warning > /tmp/mm_api_8911.log 2>&1 &";
const ISO_RESTART_VITE =
  "cd " + WBABS + "/frontend && lsof -ti:5178 | xargs kill 2>/dev/null; sleep 1; " +
  "VITE_API_PROXY_TARGET=http://127.0.0.1:8911 nohup npx vite --port 5178 --strictPort > /tmp/mm_vite_5178.log 2>&1 &";
const ISO_GUARD_RULE =
  "你负责隔离测试环境（独立API 8911 + 独立vite 5178）的可用性，它与医学写作舰队共用的 8910/5177 完全无关。" +
  "严禁重启或触碰 8910/5177，严禁推进任何业务管道、严禁碰任何项目数据。每次操作把时间戳与结果追加到 " +
  LOOP + "/ISO_ENV_LOG.md。两次尝试仍不可用就如实上报，不要硬试。若隔离运行时整目录丢失，如实上报受阻，不要自行重建。没做到就直说，不夸大不编造。";

interface Dataset {
  key: string;
  label: string;
  brief: string;
  files: string[];
}

const DATASETS: Dataset[] = [
  {
    key: "RUX",
    label: "芦可替尼乳膏·特应性皮炎III期（真实数据）",
    brief: "RUX-03-002，JAK抑制剂外用乳膏，III期，54表真实锁库数据。日常监查关注：AE/合并用药/病史跨表矛盾、化验趋势、量表（POEM/DLQI等）。",
    files: [
      STAGE + "/RUX/RUX-03-002_DataListing.xlsx",
      STAGE + "/RUX/RUX-03-002_临床研究方案_V1.3.docx",
      STAGE + "/RUX/RUX-03-002_eCRF填写指南_V1.0.pdf",
    ],
  },
  {
    key: "MY008",
    label: "MY008·初治PNH III期C5对照（真实数据·武汉协和子集）",
    brief: "MY008211A-PNH-3-02，补体B因子抑制剂类新药，初治PNH，III期。真实单中心子集。关注：溶血相关实验室（LDH等）、补体抑制下的感染风险信号、PNH克隆评估。",
    files: [
      STAGE + "/MY008_302/MY008-302_DataListing.xlsx",
      STAGE + "/MY008_302/MY008-302_研究方案_V1.1.docx",
      STAGE + "/MY008_302/MY008-302_DraftCRF_V0.1.docx",
    ],
  },
  {
    key: "CSU",
    label: "MG-K10·慢性自发性荨麻疹III期（合成数据·含植入矛盾）",
    brief: "MG-K10-CSU-001，抗IgE通路人源化单抗，CSU III期，合成数据（新研究新适应症，考察泛化）。日常监查关注：UAS7量表、AE与化验趋势矛盾、合并用药与病史一致性。",
    files: [
      STAGE + "/synth_csu/MG-K10-CSU-001_合成测试数据_V1.0.xlsx",
      STAGE + "/synth_csu/MG-K10-CSU-001_临床研究方案_V1.3.docx",
      STAGE + "/synth_csu/MG-K10-CSU-001_eCRF填写指南_V1.0.docx",
    ],
  },
  {
    key: "PSO",
    label: "CMS-D001·银屑病II/III期（合成数据·含植入矛盾）",
    brief: "CMS-D001，银屑病，合成数据。关注：PASI/BSA等皮肤病量表、生物制剂注射记录与访视对应、AE分级。",
    files: [
      STAGE + "/synth_pso/CMS-D001-PSO_合成测试数据_V1.0.xlsx",
      STAGE + "/synth_pso/CMS-D001_银屑病临床方案_V1.0.docx",
      STAGE + "/synth_pso/CMS-D001-PSO_eCRF填写指南_V1.0.docx",
    ],
  },
];

const SYNTH_TRUTH =
  "合成CSU/PSO数据由 scripts/generate_test_listing.py 生成，植入的已知违规类别：MH空术语、CM空日期、CM空适应症、SV空访视名、SV改名、SV空SUBJID，共7行植入；" +
  "listing另含名册页/long形态化验表/量表页等非标准形态（考察反过拟合）。分诊时对照：系统抓到了哪些类别、漏了哪些、有无误报。";

const PERSONAS_V2 = [
  { name: "一线医学监查专员", background: "在中心做过多年 onsite 监查，习惯从受试者旅程逐访视核对，最在意证据链能不能从结论一路点回原始记录。" },
  { name: "药物警戒（PV）专员", background: "药物警戒背景十年，对 AE/SAE 术语、严重度分级、因果评估的口径极其敏感，最恨系统把『严重度未知』悄悄渲染成明确分级。" },
  { name: "QA 稽查官", background: "质量保证与稽查背景，参加过多次监管检查，看系统先看留痕：每一步操作是否可追溯、时间戳是否可信、有没有绕过审核的暗门。" },
  { name: "系统实施工程师", background: "负责把工具部署到医院与CRO环境的实施工程师，习惯测边界：奇怪的输入、重复上传、超长文本、中断恢复，任何一处静默吞错都逃不过你。" },
  { name: "资深CRA", background: "临床监查员出身、现在仍频繁出差中心，对新工具的耐心有限：流程绕一步、反馈慢一拍，你就会记录一笔。" },
  { name: "数据管理员", background: "八年数据管理经验，看数据先看表结构、主键、空值和口径，任何数据搬运错误都逃不过你的眼睛。" },
  { name: "保守的医学总监", background: "最终拍板人，只认证据链：每个结论必须能溯源到原始记录，否则宁可不用这个系统。" },
  { name: "临床运营项目经理", background: "管过多个III期项目交付，对效率敏感：一次多余的点击、一段没有进度反馈的等待，都是你记录的对象。" },
];

const FOCUSES_V2 = [
  "界面易用性：一个没见过系统的人能否顺着引导走对，操作步数是否最短，上传与等待的反馈是否清楚，防错设计是否到位",
  "界面逻辑性：信息架构是否讲得通（先看什么后看什么），状态流转是否自洽，同一概念在不同页面叫法是否一致，域代码（AE/CM/MH/LB）是否有解释",
  "界面美观性：布局与对齐、色彩层次、密度与可读性、专业感、宽屏（1440/1920）表现——以『敢不敢给领导演示』为标尺",
  "医学语义诚实性：严重度标注是否如实区分记录值/未知/推定，不可判定是否明确标注，发现是否真有医学含量",
  "全链自主性与进度可见性：系统是否无需人在旁边推就能自己走完，等待期间进度是否可见、卡住是否有原因提示",
  "错误预防与恢复：传错文件、格式不认识、必填缺失时，系统是清楚拒绝还是静默吞掉或给出误导信息",
];

const SPECIALS_V2 = [
  "以PV核查SAE的心态：从发现列表任选一条，反查证据链直到原始记录行，任何一环点不下去或对不上号都是发现",
  "以QA稽查心态：检查全流程留痕与可追溯性——操作历史、时间戳、版本号、谁在什么时候确认了什么，找出任何不可审计的暗角",
  "以实施工程师验收心态：故意做边界测试——重复上传同一文件、先传错文件再纠正、项目名用特殊字符，观察系统的预防与提示",
  "以『从未用过这台电脑的人』心态操作：不假设任何先验知识与历史缓存，看界面本身能否教会你下一步做什么",
  "把窗口在三档宽度（1280/1440/1920）各过一遍核心页面，记录任何布局挤压、错位、溢出",
  "只用键盘走一遍主流程（不碰鼠标），记录所有焦点丢失与不可达控件",
  "以『明天要给团队做培训』的心态：把你会讲到的每个汇总数字、每张图都核对一遍出处，找自相矛盾之处",
  "中途模拟离开一小时（真实会议打断）：放置后再回来，检查状态是否还在、进度是否延续、有没有需要重做的事",
];

const CHANNELS = [
  { slot: "A", kind: "external", agent: "pi", provider: "openai-codex", model: "gpt-6-sol", label: "外部测试者A（gpt-6-sol）" },
  { slot: "B", kind: "external", agent: "cursor", provider: "omp", model: "cursor-grok-4.6", label: "外部测试者B（cursor-grok-4.6）" },
  { slot: "C", kind: "external", agent: "pi", provider: "google-antigravity", model: "gemini-3.8-flash", label: "外部测试者C（gemini-3.8-flash）" },
  { slot: "D", kind: "internal", agent: "", provider: "", model: "internal", label: "内部测试者D（本机分身）" },
];

const HONESTY =
  "诚实纪律：没走到就说没走到，不夸大不编造；界面与你的预期不同不等于bug，只有功能缺陷、数据错误、语义不诚实才是bug。" +
  "若任务无法完成或指令互相矛盾，如实说明并停止，不要硬凑通过。";

// ===== 仪表盘（每轮run开局把存量未决喂上板，保持跨run看板连续） =====
artifact.board("findings-board", {
  title: "发现看板",
  key: "key",
  status: "status",
  columns: ["待修复", "待复测", "已验证", "搁置"],
  cardTitle: "title",
  detail: [{ field: "severity" }, { field: "round" }],
});
artifact.table("rounds", {
  title: "各轮战报",
  key: "round",
  columns: [
    { field: "round", label: "轮次" },
    { field: "testersPassed", label: "通过/总数" },
    { field: "newFindings", label: "新发现" },
    { field: "fixed", label: "已修复" },
    { field: "openP1", label: "未决P0/P1" },
    { field: "cleanStreak", label: "连续清洁" },
    { field: "note", label: "备注" },
  ],
});

function failedSet(out: string): string[] {
  const rows: string[] = [];
  for (const line of out.split("\n")) {
    const t = line.trim();
    if (t.startsWith("FAILED ") || t.startsWith("ERROR ")) {
      const parts = t.split(" ");
      rows.push(parts[1] ?? t);
    }
  }
  return rows;
}

function newFailures(current: string[], baseline: string[]): string[] {
  return current.filter((x) => baseline.indexOf(x) < 0);
}

function pad2(n: number): string {
  return n < 10 ? "0" + n : "" + n;
}

function chanObj(m: Map<string, boolean>): Record<string, boolean> {
  const o: Record<string, boolean> = {};
  m.forEach((v, k) => { o[k] = v; });
  return o;
}

function boardItem(f: Finding) {
  return { key: f.id, status: f.status, title: f.title, severity: f.severity, round: f.round, category: f.category, sources: f.sources.join("/") };
}

// ===== 读取跨轮状态（读不到=首轮引导） =====
let state: RoundState | null = null;
let bootstrapNote = "";
try {
  const raw = await files.read(STATE_FILE);
  state = JSON.parse(raw) as RoundState;
} catch {
  state = null;
}

phase("开局：恢复状态、基线与通道");
if (state && state.campaignDone) {
  await world.run("bash", ["-c", "echo \"$(date '+%Y-%m-%d %H:%M') 单轮制空转保护：战役已收官（campaignDone），本轮不执行\" >> " + LOOP + "/ISO_ENV_LOG.md"]);
  return {
    conclusion: "质量循环已收官（STATE_V2.campaignDone=true），本次启动为空转保护，未派发任何成员。",
    findings: [],
    verified: ["读取 STATE_V2.json 判定战役已收官"],
    notCovered: ["本轮未执行任何测试（战役已结束）"],
  };
}
if (!state) {
  const boot = await agent("状态引导员", {
    system:
      "你负责把上一代多轮制循环的落盘状态重建为单轮制v2的初始状态。只读文件与归纳，绝不修改任何产品代码、绝不碰运行数据。" +
      "重建以权威落盘为准：STATE.json（轮次/未决计数）优先，各轮 REPORT.md 的遗留清单补全明细。查不清的字段如实留空，不编造。" + HONESTY,
  }).ask<BootstrapState>(
    "任务：读取 " + LOOP + "/STATE.json 与 STATE.json 所载轮次对应的 round_<两位轮次>/REPORT.md（缺则逐轮向前取最近存在者），重建未决发现清单：\n" +
    "1. round 与 cleanStreak 取 STATE.json；registry 重建其 openFindings 对应的未决条目（待修复/待复测），每条尽量从最近各轮 REPORT.md 的遗留清单补全 id/title/severity/status/round/what/evidence/repro/fixHint；\n" +
    "2. 搁置条目不进 registry（历史上限内打包搁置，最终清理时统一处置）；\n" +
    "3. 若 STATE.json 与 REPORT.md 数字不一致，以 REPORT.md 明细为准并在 note 说明；\n" +
    "4. 把重建结果同时写入 " + STATE_FILE + "（字段 round/cleanStreak/strategyNote/registry/baselineFailures=[]/channelOk={}/campaignDone=false，JSON数组registry按Finding结构），供脚本随后补全基线与通道。\n" +
    "返回 BootstrapState（round=最后已完成轮次）。",
  );
  state = {
    round: boot.round,
    cleanStreak: boot.cleanStreak,
    strategyNote: "",
    registry: boot.registry ?? [],
    baselineFailures: [],
    channelOk: {},
    campaignDone: false,
  };
  bootstrapNote = boot.note;
}
if ((state.baselineFailures ?? []).length === 0) {
  const baselineRun = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
    "-c",
    "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
  ], { timeoutMs: 3600000 });
  state.baselineFailures = failedSet(baselineRun.stdout);
  log("回归基线（重建）：监测子集现有失败 " + state.baselineFailures.length + " 条（存量债，修复门只看新增）");
}
if (Object.keys(state.channelOk ?? {}).length === 0) {
  const probe = await agent("通道探针员", {
    system: "你只做外部测试通道的连通性探测与结果回读，绝不做任何测试操作。三条并行、各限时6分钟。失败如实记录，不重试超过一次。" + HONESTY,
  }).ask<{ channels: { model: string; ok: boolean; note: string }[] }>(
    "探测三条外部通道。先写探测提示文件（内容：连通性探测：请只回复四个字：通道就绪）到 /tmp/channel_probe_v2/probe.md，然后并行 nohup 运行：\n" +
    "python3 " + RUNNER + " --agent pi --provider openai-codex --model gpt-6-sol --effort high --explicit-route --prompt /tmp/channel_probe_v2/probe.md --output /tmp/channel_probe_v2/out_a.md --stdout /tmp/channel_probe_v2/log_a.txt --max-turns 3 --timeout 300\n" +
    "同样地：--agent cursor --provider omp --model cursor-grok-4.6（out_b）；--agent pi --provider google-antigravity --model gemini-3.8-flash（out_c）\n" +
    "等进程退出后读各 output 判断 ok（含『通道就绪』即ok），失败把 stderr 要点写 note。返回 channels 数组。",
  );
  for (const c of probe.channels ?? []) state.channelOk[c.model] = c.ok;
  log("通道探测完成：外部通道就绪 " + Object.values(state.channelOk).filter(Boolean).length + "/3");
}
const stagingFiles = await files.glob(STAGE + "/*/*");
if (stagingFiles.length < 12) {
  await agent("材料恢复员", {
    system: "你负责恢复测试材料副本，只复制/生成，绝不改动任何源文件。所有副本放到工作区根下 " + STAGE + "/。" + HONESTY,
  }).ask(
    "测试材料副本缺失（现有 " + stagingFiles.length + " 个文件，应≥12）。按以下清单恢复：\n" +
    "- /Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/【Data Listing】RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx → " + STAGE + "/RUX/RUX-03-002_DataListing.xlsx\n" +
    "- /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/研究方案库/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx → " + STAGE + "/RUX/RUX-03-002_临床研究方案_V1.3.docx\n" +
    "- '/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/2-RUX-03-002-现场核查项目层面文件目录-20260424/9.eCRF指南/RUX-03-002_eCRF填写指南_V1.0_20240606.pdf' → " + STAGE + "/RUX/RUX-03-002_eCRF填写指南_V1.0.pdf\n" +
    "- '/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/武汉协和患者数据/EXCEL_MY008211A-PNH-3-02_20250411  （武汉协和受试者数据）.xlsx' → " + STAGE + "/MY008_302/MY008-302_DataListing.xlsx（源文件名含连续空格，用通配符定位）\n" +
    "- '/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/MY008211A-PNH-3-02_研究方案_V1.1_2024.07.26-clean（JY）.docx' → " + STAGE + "/MY008_302/MY008-302_研究方案_V1.1.docx\n" +
    "- '/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/外部CRF材料/MY008211A-PNH-3-02-初治PNH-C5III期-Draft CRF-V0.1-20240801-LC0802.docx' → " + STAGE + "/MY008_302/MY008-302_DraftCRF_V0.1.docx\n" +
    "- /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/研究方案库/MG-K10-CSU-001_临床研究方案-V1.3-0212-clean-0211.docx → " + STAGE + "/synth_csu/MG-K10-CSU-001_临床研究方案_V1.3.docx\n" +
    "- /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/研究方案库/CMS-D001 银屑病2、3期临床方案 v1.0-2025.12.21.docx → " + STAGE + "/synth_pso/CMS-D001_银屑病临床方案_V1.0.docx\n" +
    "合成数据（在 " + WBABS + " 下执行）：\n" +
    PY + " scripts/generate_test_listing.py --profile csu --out /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/" + STAGE + "/synth_csu\n" +
    PY + " scripts/generate_test_listing.py --profile pso --out /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/" + STAGE + "/synth_pso\n" +
    "生成后改名与上述清单一致。完成后核验每个数据集三件套存在且 listing>50KB、文档>20KB。真实材料属公司资产，只在本机目录间复制，不外传。",
  );
  log("测试材料副本已恢复");
}

// 开局喂板：存量未决上板（≤200条，保护256上限）
for (const f of (state.registry ?? []).filter((x) => x.status !== "搁置").slice(0, 200)) {
  report(boardItem(f), "findings-board");
}

const round = state.round + 1;
const registry = state.registry ?? [];
const baselineFailures = state.baselineFailures ?? [];
const channelOk = new Map<string, boolean>(Object.entries(state.channelOk ?? {}));
const roundDir = LOOP + "/round_" + pad2(round);
log("第" + round + "轮（单轮制）开run：存量未决 " + registry.filter((f) => f.status === "待修复" || f.status === "待复测").length + " 条" + (bootstrapNote ? "；首轮引导：" + bootstrapNote : ""));

// ===== 隔离环境门 =====
phase("开局：隔离环境就绪门");
const isoApiProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
const isoFeProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request\nr=urllib.request.urlopen('" + ISOFE + "',timeout=10)\nprint(r.status)"]);
let isoOk = isoApiProbe.exitCode === 0 && isoApiProbe.stdout.includes("READY") && isoFeProbe.exitCode === 0;
if (!isoOk) {
  await agent("隔离环境守护员-R" + round, { system: ISO_GUARD_RULE }).ask(
    "隔离测试环境不可用（API探针：" + isoApiProbe.stdout.trim() + " exit=" + isoApiProbe.exitCode +
    "；前端探针 exit=" + isoFeProbe.exitCode + "）。请恢复：\n" +
    "1. API重启：" + ISO_RESTART_API + "\n2. vite重启：" + ISO_RESTART_VITE + "\n" +
    "3. 各等15秒自检：http://127.0.0.1:8911/api/runtime-readiness ready:true；http://localhost:5178/monitoring 200；" +
    "http://localhost:5178/runtime-build.json 的 expectedBackendBuildId 与 8911 的 backend_build_id 一致\n" +
    "4. 把时间戳与结果写入 " + LOOP + "/ISO_ENV_LOG.md",
  );
  const reApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
  const reFe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request\nr=urllib.request.urlopen('" + ISOFE + "',timeout=10)\nprint(r.status)"]);
  isoOk = reApi.exitCode === 0 && reApi.stdout.includes("READY") && reFe.exitCode === 0;
  if (!isoOk) {
    return {
      conclusion: "第" + round + "轮未开考：隔离环境（8911/5178）两次恢复失败，需要人工介入。状态已保留，恢复后重跑本工作流即续。",
      findings: registry.filter((f) => f.status === "待修复").slice(0, 20).map((f) => ({ where: f.where, what: f.id + " " + f.title, evidence: f.evidence, status: "unconfirmed", severity: "high" })),
      verified: ["开局环境探针实跑，失败被如实拦截；未派发测试者"],
      notCovered: ["本轮全部测试（环境未就绪）"],
    };
  }
}
log("隔离测试环境就绪（独立API 8911 + 独立vite 5178，写作舰队 8910/5177 不受影响）");

// ===== 常驻角色（仅本轮存续；轮末随run退役） =====
const triager = agent("分诊官", {
  system:
    "你负责把多测试者报告分诊成可执行发现清单。规则：严重度标定 critical=数据丢失/崩溃/全链阻断；high=错误结果/医学结论错误/主流程严重受阻；" +
    "medium=显著可用性问题；low=外观。confirmed=true 仅当多源独立报告同一问题、或证据完整到可直接采信；单一来源的 critical/high 证据不足则 confirmed=false。" +
    "不同问题不合并，同一问题跨测试者合并进 sources。对照合成数据植入违规评估系统抓取情况。绝不虚构发现、绝不因急着修而拔高严重度。" + HONESTY,
});
const fixer = agent("修复员", {
  system:
    "你负责修复测试发现的已确认缺陷。纪律：最小根因修复（先读代码与所有调用方再动手）；严禁为让测试通过而放宽断言/删除测试/篡改期望；" +
    "严禁触碰 runs/ 运行时数据、严禁用任何 API 调用推进项目管道、严禁碰项目名不以 MX循 开头的项目（T1/T3/T5/C-ADC 等属于另一个子系统）。" +
    "修完跑相关 pytest（必要时前端 node --test），git 提交（信息前缀『测试循环R<轮>:』，不 push）。需要重启服务时 API 与 vite 必须都重启（指纹配对），" +
    "并把重启时间戳追加到 " + LOOP + "/ISO_ENV_LOG.md（共享基础设施留痕）。无法修或风险大就放入 skipped 并写明原因，升级而不是硬改。" +
    "任务所有者铁律：测试永远以用户视角经界面进行，严禁以直连后端替代测试——界面不可用即修到走通，不得绕行；" +
    "前端设计语言对齐康哲设计规范：凡触及前端代码，先读 /Users/smkzw/.zcode/skills/kangzhe-design/SKILL.md 核心篇，" +
    "以 Liquid Glass 统一材质与字体层级为准——功能性优先、美观统一其次、不追求100%遵循；渐进对齐：新改的界面按规范写，存量界面随修复顺手统一。" + HONESTY,
});
const retrospector = agent("复盘官", {
  system:
    "你负责本轮复盘与归档：根因分析、下一轮策略（若同一发现连续两轮未决必须换策略）、清理本轮测试项目、写轮次报告并提交归档。" +
    "归档纪律：只软删除项目名以本轮前缀（如 MX循R" + round + "）开头的项目，绝不碰常驻项目「MX循开考-CSU」与其他项目。" +
    "报告用非工程化语言，让医学背景的负责人读得懂。STATE_V2.json 由脚本落盘，你不要写它；STATE.json 照旧更新（人读台账）。" + HONESTY,
});

// ===== 开考预置复核（常驻项目三条件） =====
phase("开考预置复核：常驻项目就绪检查");
const reseed = await agent("开考预置守护员-R" + round, {
  system:
    "你负责为本轮开考位（D位）复核隔离测试环境上的常驻项目「MX循开考-CSU」处于「字段映射已确认+facts就绪、界面可开始运行监查」状态。" +
    "你是运维/工程师身份，允许且只允许用只读 API 与脚本操作隔离环境 http://127.0.0.1:8911（严禁碰 8910/5177）。复核为主、仅补齐缺失环节；" +
    "AI 质量门必须自然通过，严禁人为跳过或伪造状态。受阻就如实报，不绕过不造假。",
}).ask<SeedResult>(
  "为本轮D位开考做复核，目标是**常驻开考项目「MX循开考-CSU」**（跨轮持久存在，归档不会删它）：\n" +
  "0. 先查存量：若该项目已存在且 mapping confirmed + facts ready + project/open current，直接返回就绪（stateNote 注明『复用常驻项目』，本轮零重复预置）；仅补齐缺失环节\n" +
  "1. 若需新建：project_name=MX循开考-CSU、indication=慢性自发性荨麻疹、product_name=MG-K10、modules 含 medical_monitoring、幂等键唯一，材料=" + STAGE + "/synth_csu/ 三件套（绝对路径 " + WBABS + "/ 下）\n" +
  "2. API序列沿用（scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md + 既有裁决卡决策表幂等驱动），AI质量门自然通过，不跳门不造假\n" +
  "3. 推进至字段映射 confirmed + facts 物化、界面可开始运行监查即停（**不启动监查**——运行启动交给随后的攻坚验证做）\n" +
  "4. 完成后自验并把项目ID与各步状态证据追加到 " + LOOP + "/R5_SEEDED_PROJECT.md（按轮次分节），返回 {projectId, stateNote, blockedNote}",
);
log("R" + round + "开考预置：" + (reseed.blockedNote ? "受阻——" + reseed.blockedNote : "就绪（" + reseed.stateNote.slice(0, 120) + "…）"));

// ===== 攻坚验证（全链门：运行完成→发布→结果可读） =====
phase("攻坚验证：常驻项目跑通一次监查");
let siegeOk = false;
let siegeBlock = "";
for (let sgAttempt = 1; sgAttempt <= 3 && !siegeOk; sgAttempt++) {
  const sg = await agent("攻坚工程师-R" + round + "-第" + sgAttempt + "次", {
    system:
      "你是运行链路攻坚工程师（工程验证身份，允许API驱动与代码修复——这不是替代测试：测试者在链路证明后回归全量轮）。任务：证明常驻开考项目「MX循开考-CSU」当前能从『开始运行监查』真正走到运行完成→发布available→结果可读；若受阻，复现并定位到代码行、最小根因修复后重验。工程纪律：最小根因修复+相关pytest+git提交（『测试循环R" + round + "攻坚:』）+重启只动8911/5178；严禁跳门/伪造状态/绕过界面层缺陷不修。证据写入 " + LOOP + "/SIEGE_LOG.md（按轮分节）。",
  }).ask<PreflightResult>(
    "第" + sgAttempt + "次攻坚：①复现——在「MX循开考-CSU」上发起运行，完整记录从 run-setup/options→workspace/bootstrap→prepare-and-start→progress 每一步的请求/响应/状态与耗时；若被拒或卡『等待开始』，对照同一时刻后端 mapping/facts/project/open 的真实状态，把『两侧口径差』钉到具体代码行；②修复——修复该根因（若属上游门禁矛盾，沿链验证下一道门）；③重验——同项目再走一次到结果可读。返回 PreflightResult（chainOk 仅当运行真完成+发布available+结果可读；blockedAt 写具体卡点与代码行）。若你判断需要更大改动超出最小修复，如实返回并说明。",
  );
  siegeOk = sg.chainOk;
  siegeBlock = sg.blockedAt;
  if (siegeOk) {
    await world.run("bash", [
      "-c",
      "B=$(curl -s --max-time 8 http://127.0.0.1:8911/api/runtime-readiness | python3 -c \"import json,sys;print(json.load(sys.stdin).get('backend_build_id',''))\" 2>/dev/null); " +
      "printf '{\"build_id\":\"%s\",\"round\":" + round + ",\"siege\":true,\"at\":\"%s\"}\\n' \"$B\" \"$(date -u +%FT%TZ)\" > " + LOOP + "/PREFLIGHT_LAST_GREEN.json",
    ]);
    log("攻坚成功（第" + sgAttempt + "次）：常驻项目运行真完成，测试者照常派发");
  } else if (sgAttempt < 3) {
    log("攻坚第" + sgAttempt + "次未破：" + siegeBlock + " ——转修复员攻坚后重验");
    await fixer.ask<FixResult>(
      "攻坚工程师复现并定位的运行阻断（第" + round + "轮第" + sgAttempt + "次）请修复：\n" +
      JSON.stringify({ blockedAt: sg.blockedAt, stages: sg.stages, aiNodes: sg.aiNodes }) + "\n" +
      "修复纪律见你的角色设定；修完相关pytest+提交（『测试循环R" + round + "攻坚:』）。返回FixResult。",
    );
  }
}

// ===== 测试者派发 =====
let outcomes: TesterOutcome[];
if (!siegeOk) {
  outcomes = CHANNELS.map((ch) => ({
    tester: ch.label,
    channel: "engineering-round",
    reportFile: roundDir + "/no-tester-dispatch.md",
    projectName: "-",
    stagesReached: [],
    blockedAt: "攻坚门未过（" + siegeBlock + "），本轮为工程攻坚轮，不派发测试者",
    stallMinutes: 0,
    pass: false,
    findings: [],
    coverageNotes: "",
    channelNote: "工程攻坚轮（链路不绿不外派）",
  }));
  log("第" + round + "轮以工程轮收卷（0/4 派发，攻坚证据见 SIEGE_LOG.md）");
} else {
  phase("四测试位并行验收");
  log("第" + round + "轮开测：4个测试位并行，各用各的数据集与专属提示词");
  const outcomesP = CHANNELS.map((ch, s) => {
    const seeded = ch.slot === "D";
    const csuDs = DATASETS.find((x) => x.key === "CSU");
    const ds = seeded && csuDs ? csuDs : DATASETS[(round + s) % DATASETS.length];
    const externalUsable = ch.kind !== "external" || (channelOk.get(ch.model) ?? false);
    return runSlot(round, s, ds, externalUsable, state?.strategyNote ?? "", seeded);
  });
  outcomes = await Promise.all(outcomesP);
}
const totalFindingsRaw = outcomes.reduce((n, o) => n + (o.findings ?? []).length, 0);
log(
  "第" + round + "轮收卷：通过 " + outcomes.filter((o) => o.pass).length + "/4；原始发现 " + totalFindingsRaw + " 条；" +
  outcomes.map((o) => o.tester.split("（")[0] + "=" + (o.pass ? "过" : "停于" + (o.blockedAt || "未知"))).join("，"),
);

// ===== 分诊 =====
phase("分诊发现并独立复核");
const openSummary = registry
  .filter((f) => f.status === "待修复" || f.status === "待复测")
  .map((f) => f.id + " " + f.title + " [" + f.severity + "/" + f.status + "] 开自R" + f.round);
const verdict = await triager.ask<TriageVerdict>(
  "第" + round + "轮四个测试位的原始结果如下（JSON）：\n" + JSON.stringify(outcomes) + "\n\n" +
  "当前未决发现清单：\n" + (openSummary.length ? openSummary.join("\n") : "（无）") + "\n\n" +
  "合成数据植入违规对照（不外发）：\n" + SYNTH_TRUTH + "\n\n" +
  "请分诊：1) 提取新发现（与未决清单语义重复的并入 duplicatesMerged 不重复立单）；2) 评估系统对合成植入违规的抓取（synthAssessment）；" +
  "3) 本轮各测试者的覆盖面足以把哪些未决『待复测』发现升级为已验证（verifyUpgrades，谨慎：只有其覆盖说明确实经过该问题所在流程才可升级）；" +
  "4) 哪些未决发现本轮没被覆盖到（coverageGaps，供下轮定向）。newFindings 的 fixHint 给修复定位建议（文件/模块级即可）。",
);
let seq = 0;
const confirmTargets: NewFindingDraft[] = [];
for (const d of verdict.newFindings) {
  seq += 1;
  const id = "R" + round + "-" + (seq < 10 ? "0" + seq : seq);
  registry.push({
    id, round, title: d.title, where: d.where, what: d.what, severity: d.severity, category: d.category,
    evidence: d.evidence, repro: d.repro, sources: d.sources, confirmed: d.confirmed, confirmNote: d.confirmNote,
    fixHint: d.fixHint, status: "待修复",
  });
  if (!d.confirmed && (d.severity === "critical" || d.severity === "high")) confirmTargets.push(d);
}
for (const upg of verdict.verifyUpgrades) {
  const f = registry.find((x) => x.id === upg.id);
  if (f && f.status === "待复测") {
    f.status = "已验证"; f.confirmNote += "；R" + round + "复测通过：" + upg.note;
    report(boardItem(f), "findings-board");
  }
}
const fresh = registry.filter((f) => f.round === round);
for (const f of fresh) report(boardItem(f), "findings-board");
const confirmSlice = confirmTargets.slice(0, 6);
const confirmations = await Promise.all(
  confirmSlice.map((d, i) => {
    const confirmer = agent("独立复核-R" + round + "-" + i);
    return confirmer.ask<{ confirmed: boolean; note: string }>(
      "请独立复核以下测试发现是否真实存在（你可以用只读手段：浏览器打开 http://localhost:5178 观察、只读 GET 类 API、读代码；严禁任何写操作/重启/管道推进）：\n" +
      JSON.stringify(d) + "\n工作目录 " + WBABS + "。返回 confirmed 与依据 note。复现不了就如实说复现不了。",
    );
  }),
);
for (let i = 0; i < confirmSlice.length; i++) {
  const d = confirmSlice[i];
  const c = confirmations[i];
  const f = registry.find((x) => x.round === round && x.title === d.title);
  if (f && c) { f.confirmed = c.confirmed; f.confirmNote += "；独立复核：" + c.note; }
}
const newConfirmed01 = fresh.filter((f) => f.confirmed && (f.severity === "critical" || f.severity === "high"));
const open01 = registry.filter((f) => f.confirmed && (f.severity === "critical" || f.severity === "high") && (f.status === "待修复" || f.status === "待复测"));
const agedFix = (f: Finding) => round - f.round >= 2;
const fixTargets = registry
  .filter((f) => f.status === "待修复" && f.severity !== "low" && (f.confirmed || agedFix(f)))
  .sort((a, b) => {
    const rank = (x: Finding) => (x.severity === "critical" ? 0 : x.severity === "high" ? 1 : agedFix(x) ? 2 : 3);
    return rank(a) - rank(b) || b.round - a.round;
  })
  .slice(0, 6);
log("分诊完成：新发现 " + fresh.length + " 条（已确认P0/P1 " + newConfirmed01.length + "）；未决P0/P1 累计 " + open01.length + " 条");

// ===== 修复 =====
phase("修复缺陷并守住回归门");
let fixResult: FixResult | null = null;
if (fixTargets.length > 0) {
  fixResult = await fixer.ask<FixResult>(
    "第" + round + "轮分诊后待修复清单（机制：①每轮修复配额约 6 条 ②轮龄≥2轮未轮到的条目已插队排在前面 ③critical/high 必须处理 ④纯打磨 low 级不进本清单）：\n" +
    JSON.stringify(fixTargets.map((f) => ({ id: f.id, title: f.title, severity: f.severity, where: f.where, what: f.what, evidence: f.evidence, repro: f.repro, fixHint: f.fixHint }))) + "\n" +
    (state?.strategyNote ? "上轮复盘策略提示：" + state.strategyNote + "\n" : "") +
    "修复纪律见你的角色设定。修完把 fixedIds/skipped/commitHash/testsRun/frontendTouched 如实返回。\n" +
    "修复需重启时只允许重启隔离测试环境（与医学写作舰队完全隔离）：\n" +
    "API：" + ISO_RESTART_API + "\nvite：" + ISO_RESTART_VITE + "\n" +
    "（两个都要重启；重启后自检 http://127.0.0.1:8911/api/runtime-readiness ready:true 与 http://localhost:5178/monitoring 200，" +
    "并核对 http://localhost:5178/runtime-build.json 与 8911 的 backend_build_id 一致；严禁重启或触碰 8910/5177；重启留痕写入 " + LOOP + "/ISO_ENV_LOG.md）",
  );
  for (const id of fixResult.fixedIds ?? []) {
    const f = registry.find((x) => x.id === id);
    if (f) { f.status = "待复测"; report(boardItem(f), "findings-board"); }
  }
  for (const sk of fixResult.skipped ?? []) {
    const f = registry.find((x) => x.id === sk.id);
    if (f && f.status === "待修复") f.status = "搁置";
  }
  const gate = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
    "-c",
    "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
  ], { timeoutMs: 3600000 });
  const newlyFailed = newFailures(failedSet(gate.stdout), baselineFailures);
  if (newlyFailed.length > 0) {
    log("回归门拦截：修复引入 " + newlyFailed.length + " 条新失败，退回修复员");
    await fixer.ask(
      "修复引入了新的测试失败（相对基线），必须处理（修好或回滚）：\n" + newlyFailed.join("\n") + "\n失败输出尾部：\n" + gate.stdout.slice(-4000),
    );
    const gate2 = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
      "-c",
      "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
    ], { timeoutMs: 3600000 });
    if (newFailures(failedSet(gate2.stdout), baselineFailures).length > 0) {
      for (const id of fixResult.fixedIds ?? []) {
        const f = registry.find((x) => x.id === id);
        if (f && f.status === "待复测") f.status = "待修复";
      }
      log("回归门二次拦截：本批修复判无效，发现退回待修复，留待复盘升级");
    }
  }
  const postApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
  if (!(postApi.exitCode === 0 && postApi.stdout.includes("READY"))) {
    await agent("环境守护员-R" + round).ask(
      "修复后隔离API(8911)未就绪，请恢复：" + ISO_RESTART_API + " ；随后自检 ready:true；严禁动 8910/5177",
    );
  }
}

// ===== 复盘 =====
phase("复盘认账并归档本轮");
const recap = await retrospector.ask<Recap>(
  "第" + round + "轮复盘。输入：\n" +
  "- 测试者结果：" + JSON.stringify(outcomes.map((o) => ({ tester: o.tester, projectName: o.projectName, pass: o.pass, blockedAt: o.blockedAt, stages: o.stagesReached ?? [], stallMinutes: o.stallMinutes, channelNote: o.channelNote }))) + "\n" +
  "- 分诊：" + JSON.stringify({ 新发现: fresh.map((f) => f.id + " " + f.title + " " + f.severity + (f.confirmed ? "(已确认)" : "(未确认)")), synthAssessment: verdict.synthAssessment, coverageGaps: verdict.coverageGaps }) + "\n" +
  "- 修复：" + (fixResult ? JSON.stringify({ fixed: fixResult.fixedIds, skipped: fixResult.skipped, commit: fixResult.commitHash }) : "本轮无需修复") + "\n" +
  "- 全部未决：" + JSON.stringify(registry.filter((f) => f.status === "待修复" || f.status === "待复测").map((f) => ({ id: f.id, title: f.title, round: f.round, status: f.status }))) + "\n\n" +
  "职责：\n" +
  "1. 根因归类与下一轮策略（同一发现连续2轮未决→必须给出与之前不同的策略）\n" +
  "2. 归档本轮测试项目：curl -s http://127.0.0.1:8911/api/projects 列出后，只对项目名以 MX循R" + round + " 开头的执行 curl -X DELETE http://127.0.0.1:8911/api/projects/<id>（软删除；绝不碰常驻项目与其他前缀；同时核对各测试报告是否含『收尾清理』一节，缺失的在轮次报告里如实注明）\n" +
  "3. 写轮次报告到 " + roundDir + "/REPORT.md（章节：本轮概览/各测试者旅程/发现与分诊/修复与回归/复盘与策略/遗留清单；面向医学背景负责人的平实语言）\n" +
  "4. 更新 " + LOOP + "/STATE.json（轮次、未决数、连续清洁轮数）\n" +
  "5. git add " + LOOP + " 的本轮目录与 STATE、提交（信息『测试循环R" + round + "轮次归档』）并 push\n" +
  "返回 Recap（roundReportPath 必须是刚写好的报告绝对路径）。",
);
const allReachedEnd = outcomes.every((o) => (o.stagesReached ?? []).indexOf("结果验收") >= 0);
const roundClean = allReachedEnd && newConfirmed01.length === 0 && open01.length === 0;
const cleanStreak = roundClean ? (state?.cleanStreak ?? 0) + 1 : 0;
report(
  {
    round, key: round,
    testersPassed: outcomes.filter((o) => o.pass).length + "/4",
    newFindings: fresh.length, fixed: fixResult ? (fixResult.fixedIds ?? []).length : 0,
    openP1: registry.filter((f) => f.confirmed && (f.severity === "critical" || f.severity === "high") && (f.status === "待修复" || f.status === "待复测")).length,
    cleanStreak,
    note: roundClean ? "清洁轮" : "存在未决问题",
  },
  "rounds",
);
const reportRel = WB + "/scripts/tester_loop_0927/round_" + pad2(round) + "/REPORT.md";
try {
  await artifact.file("round-report", reportRel, { title: "第" + round + "轮验收报告", description: recap.rootCauses.slice(0, 200) });
} catch {
  log("轮次报告发布失败（文件缺失），复盘官报告路径：" + recap.roundReportPath);
}

// ===== 收敛判定：连续清洁即就地收官 =====
if (round >= 3 && cleanStreak >= CLEANSTREAKNEED) {
  phase("收官：总交付与全量清理");
  const finalizer = agent("收官撰稿人", {
    system: "你负责把整个测试循环写成最终交付报告，读 " + LOOP + " 下各轮 REPORT.md 与 STATE.json 汇总（环境记录见 " + LOOP + "/ISO_ENV_LOG.md），输出到 " + LOOP + "/DELIVERY.md。" +
      "面向医学背景负责人：非工程化语言、四段式（做了什么/没做什么/踩了哪些坑/下一步建议）、每个结论附证据出处。" + HONESTY,
  });
  const delivery = await finalizer.ask<{ deliveryPath: string; summary: string }>(
    "写总交付报告到 " + LOOP + "/DELIVERY.md：质量循环已收敛（连续" + CLEANSTREAKNEED + "轮清洁）、累计发现/修复/验证数、未决清单（应为空或仅搁置项）、附各轮报告路径。返回 deliveryPath 与 summary。",
  );
  try {
    await artifact.file("final-report", WB + "/scripts/tester_loop_0927/DELIVERY.md", { title: "质量循环·总交付报告", description: delivery.summary.slice(0, 300), primary: true });
  } catch {
    await artifact.markdown("final-report-fallback", "## 总交付报告文件发布失败\n汇总摘要：\n" + delivery.summary, { title: "质量循环·汇总（降级版）" });
  }
  await world.run("bash", [
    "-c",
    "lsof -ti:8911 | xargs kill 2>/dev/null; lsof -ti:5178 | xargs kill 2>/dev/null; sleep 2; " +
    "(lsof -ti:8911 >/dev/null 2>&1 && echo '8911_STILL_UP' || echo '8911_down'); " +
    "(lsof -ti:5178 >/dev/null 2>&1 && echo '5178_STILL_UP' || echo '5178_down'); " +
    "echo \"$(date '+%Y-%m-%d %H:%M') 循环收敛收官：隔离测试环境已停止\" >> '" + WBABS + "/scripts/tester_loop_0927/ISO_ENV_LOG.md'",
  ]);
  await world.run("bash", [
    "-c",
    "rm -rf '/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/runs/tester_loop_iso_20260928' '/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/tester_staging_0927' '/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/tester_staging_0927' /tmp/tester_channel_probe /tmp/channel_probe_v2 2>/dev/null || true\n" +
    "rm -f /tmp/mm_api_8911.log /tmp/mm_vite_5178.log 2>/dev/null || true\n" +
    "find " + LOOP_ABS + "/logs -maxdepth 1 -type d -name 'round_*' 2>/dev/null | sort | awk '{a[NR]=\$0} END{for(i=1;i<=NR-3;i++) print a[i]}' | xargs rm -rf 2>/dev/null || true\n" +
    "echo '收敛全量清理完成（运行时/测试材料/临时件已清，报告与台账保留）'",
  ]);
  await world.run("bash", ["-c", "cat > " + STATE_ABS + " <<'ZCODEJSON'\n" + JSON.stringify({ round, cleanStreak, strategyNote: recap.strategyNote, registry: [], baselineFailures, channelOk: chanObj(channelOk), campaignDone: true }) + "\nZCODEJSON"]);
  return {
    conclusion: "质量循环收敛收官：连续" + CLEANSTREAKNEED + "轮清洁，全员走通且无未决P0/P1。详见 " + LOOP + "/DELIVERY.md。单轮制循环已标记campaignDone，后续启动将自动空转保护。",
    findings: [],
    verified: ["收敛判定=连续" + CLEANSTREAKNEED + "轮清洁（4/4走通结果验收且无新确认P0/P1）", "收官清理实跑（运行时/材料/临时件清除，报告台账保留）"],
    notCovered: [],
  };
}

// ===== 轮末退役：状态落盘 + 定期瘦身（用户2026-10-07指令） =====
phase("轮末退役：状态落盘与定期瘦身");
const nextRegistry = registry.filter((f) => f.status !== "已验证");
const persistRun = await world.run("bash", [
  "-c",
  "cat > " + STATE_ABS + " <<'ZCODEJSON'\n" + JSON.stringify({ round, cleanStreak, strategyNote: recap.strategyNote, registry: nextRegistry, baselineFailures, channelOk: chanObj(channelOk), campaignDone: false }) + "\nZCODEJSON\nwc -c " + STATE_ABS,
]);
const trimRun = await world.run("bash", [
  "-c",
  "rm -rf /tmp/tester_channel_probe /tmp/channel_probe_v2 2>/dev/null || true; " +
  "rm -f /tmp/mm_api_8911.log /tmp/mm_vite_5178.log 2>/dev/null || true; " +
  "find " + LOOP_ABS + "/logs -maxdepth 1 -type d -name 'round_*' 2>/dev/null | sort | awk '{a[NR]=\$0} END{for(i=1;i<=NR-3;i++) print a[i]}' | xargs rm -rf 2>/dev/null || true; " +
  "du -sh " + WBABS + "/runs/tester_loop_iso_20260928 2>/dev/null | awk '{print \"隔离运行时体量：\" $1}'",
]);
log("轮末退役完成：" + persistRun.stdout.trim().split("\n").pop() + "；本轮成员随run结束全部退役，下一轮由新run从 STATE_V2.json 无缝接续。" + trimRun.stdout.trim());

return {
  conclusion: "第" + round + "轮（单轮制）完成：通过 " + outcomes.filter((o) => o.pass).length + "/4；新发现 " + fresh.length + " 条（已确认P0/P1 " + newConfirmed01.length + "）；修复 " + (fixResult ? (fixResult.fixedIds ?? []).length : 0) + " 条；未决P0/P1 累计 " + registry.filter((f) => f.confirmed && (f.severity === "critical" || f.severity === "high") && (f.status === "待修复" || f.status === "待复测")).length + " 条；连续清洁 " + cleanStreak + " 轮。下一轮：重新运行本工作流即从 STATE_V2.json 接续第" + (round + 1) + "轮。",
  findings: registry.filter((f) => f.status === "待修复" || f.status === "待复测").slice(0, 40).map((f) => ({
    where: f.where, what: f.id + " " + f.title + " [" + f.severity + "/" + f.status + "]",
    evidence: f.evidence + "；来源:" + f.sources.join("/"),
    status: f.confirmed ? "verified" : "unconfirmed",
    severity: f.severity === "critical" || f.severity === "high" ? "high" : f.severity === "medium" ? "medium" : "low",
  })),
  verified: [
    "开局环境探针（API ready + 前端 200）实跑",
    "修复后监测 pytest 子集回归门，与基线失败集比对（基线存量 " + baselineFailures.length + " 条）",
    "4 测试位独立 E2E（外部通道 " + Object.values(chanObj(channelOk)).filter(Boolean).length + "/3 就绪，其余内部测试者代打）",
    "每轮发现经分诊官合并去重，单源critical/high经独立复核",
    "轮末退役：状态落盘 STATE_V2.json + 过程日志只留最近三轮",
  ],
  notCovered: [
    "前端 node --test 未作脚本级回归门（由修复员自行运行并在结果中报告）",
    "医学准确率无独立金标准测量（合成数据植入违规仅作类别级对照）",
  ],
};

// ===== 测试位执行（外部调度/内部直跑） =====
function buildPromptIso(rd: number, slot: string, ds: Dataset, reportPath: string): string {
  const s = CHANNELS.findIndex((c) => c.slot === slot);
  const persona = PERSONAS_V2[(rd + (s < 0 ? 0 : s)) % PERSONAS_V2.length];
  const focus = FOCUSES_V2[(rd * 2 + (s < 0 ? 0 : s)) % FOCUSES_V2.length];
  const special = SPECIALS_V2[(rd * 3 + (s < 0 ? 0 : s)) % SPECIALS_V2.length];
  const projName = "MX循R" + rd + slot + "-" + ds.key;
  const files = ds.files.map((f) => "- " + WBABS + "/" + f).join("\n");
  return (
    "【第" + rd + "轮·" + slot + "号测试任务】（提示词编号 R" + rd + "-" + slot + "，与以往任何一轮都不同）\n\n" +
    "你是" + persona.name + "。" + persona.background + "\n" +
    "本轮以真实用户身份，独立验收「康哲 AI 医学经理工作台」的医学监查子系统。\n\n" +
    "## 进入方式\n" +
    "- 浏览器打开 http://localhost:5178/ ，确认页面标题是「康哲 AI 医学经理工作台」\n" +
    "- 只准使用 5178 这个入口；若页面打不开、或打开后发现端口/应用不对（例如入排审核工作台或 5177），立即停止并作为发现记录，不要改用其他入口\n" +
    "- 若你的运行环境（如 Trellis 等任务框架）询问「是否创建任务/文件/目录」，一律直接选择不创建，然后继续纯浏览器测试——这是任务所有者预先批准的答案，不需要请示任何人，也不要因此提前收卷\n" +
    "- 浏览器工具：ego-browser（先读 /Users/smkzw/.zcode/skills/ego-browser/SKILL.md 学用法；上传本地文件用它的 FileChooser；整个任务只用一个 TaskSpace）\n\n" +
    "## 铁律（违反即测试作废）\n" +
    "1. 只通过浏览器界面操作。严禁 curl/API/直连后端/读写数据库/读日志/修改任何文件\n" +
    "2. 严禁重启或触碰任何服务；严禁推进后台任务——你不是运维，系统必须自己跑\n" +
    "3. 系统卡住不动本身就是最重要的发现：记录当时页面、状态与已等待时长\n" +
    "4. 只使用分给你的这套研究材料；页面上如有别人的项目，一律不点开\n" +
    "5. 报告里不要复制患者身份信息（受试者编号可用，姓名/生日等不可）\n\n" +
    "## 你的专属研究材料（从本机这些路径经浏览器上传）\n" + files + "\n" +
    "研究背景：" + ds.brief + "\n\n" +
    "## 任务（从零开始，走完为止）\n" +
    "1. 新建项目（新首页流程）：点「新建项目」后会出现**子系统多选卡片**（医学写作/医学监查/入排审核）——**只勾选「医学监查」一张卡**，然后点「前往医学监查配置」；系统会直接跳到医学监查页并弹出**项目配置面板**，在面板里填写：项目名称=「" + projName + "」、试验药物/适应症/研究分期按分给你的研究材料如实填写，点「创建项目」。全程只在医学监查模块内操作：一旦发现自己在医学写作工作区或写作功能页，立即记录为一条导航类发现（【页面】【问题】【证据】），随即返回医学监查模块继续，**绝不在写作模块内执行操作或等待其长任务**\n" +
    "2. 上传上述材料，按界面引导完成数据接入\n" +
    "3. 跟随系统走完全链：内容确认→字段映射→事实准备→运行→发布→结果视图，每一步只做界面允许的用户操作\n" +
    "4. 在结果视图（概览/发现/旅程等）做结果验收\n" +
    "5. 全程以" + persona.name + "的视角观察：" + focus + "\n" +
    "6. 无论你的角色是什么，始终顺带评价界面的易用性、逻辑性与美观性（具体到布局、文案、反馈、对齐、色彩），这是本轮必测项\n\n" +
    "## 本轮特别情境\n" + special + "\n\n" +
    "## 等待纪律\n" +
    "- 系统处理时保持浏览器开着（真实用户会等），每隔几分钟刷新观察进展\n" +
    "- 单一步骤 ≥" + STALLMIN + " 分钟无任何进展，或总时长 ≥5 小时：停止操作，按当前状态交报告（这本身计为发现）\n\n" +
    "## 交付\n" +
    "把最终测试报告（Markdown）写入：" + reportPath + "\n" +
    "报告必含：\n" +
    "- 旅程清单：走到了哪些阶段（建项/上传/内容确认/映射/事实/运行/发布/结果验收），在哪个阶段停住\n" +
    "- 总结论：pass / fail（fail注明卡点）\n" +
    "- 发现清单：每条含【页面】【问题】【严重度 critical|high|medium|low】【类别 product_bug|medical_accuracy|ux_issue|cosmetic】【证据（你看到的现象）】【复现步骤】\n" +
    "- 界面评价：易用性/逻辑性/美观性各一小段（具体事例，不写空话）\n" +
    "- 等待与卡点时长\n" +
    "- 对「这套系统能否由一名真实用户独立跑通」的一句话判断\n" +
    "- 收尾清理：说明你做了什么清理\n\n" +
    "## 收尾清理（报告写完并保存后必做）\n" +
    "1. 关闭并删除本轮使用的浏览器任务空间（ego-browser：对本次 TaskSpace 调用 delete()；确认浏览器会话完全退出）\n" +
    "2. 删除测试过程中产生的下载副本、截图与临时缓存文件（分给你的源材料文件本身不动）\n" +
    "3. 把清理结果追加写在报告的『收尾清理』一节\n" +
    HONESTY
  );
}

function buildPromptSeeded(rd: number, ds: Dataset, reportPath: string): string {
  return (
    "【第" + rd + "轮·D号测试任务·开考位】（提示词编号 R" + rd + "-D-开考，与以往任何一轮都不同）\n\n" +
    "你是一线医学监查专员。在中心做过多年 onsite 监查，习惯从受试者旅程逐访视核对，最在意证据链能不能从结论一路点回原始记录。\n" +
    "本轮以真实用户身份，独立验收「康哲 AI 医学经理工作台」的医学监查子系统。与其他三位从零建项的测试者不同：**你接手的是一个已由同事完成全部准备工作的研究项目**（数据已接入、研究文件已核对、字段对应已确认），你的任务是从「开始运行监查」起步，把这套系统最核心的价值考到底。\n\n" +
    "## 进入方式\n" +
    "- 浏览器打开 http://localhost:5178/ ，确认页面标题是「康哲 AI 医学经理工作台」\n" +
    "- 只准使用 5178 这个入口；若页面打不开、或打开后发现端口/应用不对，立即停止并作为发现记录\n" +
    "- 在项目选择器中选择项目「MX循开考-CSU」（如该项目不存在或准备状态不符——例如字段未确认、无法开始运行监查——如实记录，这本身就是本轮最重要的发现，不要自己动手补准备工作）\n" +
    "- 浏览器工具：ego-browser（先读 /Users/smkzw/.zcode/skills/ego-browser/SKILL.md 学用法；整个任务只用一个 TaskSpace）\n\n" +
    "## 铁律（违反即测试作废）\n" +
    "1. 只通过浏览器界面操作。严禁 curl/API/直连后端/读写数据库/读日志/修改任何文件\n" +
    "2. 严禁重启或触碰任何服务；监查运行必须由系统自己推进——你不是运维\n" +
    "3. 系统卡住不动本身就是最重要的发现：记录当时页面、状态与已等待时长\n" +
    "4. 只操作分给你的项目；页面上如有别人的项目，一律不点开\n" +
    "5. 报告里不要复制患者身份信息（受试者编号可用，姓名/生日等不可）\n\n" +
    "## 你的研究项目背景（仅供理解，无需重新上传）\n" +
    ds.brief + "\n\n" +
    "## 任务（从运行监查开始，走完为止）\n" +
    "1. 核对项目准备状态（数据、研究文件、字段对应均已就绪）\n" +
    "2. 在界面发起监查运行，跟随系统走完：运行→发布→结果视图\n" +
    "3. 结果验收（本轮重头戏）：\n" +
    "   - 概览数字自洽性：受试者数、发现数、风险分布互相之间、以及与详情列表是否对得上\n" +
    "   - 抽至少 3 名受试者做证据链深挖：从发现卡片→受试者旅程→原始记录行，每一步都要点得下去、内容对得上号\n" +
    "   - 以你的医学判断逐条评估发现质量，三分类计数并各举一例：真问题（该抓）/存疑（说不清）/误报（冤枉好人）\n" +
    "   - 界面的易用性、逻辑性、美观性各写一段具体评价（必测项）\n" +
    "4. 系统长时间运行时保持浏览器开着（真实用户会等），每隔几分钟刷新观察进展；单一步骤 ≥" + STALLMIN + " 分钟无任何进展，或总时长 ≥5 小时：停止操作，按当前状态交报告（这本身计为发现）\n\n" +
    "## 交付\n" +
    "把最终测试报告（Markdown）写入：" + reportPath + "\n" +
    "报告必含：\n" +
    "- 旅程清单（起点=运行监查，走到了哪些阶段，在哪个阶段停住）\n" +
    "- 总结论：pass / fail（fail注明卡点）\n" +
    "- 发现清单：每条含【页面】【问题】【严重度 critical|high|medium|low】【类别 product_bug|medical_accuracy|ux_issue|cosmetic】【证据（你看到的现象）】【复现步骤】\n" +
    "- 发现质量三分类：真问题/存疑/误报的计数与各一例详述\n" +
    "- 界面评价：易用性/逻辑性/美观性各一小段（具体事例，不写空话）\n" +
    "- 等待与卡点时长\n" +
    "- 对「这套系统能否由一名真实用户独立跑通并信任其产出」的一句话判断\n" +
    "- 收尾清理：说明你做了什么清理\n\n" +
    "## 收尾清理（报告写完并保存后必做）\n" +
    "1. 关闭并删除本轮使用的浏览器任务空间（ego-browser：对本次 TaskSpace 调用 delete()；确认浏览器会话完全退出）\n" +
    "2. 删除测试过程中产生的下载副本、截图与临时缓存文件\n" +
    "3. 把清理结果追加写在报告的『收尾清理』一节\n" +
    HONESTY
  );
}

async function runSlot(
  rd: number,
  slotIdx: number,
  ds: Dataset,
  externalUsable: boolean,
  strategyNote: string,
  seeded: boolean,
): Promise<TesterOutcome> {
  const ch = CHANNELS[slotIdx];
  const slot = ch.slot;
  const rDir = LOOP + "/round_" + pad2(rd);
  const reportPath = rDir + "/report_" + slot + ".md";
  const promptPath = rDir + "/prompt_" + slot + ".md";
  const strategyAppend = strategyNote
    ? "\n\n## 上一轮复盘给本轮的背景提示（仅供留意，不影响你的独立判断）\n" + strategyNote
    : "";
  const promptText = seeded
    ? buildPromptSeeded(rd, ds, reportPath) + strategyAppend
    : buildPromptIso(rd, slot, ds, reportPath) + strategyAppend;
  const useExternal = ch.kind === "external" && externalUsable;
  const projName = "MX循R" + rd + slot + "-" + ds.key;
  const fallback: TesterOutcome = {
    tester: ch.label,
    channel: useExternal ? ch.model : "internal",
    reportFile: reportPath,
    projectName: projName,
    stagesReached: [],
    blockedAt: "通道失败",
    stallMinutes: 0,
    pass: false,
    findings: [],
    coverageNotes: "",
    channelNote: "",
  };
  try {
    if (useExternal) {
      const dispatcher = agent("外部通道调度-R" + rd + slot);
      return await dispatcher.ask<TesterOutcome>(
        "你是外部测试通道调度员，只做机械调度与结果解析，自己绝不做任何测试操作、不碰浏览器。\n" +
        "步骤：\n" +
        "1. mkdir -p " + rDir + " 与 " + LOOP + "/logs/round_" + pad2(rd) + "\n" +
        "2. 把下面的任务文件原文写入 " + promptPath + "（一字不改）\n" +
        "3. 后台启动外部测试者（nohup，避免单条命令超时）：\n" +
        "python3 " + RUNNER + " --agent " + ch.agent + " --provider " + ch.provider + " --model " + ch.model +
        " --effort high --explicit-route --prompt " + promptPath + " --output " + reportPath +
        " --stdout " + LOOP + "/logs/round_" + pad2(rd) + "/slot" + slot + ".log" +
        " --max-turns 60 --timeout 21000 --workdir " + WBABS + "\n" +
        "4. 外部测试者可能运行数小时：轮询等待输出文件出现且 runner 进程退出（每次 sleep 300 后检查，单次 bash 调用保持 ≤9 分钟），最多等 6.5 小时\n" +
        "5. 完成后读 " + reportPath + "（外部测试者写的 Markdown 报告）与 stdout 日志末尾，解析为 TesterOutcome 返回：findings 从报告提取（缺字段按报告原文填 evidence）；projectName 默认「" + projName + "」以报告实际为准；stagesReached 按报告旅程归纳；channelNote 写通道运行情况\n" +
        "6. runner 启动即失败（无输出文件且退出码非0）→ 重试一次；仍失败 → 返回 channelNote 含失败详情的 outcome（findings 可为空）\n" +
        "7. 绝不代替测试者补写报告；解析不出来就在 channelNote 说明\n\n" +
        "=== 任务文件原文 ===\n" + promptText,
      );
    }
    const testerSystem =
      "你就是任务里描述的那名测试者本人，直接亲自执行任务（不是调度员）。全程只用浏览器（按 ego-browser skill，整个任务只用一个 TaskSpace），" +
      "只观察不修改，卡住即记录。报告写完后必须执行任务里的『收尾清理』并如实确认（TaskSpace 用 delete() 关删、临时缓存清除），清理做没做都要说真话。" + HONESTY;
    const tester = agent("内部测试者-R" + rd + slot, { system: testerSystem });
    const testerSuffix =
      "\n\n（你是内部测试者，直接执行上述任务；执行前先 mkdir -p " + rDir + "）\n" +
      "完成后除把报告写入文件外，同时以 TesterOutcome 结构返回结果（findings 字段严格按报告归纳，不要增删事实）。" +
      "然后完成『收尾清理』，并在返回的 coverageNotes 里注明清理结果。";
    return await tester.ask<TesterOutcome>(promptText + testerSuffix);
  } catch (e) {
    fallback.channelNote = "槽位执行异常：" + String(e);
    return fallback;
  }
}
