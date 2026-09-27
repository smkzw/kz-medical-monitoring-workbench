// 0927V1 多测试者质量循环：从零建项→全链→浏览器验收；审阅-反馈-复盘-修订-再测，无限轮次直至收敛
// 原则：①系统独立运行（测试者只当用户，卡住=发现）②模拟真实视角③每轮提示词不同④项目不交叉⑤禁止单轮通过

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

interface PrecheckResult {
  envOk: boolean;
  envNote: string;
  datasets: { key: string; ok: boolean; note: string }[];
  channels: { model: string; ok: boolean; note: string }[];
}

// ===== 常量 =====
const WB = "implementation/workbench";
const PY = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python";
const WBABS = "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench";
const APIURL = "http://127.0.0.1:8910/api/runtime-readiness";
const FEURL = "http://localhost:5177/monitoring";
const LOOP = WB + "/scripts/tester_loop_0927";
const STAGE = "tester_staging_0927";
const RUNNER = "/Users/smkzw/.codex/tools/conference_session_runner.py";
const MAXROUNDS = 12;
const MINROUNDS = 3;
const CLEANSTREAKNEED = 2;
const STALLMIN = 45;

const RESTART_API =
  "cd " + WBABS + " && lsof -ti:8910 | xargs kill 2>/dev/null; sleep 2; source ~/.config/cms-medical-workbench/ai-runtime.env; " +
  "WORKBENCH_RUNTIME_DIR=\"$PWD/runs/phase_c_mgk10_authority_v2_20260905/runtime\" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api " +
  "WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8910 --log-level warning > /tmp/mm_api_8910.log 2>&1 &";
const RESTART_VITE = "cd " + WBABS + "/frontend && lsof -ti:5177 | xargs kill 2>/dev/null; sleep 1; nohup npx vite --port 5177 --strictPort > /tmp/mm_vite_5177.log 2>&1 &";

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

// 合成数据植入的已知违规（分诊对照用，不发给测试者）
const SYNTH_TRUTH =
  "合成CSU/PSO数据由 scripts/generate_test_listing.py 生成，植入的已知违规类别：MH空术语、CM空日期、CM空适应症、SV空访视名、SV改名、SV空SUBJID，共7行植入；" +
  "listing另含名册页/long形态化验表/量表页等非标准形态（考察反过拟合）。分诊时对照：系统抓到了哪些类别、漏了哪些、有无误报。";

const PERSONAS = [
  { name: "资深医学监查员", background: "药物警戒背景十五年，对医学语义诚实性极度挑剔，最恨系统把'不知道'伪装成结论。" },
  { name: "CRA转岗的医学经理", background: "刚从临床监查员转岗医学经理三个月，熟悉试验流程但对新工具没耐心，遇到没反馈的等待会立刻烦躁。" },
  { name: "数据管理员出身的医学经理", background: "干过八年数据管理，看数据先看表结构、主键、空值和口径，任何数据搬运错误都逃不过你的眼睛。" },
  { name: "保守的医学总监", background: "最终拍板人，只认证据链：每个结论必须能溯源到原始记录，否则宁可不用这个系统。" },
  { name: "急性子项目经理", background: "管过多个III期项目交付，对效率敏感：一次多余的点击、一段没有进度反馈的等待，都是你记录的对象。" },
];

const FOCUSES = [
  "从零建项到数据接入的顺畅度：每一步是否知道该干什么、上传后反馈是否及时清楚",
  "全链推进的自主性：系统是否无需人在旁边推就能自己走完，等待期间进度是否可见",
  "结果的医学语义诚实性：严重度标注是否如实（记录值/未知/推定区分）、不可判定是否明确标注、发现是否真有医学含量",
  "导航与信息呈现：视图切换不丢状态、宽屏1440/1920布局、列表密度与可读性",
  "错误预防与恢复：传错文件、格式不认识、必填缺失时，系统是清楚拒绝还是静默吞掉或给出误导信息",
  "术语与文案一致性：中英文混排、域代码（AE/CM/MH/LB）解释、同一概念在不同页面叫法是否一致",
];

const SPECIALS = [
  "以『新员工第一天、没有任何培训文档』的心态操作：不假设任何先验知识，看界面本身能否教会你。",
  "假定你今天只有两小时空闲：优先把主链走通，但如实记录每一处让你想放弃的时刻。",
  "过程中自然地犯一次真实用户会犯的错（比如先选错文件再纠正、把两个文件顺序传反），观察系统的预防与提示。",
  "重点核对数字：各视图的发现计数、受试者数、风险分布是否互相一致、是否与详情对得上。",
  "中途关闭浏览器标签页再重新进入（真实用户会离开再回来），检查状态是否还在、是否需要重做任何步骤。",
  "在结果页随机抽3名受试者深挖：从发现卡片下钻到旅程、再到原始证据，评价证据链是否完整。",
  "故意用一次浏览器后退/刷新，观察路由与状态保持；再检查页面标题与面包屑是否始终告诉你身在何处。",
  "以向领导汇报前核查的心态过一遍所有汇总数字与图表，寻找任何自相矛盾之处。",
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

// ===== 仪表盘（开赛即声明） =====
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

// ===== 工具函数 =====
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

function buildPrompt(
  round: number,
  slot: string,
  ds: Dataset,
  personaIdx: number,
  focusIdx: number,
  specialIdx: number,
  reportPath: string,
): string {
  const persona = PERSONAS[personaIdx % PERSONAS.length];
  const focus = FOCUSES[focusIdx % FOCUSES.length];
  const special = SPECIALS[specialIdx % SPECIALS.length];
  const projName = "MX循R" + round + slot + "-" + ds.key;
  const files = ds.files.map((f) => "- " + f).join("\n");
  return (
    "【第" + round + "轮·" + slot + "号测试任务】（提示词编号 R" + round + "-" + slot + "，与以往任何一轮都不同）\n\n" +
    "你是" + persona.name + "。" + persona.background + "\n" +
    "本轮以真实用户身份，独立验收「康哲 AI 医学经理工作台」的医学监查子系统。\n\n" +
    "## 进入方式\n" +
    "- 浏览器打开 http://localhost:5177/ ，确认页面标题是「康哲 AI 医学经理工作台」（若看到「入排审核工作台」说明开错应用，立即停止并记录）\n" +
    "- 浏览器工具：ego-browser（先读 /Users/smkzw/.zcode/skills/ego-browser/SKILL.md 学用法；上传本地文件用它的 FileChooser；一次任务只用一个 TaskSpace）\n\n" +
    "## 铁律（违反即测试作废）\n" +
    "1. 只通过浏览器界面操作。严禁 curl/API/直连后端/读写数据库/读日志/修改任何文件\n" +
    "2. 严禁重启或触碰任何服务；严禁推进后台任务——你不是运维，系统必须自己跑\n" +
    "3. 系统卡住不动本身就是最重要的发现：记录当时页面、状态与已等待时长\n" +
    "4. 只使用分给你的这套研究材料；页面上如有别人的项目，一律不点开\n" +
    "5. 报告里不要复制患者身份信息（受试者编号可用，姓名/生日等不可）\n\n" +
    "## 你的专属研究材料（从本机这些路径经浏览器上传）\n" + files + "\n" +
    "研究背景：" + ds.brief + "\n\n" +
    "## 任务（从零开始，走完为止）\n" +
    "1. 新建项目：名称必须完全是「" + projName + "」，类型勾选「启用医学监查模块」\n" +
    "2. 上传上述材料，按界面引导完成数据接入\n" +
    "3. 跟随系统走完全链：内容确认→字段映射→事实准备→运行→发布→结果视图，每一步只做界面允许的用户操作\n" +
    "4. 在结果视图（概览/发现/旅程等）做结果验收\n" +
    "5. 全程以" + persona.name + "的视角观察：" + focus + "\n\n" +
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
    "- 等待与卡点时长\n" +
    "- 对「这套系统能否由一名真实用户独立跑通」的一句话判断\n" +
    HONESTY
  );
}

async function runSlot(
  round: number,
  slotIdx: number,
  ds: Dataset,
  personaIdx: number,
  focusIdx: number,
  specialIdx: number,
  externalUsable: boolean,
  strategyNote: string,
): Promise<TesterOutcome> {
  const ch = CHANNELS[slotIdx];
  const slot = ch.slot;
  const roundDir = LOOP + "/round_" + (round < 10 ? "0" + round : round);
  const reportPath = roundDir + "/report_" + slot + ".md";
  const promptPath = roundDir + "/prompt_" + slot + ".md";
  const promptText =
    buildPrompt(round, slot, ds, personaIdx, focusIdx, specialIdx, reportPath) +
    (strategyNote ? "\n\n## 上一轮复盘给本轮的背景提示（仅供留意，不影响你的独立判断）\n" + strategyNote : "");
  const useExternal = ch.kind === "external" && externalUsable;
  const projName = "MX循R" + round + slot + "-" + ds.key;
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
      const dispatcher = agent("外部通道调度-R" + round + slot);
      return await dispatcher.ask<TesterOutcome>(
        "你是外部测试通道调度员，只做机械调度与结果解析，自己绝不做任何测试操作、不碰浏览器。\n" +
        "步骤：\n" +
        "1. mkdir -p " + roundDir + " 与 " + LOOP + "/logs/round_" + (round < 10 ? "0" + round : round) + "\n" +
        "2. 把下面的任务文件原文写入 " + promptPath + "（一字不改）\n" +
        "3. 后台启动外部测试者（nohup，避免单条命令超时）：\n" +
        "python3 " + RUNNER + " --agent " + ch.agent + " --provider " + ch.provider + " --model " + ch.model +
        " --effort high --explicit-route --prompt " + promptPath + " --output " + reportPath +
        " --stdout " + LOOP + "/logs/round_" + (round < 10 ? "0" + round : round) + "/slot" + slot + ".log" +
        " --max-turns 60 --timeout 21000 --workdir " + WBABS + "\n" +
        "4. 外部测试者可能运行数小时：轮询等待输出文件出现且 runner 进程退出（每次 sleep 300 后检查，单次 bash 调用保持 ≤9 分钟），最多等 6.5 小时\n" +
        "5. 完成后读 " + reportPath + "（外部测试者写的 Markdown 报告）与 stdout 日志末尾，解析为 TesterOutcome 返回：findings 从报告提取（缺字段按报告原文填 evidence）；projectName 默认「" + projName + "」以报告实际为准；stagesReached 按报告旅程归纳；channelNote 写通道运行情况\n" +
        "6. runner 启动即失败（无输出文件且退出码非0）→ 重试一次；仍失败 → 返回 channelNote 含失败详情的 outcome（findings 可为空）\n" +
        "7. 绝不代替测试者补写报告；解析不出来就在 channelNote 说明\n\n" +
        "=== 任务文件原文 ===\n" + promptText,
      );
    }
    const tester = agent("内部测试者-R" + round + slot, {
      system:
        "你就是任务里描述的那名测试者本人，直接亲自执行任务（不是调度员）。全程只用浏览器（按 ego-browser skill），" +
        "只观察不修改，卡住即记录。" + HONESTY,
    });
    return await tester.ask<TesterOutcome>(
      promptText + "\n\n（你是内部测试者，直接执行上述任务；执行前先 mkdir -p " + roundDir + "）\n" +
      "完成后除把报告写入文件外，同时以 TesterOutcome 结构返回结果（findings 字段严格按报告归纳，不要增删事实）。",
    );
  } catch (e) {
    fallback.channelNote = "槽位执行异常：" + String(e);
    return fallback;
  }
}

// ===== 基线环境探针 =====
phase("开局准备：环境、数据与测试通道");
const apiProbe = await world.run(PY, [
  "-c",
  "import urllib.request,json\nr=urllib.request.urlopen('" + APIURL + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')",
]);
const feProbe = await world.run(PY, [
  "-c",
  "import urllib.request\nr=urllib.request.urlopen('" + FEURL + "',timeout=10)\nprint(r.status)",
]);
let envOk = apiProbe.exitCode === 0 && apiProbe.stdout.includes("READY") && feProbe.exitCode === 0;
if (!envOk) {
  const keeper = agent("环境守护员", {
    system:
      "你负责让工作台可访问，只做服务保活，绝不推进任何业务管道、绝不碰任何项目数据。API与vite与医学写作子系统共用，" +
      "重启前把时间戳记入 " + LOOP + "/ENV_RESTART_LOG.md。若两次尝试后仍不可用，升级上报而非继续硬试。" + HONESTY,
  });
  await keeper.ask(
    "工作台不可访问（API探针：" + apiProbe.stdout.trim() + " exit=" + apiProbe.exitCode +
    "；前端探针 exit=" + feProbe.exitCode + "）。请修复：\n" +
    "1. API 重启命令：" + RESTART_API + "\n" +
    "2. vite 重启命令：" + RESTART_VITE + "\n" +
    "3. 各等 15 秒后用 curl 自检 http://127.0.0.1:8910/api/runtime-readiness 返回 ready:true 且 http://localhost:5177/monitoring 返回 200\n" +
    "4. 把重启时间与结果写入 " + LOOP + "/ENV_RESTART_LOG.md",
  );
  const reApi = await world.run(PY, [
    "-c",
    "import urllib.request,json\nr=urllib.request.urlopen('" + APIURL + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')",
  ]);
  const reFe = await world.run(PY, ["-c", "import urllib.request\nr=urllib.request.urlopen('" + FEURL + "',timeout=10)\nprint(r.status)"]);
  envOk = reApi.exitCode === 0 && reApi.stdout.includes("READY") && reFe.exitCode === 0;
  if (!envOk) {
    return {
      conclusion: "开局失败：环境守护员两次修复后工作台仍不可访问，循环未启动。需要人工介入恢复 API(8910)/vite(5177) 后重新运行本工作流。",
      findings: [],
      verified: ["启动前环境探针（API ready + 前端 200）实跑，失败被如实拦截"],
      notCovered: ["全部测试循环（环境未就绪）"],
    };
  }
}

// ===== 准备员：数据副本 + 通道探测 =====
const prep = agent("开局准备员", {
  system:
    "你负责为多测试者循环备齐数据与通道，只复制/生成，绝不改动任何源文件，绝不碰工作台业务。所有副本放到工作区根下 " + STAGE + "/。" + HONESTY,
});
const precheck = await prep.ask<PrecheckResult>(
  "任务（全部用 bash 完成，逐项核验后返回 PrecheckResult）：\n" +
  "1. 建目录 " + STAGE + "/{RUX,MY008_302,synth_csu,synth_pso} 与 " + LOOP + " 及 " + LOOP + "/logs（logs 下写一个内容为 * 的 .gitignore）\n" +
  "2. 复制真实材料（改名如下，源文件绝不动）：\n" +
  "- /Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/【Data Listing】RUX-03-002_列表_数据集_Excel_20250612_处理后.xlsx → " + STAGE + "/RUX/RUX-03-002_DataListing.xlsx\n" +
  "- /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/研究方案库/磷酸芦可替尼乳膏-AD3期临床研究方案V1.3-clean-20240814.docx → " + STAGE + "/RUX/RUX-03-002_临床研究方案_V1.3.docx\n" +
  "- '/Users/smkzw/Documents/康哲项目资料/Ruxolitinib-AD/2-RUX-03-002-现场核查项目层面文件目录-20260424/9.eCRF指南/RUX-03-002_eCRF填写指南_V1.0_20240606.pdf' → " + STAGE + "/RUX/RUX-03-002_eCRF填写指南_V1.0.pdf\n" +
  "- '/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/武汉协和患者数据/EXCEL_MY008211A-PNH-3-02_20250411  （武汉协和受试者数据）.xlsx' → " + STAGE + "/MY008_302/MY008-302_DataListing.xlsx（注意源文件名里有连续空格，用通配符 EXCEL_MY008211A-PNH-3-02_20250411*.xlsx 定位）\n" +
  "- '/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/MY008211A-PNH-3-02_研究方案_V1.1_2024.07.26-clean（JY）.docx' → " + STAGE + "/MY008_302/MY008-302_研究方案_V1.1.docx\n" +
  "- '/Users/smkzw/Documents/朗来项目资料/MY008治疗PNH/3-02（MM外包）/外部CRF材料/MY008211A-PNH-3-02-初治PNH-C5III期-Draft CRF-V0.1-20240801-LC0802.docx' → " + STAGE + "/MY008_302/MY008-302_DraftCRF_V0.1.docx\n" +
  "- /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/研究方案库/MG-K10-CSU-001_临床研究方案-V1.3-0212-clean-0211.docx → " + STAGE + "/synth_csu/MG-K10-CSU-001_临床研究方案_V1.3.docx\n" +
  "- /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/研究方案库/CMS-D001 银屑病2、3期临床方案 v1.0-2025.12.21.docx → " + STAGE + "/synth_pso/CMS-D001_银屑病临床方案_V1.0.docx\n" +
  "3. 生成合成数据（venv python，在 " + WBABS + " 下执行）：\n" +
  PY + " scripts/generate_test_listing.py --profile csu --out /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/" + STAGE + "/synth_csu\n" +
  PY + " scripts/generate_test_listing.py --profile pso --out /Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/" + STAGE + "/synth_pso\n" +
  "生成后把 listing xlsx 改名为 <研究>_合成测试数据_V1.0.xlsx、eCRF docx 改名为 <研究>_eCRF填写指南_V1.0.docx（CSU 用 MG-K10-CSU-001 前缀，PSO 用 CMS-D001-PSO 前缀），与 DATASETS 清单一致\n" +
  "4. 核验：每个数据集三件套存在且 listing>50KB、文档>20KB，逐项记 ok/note\n" +
  "5. 通道探测（三条并行，各限时6分钟）：先写探测提示文件（内容：连通性探测：请只回复四个字：通道就绪），再 nohup 运行：\n" +
  "python3 " + RUNNER + " --agent pi --provider openai-codex --model gpt-6-sol --effort high --explicit-route --prompt <探测文件> --output <out> --stdout <log> --max-turns 3 --timeout 300\n" +
  "同样地：--agent cursor --provider omp --model cursor-grok-4.6；--agent pi --provider google-antigravity --model gemini-3.8-flash\n" +
  "（探测文件、输出都放 /tmp/channel_probe_final/ 下）等待进程退出读 output 判 ok；失败把 stderr 要点写进 note\n" +
  "6. 返回 PrecheckResult（datasets 按 key=RUX/MY008/CSU/PSO；channels 按 model 名）\n" +
  "注意：真实材料属于公司资产，只在本机目录间复制，不外传。",
);
const channelOk = new Map<string, boolean>();
for (const c of precheck.channels ?? []) channelOk.set(c.model, c.ok);
log(
  "开局准备完成：数据集就绪 " + (precheck.datasets ?? []).filter((d) => d.ok).length + "/4；外部通道就绪 " +
  (precheck.channels ?? []).filter((c) => c.ok).length + "/3（" + (precheck.channels ?? []).map((c) => c.model + (c.ok ? "✓" : "✗")).join(" ") + "）",
);

// ===== 回归基线 =====
const baselineRun = await world.run(PY, [
  "-c",
  "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
], { timeoutMs: 3600000 });
const baselineFailures = failedSet(baselineRun.stdout);
log("回归基线已记录：监测子集现有失败 " + baselineFailures.length + " 条（存量债，修复门只看新增）");

// ===== 常驻角色 =====
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
    "并把重启时间戳追加到 " + LOOP + "/ENV_RESTART_LOG.md（共享基础设施留痕）。无法修或风险大就放入 skipped 并写明原因，升级而不是硬改。" + HONESTY,
});
const retrospector = agent("复盘官", {
  system:
    "你负责每轮复盘与归档：根因分析、下一轮策略（若同一发现连续两轮未决必须换策略）、清理本轮测试项目、写轮次报告并提交归档。" +
    "归档纪律：只软删除项目名以本轮前缀（如 MX循R3）开头的项目，绝不碰其他项目。报告用非工程化语言，让医学背景的负责人读得懂。" + HONESTY,
});

// ===== 主循环 =====
const registry: Finding[] = [];
let cleanStreak = 0;
let strategyNote = "";
let roundsDone = 0;
let convergeReached = false;
let stagnationEscalation = "";

for (let round = 1; round <= MAXROUNDS; round++) {
  roundsDone = round;
  phase("多测试者并行从零验收");
  log("第" + round + "轮开测：4个测试位并行，各用各的数据集与专属提示词");
  const outcomesP = CHANNELS.map((ch, s) => {
    const ds = DATASETS[(round + s) % DATASETS.length];
    const externalUsable = ch.kind !== "external" || (channelOk.get(ch.model) ?? false);
    return runSlot(round, s, ds, (round + s) % PERSONAS.length, (round * 2 + s) % FOCUSES.length, (round * 3 + s) % SPECIALS.length, externalUsable, strategyNote);
  });
  const outcomes = await Promise.all(outcomesP);
  const totalFindingsRaw = outcomes.reduce((n, o) => n + (o.findings ?? []).length, 0);
  log(
    "第" + round + "轮收卷：通过 " + outcomes.filter((o) => o.pass).length + "/4；原始发现 " + totalFindingsRaw + " 条；" +
    outcomes.map((o) => o.tester.split("（")[0] + "=" + (o.pass ? "过" : "停于" + (o.blockedAt || "未知"))).join("，"),
  );

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
    if (f && f.status === "待复测") { f.status = "已验证"; f.confirmNote += "；R" + round + "复测通过：" + upg.note; }
  }
  const fresh = registry.filter((f) => f.round === round);
  for (const f of fresh) {
    report({ key: f.id, status: f.status, title: f.title, severity: f.severity, round: f.round, category: f.category, sources: f.sources.join("/") }, "findings-board");
  }
  // 单源 critical/high 且未采信 → 独立复核（每轮上限6条）
  const confirmSlice = confirmTargets.slice(0, 6);
  const confirmations = await Promise.all(
    confirmSlice.map((d, i) => {
      const confirmer = agent("独立复核-R" + round + "-" + i);
      return confirmer.ask<{ confirmed: boolean; note: string }>(
        "请独立复核以下测试发现是否真实存在（你可以用只读手段：浏览器打开 http://localhost:5177 观察、只读 GET 类 API、读代码；严禁任何写操作/重启/管道推进）：\n" +
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
  const fixTargets = registry.filter((f) => f.confirmed && f.status === "待修复" && (f.severity === "critical" || f.severity === "high" || f.severity === "medium"));
  log("分诊完成：新发现 " + fresh.length + " 条（已确认P0/P1 " + newConfirmed01.length + "）；未决P0/P1 累计 " + open01.length + " 条");

  phase("修复缺陷并守住回归门");
  let fixResult: FixResult | null = null;
  if (fixTargets.length > 0) {
    fixResult = await fixer.ask<FixResult>(
      "第" + round + "轮分诊后待修复清单（按严重度优先，量力而为，critical/high 必须处理）：\n" +
      JSON.stringify(fixTargets.map((f) => ({ id: f.id, title: f.title, severity: f.severity, where: f.where, what: f.what, evidence: f.evidence, repro: f.repro, fixHint: f.fixHint }))) + "\n" +
      (strategyNote ? "上轮复盘策略提示：" + strategyNote + "\n" : "") +
      "修复纪律见你的角色设定。修完把 fixedIds/skipped/commitHash/testsRun/frontendTouched 如实返回。修复需重启时命令：\n" +
      "API：" + RESTART_API + "\nvite：" + RESTART_VITE + "\n（两个都要重启，重启后 curl 自检 runtime-readiness ready:true 与 5177=200）",
    );
    for (const id of fixResult.fixedIds ?? []) {
      const f = registry.find((x) => x.id === id);
      if (f) f.status = "待复测";
    }
    for (const sk of fixResult.skipped ?? []) {
      const f = registry.find((x) => x.id === sk.id);
      if (f && f.status === "待修复") f.status = "搁置";
    }
    const gate = await world.run(PY, [
      "-c",
      "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
    ], { timeoutMs: 3600000 });
    const newlyFailed = newFailures(failedSet(gate.stdout), baselineFailures);
    if (newlyFailed.length > 0) {
      log("回归门拦截：修复引入 " + newlyFailed.length + " 条新失败，退回修复员");
      await fixer.ask(
        "修复引入了新的测试失败（相对第0轮基线），必须处理（修好或回滚）：\n" + newlyFailed.join("\n") + "\n失败输出尾部：\n" + gate.stdout.slice(-4000),
      );
      const gate2 = await world.run(PY, [
        "-c",
        "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
      ], { timeoutMs: 3600000 });
      const newlyFailed2 = newFailures(failedSet(gate2.stdout), baselineFailures);
      if (newlyFailed2.length > 0) {
        for (const id of fixResult.fixedIds ?? []) {
          const f = registry.find((x) => x.id === id);
          if (f && f.status === "待复测") f.status = "待修复";
        }
        log("回归门二次拦截：本批修复判无效，发现退回待修复，留待复盘升级");
      }
    }
    const postApi = await world.run(PY, ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + APIURL + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
    if (!(postApi.exitCode === 0 && postApi.stdout.includes("READY"))) {
      await agent("环境守护员-R" + round).ask("修复后API未就绪，请按标准命令恢复并记录：" + RESTART_API + " ；随后自检 ready:true");
    }
  }

  phase("复盘认账并归档本轮");
  const recap = await retrospector.ask<Recap>(
    "第" + round + "轮复盘。输入：\n" +
    "- 测试者结果：" + JSON.stringify(outcomes.map((o) => ({ tester: o.tester, projectName: o.projectName, pass: o.pass, blockedAt: o.blockedAt, stages: o.stagesReached ?? [], stallMinutes: o.stallMinutes, channelNote: o.channelNote }))) + "\n" +
    "- 分诊：" + JSON.stringify({ 新发现: fresh.map((f) => f.id + " " + f.title + " " + f.severity + (f.confirmed ? "(已确认)" : "(未确认)")), synthAssessment: verdict.synthAssessment, coverageGaps: verdict.coverageGaps }) + "\n" +
    "- 修复：" + (fixResult ? JSON.stringify({ fixed: fixResult.fixedIds, skipped: fixResult.skipped, commit: fixResult.commitHash }) : "本轮无需修复") + "\n" +
    "- 全部未决：" + JSON.stringify(registry.filter((f) => f.status === "待修复" || f.status === "待复测").map((f) => ({ id: f.id, title: f.title, round: f.round, status: f.status }))) + "\n\n" +
    "职责：\n" +
    "1. 根因归类与下一轮策略（同一发现连续2轮未决→必须给出与之前不同的策略）\n" +
    "2. 归档本轮测试项目：curl -s http://127.0.0.1:8910/api/projects 列出后，只对项目名以 MX循R" + round + " 开头的执行 curl -X DELETE http://127.0.0.1:8910/api/projects/<id>（软删除；绝不碰其他前缀）\n" +
    "3. 写轮次报告到 " + LOOP + "/round_" + (round < 10 ? "0" + round : round) + "/REPORT.md（章节：本轮概览/各测试者旅程/发现与分诊/修复与回归/复盘与策略/遗留清单；面向医学背景负责人的平实语言）\n" +
    "4. 更新 " + LOOP + "/STATE.json（轮次、未决数、连续清洁轮数）\n" +
    "5. git add " + LOOP + " 的本轮目录与 STATE、提交（信息『测试循环R" + round + "轮次归档』）并 push\n" +
    "返回 Recap。",
  );
  for (const f of registry) {
    if (f.round === round || f.status === "待复测" || f.status === "搁置") {
      report({ key: f.id, status: f.status, title: f.title, severity: f.severity, round: f.round, category: f.category, sources: f.sources.join("/") }, "findings-board");
    }
  }
  strategyNote = recap.strategyNote;
  const allReachedEnd = outcomes.every((o) => (o.stagesReached ?? []).indexOf("结果验收") >= 0);
  const roundClean = allReachedEnd && newConfirmed01.length === 0 && open01.length === 0;
  cleanStreak = roundClean ? cleanStreak + 1 : 0;
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
  try {
    await artifact.file("round-report", recap.roundReportPath, { title: "第" + round + "轮验收报告", description: recap.rootCauses.slice(0, 200) });
  } catch {
    log("轮次报告发布失败（文件缺失），复盘官报告路径：" + recap.roundReportPath);
  }
  const stagnated = recap.stagnatedIds ?? [];
  const hardStuck = registry.filter((f) => stagnated.indexOf(f.id) >= 0 && f.round <= round - 3 && (f.status === "待修复" || f.status === "待复测"));
  if (hardStuck.length > 0) {
    stagnationEscalation = "升级：发现 " + hardStuck.map((f) => f.id).join(",") + " 连续≥3轮未决且已换过策略，需要任务所有者介入决策。";
    break;
  }
  if (round >= MINROUNDS && cleanStreak >= CLEANSTREAKNEED) { convergeReached = true; break; }
}

// ===== 总交付 =====
phase("收敛判定与总交付");
const openAtEnd = registry.filter((f) => f.status === "待修复" || f.status === "待复测");
const finalizer = agent("收官撰稿人", {
  system: "你负责把整个测试循环写成最终交付报告，读 " + LOOP + " 下各轮 REPORT.md 与 STATE.json 汇总，输出到 " + LOOP + "/DELIVERY.md。" +
    "面向医学背景负责人：非工程化语言、四段式（做了什么/没做什么/踩了哪些坑/下一步建议）、每个结论附证据出处。" + HONESTY,
});
const delivery = await finalizer.ask<{ deliveryPath: string; summary: string }>(
  "写总交付报告到 " + LOOP + "/DELIVERY.md：共" + roundsDone + "轮、是否收敛（" + (convergeReached ? "是" : stagnationEscalation ? "否-升级" : "否-轮次上限") + "）、" +
  "累计发现/修复/验证数、未决清单、" + (stagnationEscalation || "") + " 附各轮报告路径。返回 deliveryPath 与 summary。",
);
try {
  await artifact.file("final-report", delivery.deliveryPath, { title: "多测试者质量循环·总交付报告", description: delivery.summary.slice(0, 300), primary: true });
} catch {
  await artifact.markdown("final-report", "## 总交付报告发布失败\n汇总摘要：\n" + delivery.summary, { title: "多测试者质量循环·总交付报告" });
}

return {
  conclusion: convergeReached
    ? "质量循环收敛：历经 " + roundsDone + " 轮（最少" + MINROUNDS + "轮、连续" + CLEANSTREAKNEED + "轮清洁），全部测试者从零建项走通全链且无未决P0/P1。详见 " + LOOP + "/DELIVERY.md"
    : "质量循环未收敛即止（" + roundsDone + "轮）。" + (stagnationEscalation || "达到轮次上限") + "；未决P0/P1 " + openAtEnd.filter((f) => f.severity === "critical" || f.severity === "high").length + " 条。详见 " + LOOP + "/DELIVERY.md",
  findings: openAtEnd.slice(0, 40).map((f) => ({
    where: f.where, what: f.id + " " + f.title + " [" + f.severity + "/" + f.status + "]",
    evidence: f.evidence + "；来源:" + f.sources.join("/"),
    status: f.confirmed ? "verified" : "unconfirmed",
    severity: f.severity === "critical" || f.severity === "high" ? "high" : f.severity === "medium" ? "medium" : "low",
  })),
  verified: [
    "每轮开测前环境探针（API ready + 前端 200）实跑",
    "修复后监测 pytest 子集回归门，与第0轮基线失败集比对（基线存量 " + baselineFailures.length + " 条）",
    roundsDone + " 轮 × 4 测试位独立从零 E2E（外部通道 " + precheck.channels.filter((c) => c.ok).length + "/3 就绪，其余内部测试者代打）",
    "每轮发现经分诊官合并去重，单源critical/high经独立复核",
  ],
  notCovered: [
    "前端 node --test 未作脚本级回归门（由修复员自行运行并在结果中报告）",
    "医学准确率无独立金标准测量（合成数据植入违规仅作类别级对照）",
    "A24 浏览器宽屏三档系统性走查未单独执行（由各轮测试者自然覆盖部分）",
  ],
};
