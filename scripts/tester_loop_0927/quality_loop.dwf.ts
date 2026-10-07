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

interface ClarifyResult {
  /** R4-03 口径澄清结论：一句话说明 22 张表数字的来历 */
  verdict: string;
  /** true=漏识别（缺陷）；false=正确剔除（正面证据） */
  isDefect: boolean;
  note: string;
}

interface SeedResult {
  /** 预置的开考项目ID */
  projectId: string;
  /** 各步状态证据摘要 */
  stateNote: string;
  /** 受阻时写清卡点；空=未受阻 */
  blockedNote: string;
}

interface PreflightStage {
  /** 阶段名：建项/上传/文档权威/映射/事实/运行/发布/结果 */
  stage: string;
  ok: boolean;
  seconds: number;
  note: string;
}

interface PreflightAiNode {
  /** AI节点名：文档权威主/文档权威盲核/映射主/映射盲核/裁决/监查分析等 */
  node: string;
  /** 该节点实际路由到的 provider/model（从台账读） */
  providerModel: string;
  ok: boolean;
  note: string;
}

interface PreflightResult {
  /** 端到端全链是否真正跑通（运行完成+发布可用+结果可读） */
  chainOk: boolean;
  /** chainOk=false 时写清卡在哪个阶段、什么现象 */
  blockedAt: string;
  stages: PreflightStage[];
  aiNodes: PreflightAiNode[];
  evidenceNote: string;
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
const MAXROUNDS = 23;
const MINROUNDS = 3;
const CLEANSTREAKNEED = 2;
const STALLMIN = 45;

const RESTART_API =
  "cd " + WBABS + " && lsof -ti:8910 | xargs kill 2>/dev/null; sleep 2; source ~/.config/cms-medical-workbench/ai-runtime.env; " +
  "WORKBENCH_RUNTIME_DIR=\"$PWD/runs/phase_c_mgk10_authority_v2_20260905/runtime\" WORKBENCH_LOCAL_SINGLE_USER=1 WORKBENCH_AI_RUNTIME=api " +
  "WORKBENCH_MONITORING_AI_PARALLELISM=2 nohup .venv/bin/python -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8910 --log-level warning > /tmp/mm_api_8910.log 2>&1 &";
const RESTART_VITE = "cd " + WBABS + "/frontend && lsof -ti:5177 | xargs kill 2>/dev/null; sleep 1; nohup npx vite --port 5177 --strictPort > /tmp/mm_vite_5177.log 2>&1 &";

// ===== 隔离测试环境（R3+）：独立API 8911 + 独立vite 5178，与医学写作舰队共用的 8910/5177 完全隔离 =====
const ISOAPI = "http://127.0.0.1:8911/api/runtime-readiness";
const ISOFE = "http://localhost:5178/monitoring";
const ISORT_ABS = WBABS + "/runs/tester_loop_iso_20260928/runtime";
const ISO_SRC_RT = WBABS + "/runs/phase_c_mgk10_authority_v2_20260905/runtime";
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
  LOOP + "/ISO_ENV_LOG.md。两次尝试仍不可用就如实上报，不要硬试。没做到就直说，不夸大不编造。";

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

// ===== R3+ 视角池（用户0928指令：轮换医学监查/PV/QA/工程师等视角；界面易用性·逻辑性·美观性为必测项） =====
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

function buildPromptIso(round: number, slot: string, ds: Dataset, reportPath: string): string {
  const s = CHANNELS.findIndex((c) => c.slot === slot);
  const persona = PERSONAS_V2[(round + (s < 0 ? 0 : s)) % PERSONAS_V2.length];
  const focus = FOCUSES_V2[(round * 2 + (s < 0 ? 0 : s)) % FOCUSES_V2.length];
  const special = SPECIALS_V2[(round * 3 + (s < 0 ? 0 : s)) % SPECIALS_V2.length];
  const projName = "MX循R" + round + slot + "-" + ds.key;
  const files = ds.files.map((f) => "- " + WBABS + "/" + f).join("\n");
  return (
    "【第" + round + "轮·" + slot + "号测试任务】（提示词编号 R" + round + "-" + slot + "，与以往任何一轮都不同）\n\n" +
    "你是" + persona.name + "。" + persona.background + "\n" +
    "本轮以真实用户身份，独立验收「康哲 AI 医学经理工作台」的医学监查子系统。\n\n" +
    "## 进入方式\n" +
    "- 浏览器打开 http://localhost:5178/ ，确认页面标题是「康哲 AI 医学经理工作台」\n" +
    "- 只准使用 5178 这个入口；若页面打不开、或打开后发现端口/应用不对（例如入排审核工作台或 5177），立即停止并作为发现记录，不要改用其他入口\n" +
    (round >= 8 ? "- 若你的运行环境（如 Trellis 等任务框架）询问「是否创建任务/文件/目录」，一律直接选择不创建，然后继续纯浏览器测试——这是任务所有者预先批准的答案，不需要请示任何人，也不要因此提前收卷\n" : "") +
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
    (round >= 22
      ? "1. 新建项目（新首页流程）：点「新建项目」后会出现**子系统多选卡片**（医学写作/医学监查/入排审核）——**只勾选「医学监查」一张卡**，然后点「前往医学监查配置」；系统会直接跳到医学监查页并弹出**项目配置面板**，在面板里填写：项目名称=「" + projName + "」、试验药物/适应症/研究分期按分给你的研究材料如实填写，点「创建项目」。全程只在医学监查模块内操作：一旦发现自己在医学写作工作区或写作功能页，立即记录为一条导航类发现（【页面】【问题】【证据】），随即返回医学监查模块继续，**绝不在写作模块内执行操作或等待其长任务**\n"
      : round >= 21
        ? "1. 新建项目：名称必须完全是「" + projName + "」，入口必须选「**从零开始**」——**严禁选『导入方案摘要』（那是医学写作模块的入口）**；类型勾选「启用医学监查模块」。全程只在医学监查模块内操作：一旦发现自己在医学写作工作区或写作功能页（方案摘要导入、文档生成、写作任务等），立即记录为一条导航类发现（【页面】【问题】【证据】），随即返回医学监查模块继续，**绝不在写作模块内执行操作或等待其长任务**\n"
        : "1. 新建项目：名称必须完全是「" + projName + "」，类型勾选「启用医学监查模块」\n") +
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

// ===== R5 开考位专属提示词（用户拍板：开赛门槛——接手已备好的项目，从运行监查起步考主考题） =====
function buildPromptSeeded(round: number, slot: string, ds: Dataset, reportPath: string): string {
  const projName = round >= 19 ? "MX循开考-CSU" : "MX循R" + round + slot + "-" + ds.key;
  return (
    "【第" + round + "轮·" + slot + "号测试任务·开考位】（提示词编号 R" + round + "-" + slot + "-开考，与以往任何一轮都不同）\n\n" +
    "你是一线医学监查专员。在中心做过多年 onsite 监查，习惯从受试者旅程逐访视核对，最在意证据链能不能从结论一路点回原始记录。\n" +
    "本轮以真实用户身份，独立验收「康哲 AI 医学经理工作台」的医学监查子系统。与其他三位从零建项的测试者不同：**你接手的是一个已由同事完成全部准备工作的研究项目**（数据已接入、研究文件已核对、字段对应已确认），你的任务是从「开始运行监查」起步，把这套系统最核心的价值考到底。\n\n" +
    "## 进入方式\n" +
    "- 浏览器打开 http://localhost:5178/ ，确认页面标题是「康哲 AI 医学经理工作台」\n" +
    "- 只准使用 5178 这个入口；若页面打不开、或打开后发现端口/应用不对，立即停止并作为发现记录\n" +
    "- 在项目选择器中选择项目「" + projName + "」（如该项目不存在或准备状态不符——例如字段未确认、无法开始运行监查——如实记录，这本身就是本轮最重要的发现，不要自己动手补准备工作）\n" +
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
    (round >= 22
      ? "1. 新建项目（新首页流程）：点「新建项目」后会出现**子系统多选卡片**（医学写作/医学监查/入排审核）——**只勾选「医学监查」一张卡**，然后点「前往医学监查配置」；系统会直接跳到医学监查页并弹出**项目配置面板**，在面板里填写：项目名称=「" + projName + "」、试验药物/适应症/研究分期按分给你的研究材料如实填写，点「创建项目」。全程只在医学监查模块内操作：一旦发现自己在医学写作工作区或写作功能页，立即记录为一条导航类发现（【页面】【问题】【证据】），随即返回医学监查模块继续，**绝不在写作模块内执行操作或等待其长任务**\n"
      : round >= 21
        ? "1. 新建项目：名称必须完全是「" + projName + "」，入口必须选「**从零开始**」——**严禁选『导入方案摘要』（那是医学写作模块的入口）**；类型勾选「启用医学监查模块」。全程只在医学监查模块内操作：一旦发现自己在医学写作工作区或写作功能页（方案摘要导入、文档生成、写作任务等），立即记录为一条导航类发现（【页面】【问题】【证据】），随即返回医学监查模块继续，**绝不在写作模块内执行操作或等待其长任务**\n"
        : "1. 新建项目：名称必须完全是「" + projName + "」，类型勾选「启用医学监查模块」\n") +
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
  seeded: boolean,
): Promise<TesterOutcome> {
  const ch = CHANNELS[slotIdx];
  const slot = ch.slot;
  const roundDir = LOOP + "/round_" + (round < 10 ? "0" + round : round);
  const reportPath = roundDir + "/report_" + slot + ".md";
  const promptPath = roundDir + "/prompt_" + slot + ".md";
  const strategyAppend = strategyNote
    ? "\n\n## 上一轮复盘给本轮的背景提示（仅供留意，不影响你的独立判断）\n" + strategyNote
    : "";
  const promptText =
    round <= 2
      ? buildPrompt(round, slot, ds, personaIdx, focusIdx, specialIdx, reportPath) + strategyAppend
      : seeded
        ? buildPromptSeeded(round, slot, ds, reportPath) + strategyAppend
        : buildPromptIso(round, slot, ds, reportPath) + strategyAppend;
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
    const testerSystem = round <= 2
      ? "你就是任务里描述的那名测试者本人，直接亲自执行任务（不是调度员）。全程只用浏览器（按 ego-browser skill），" +
        "只观察不修改，卡住即记录。" + HONESTY
      : "你就是任务里描述的那名测试者本人，直接亲自执行任务（不是调度员）。全程只用浏览器（按 ego-browser skill，整个任务只用一个 TaskSpace），" +
        "只观察不修改，卡住即记录。报告写完后必须执行任务里的『收尾清理』并如实确认（TaskSpace 用 delete() 关删、临时缓存清除），清理做没做都要说真话。" + HONESTY;
    const tester = agent("内部测试者-R" + round + slot, { system: testerSystem });
    const testerSuffix = round <= 2
      ? "\n\n（你是内部测试者，直接执行上述任务；执行前先 mkdir -p " + roundDir + "）\n" +
        "完成后除把报告写入文件外，同时以 TesterOutcome 结构返回结果（findings 字段严格按报告归纳，不要增删事实）。"
      : "\n\n（你是内部测试者，直接执行上述任务；执行前先 mkdir -p " + roundDir + "）\n" +
        "完成后除把报告写入文件外，同时以 TesterOutcome 结构返回结果（findings 字段严格按报告归纳，不要增删事实）。" +
        "然后完成『收尾清理』，并在返回的 coverageNotes 里注明清理结果。";
    return await tester.ask<TesterOutcome>(promptText + testerSuffix);
  } catch (e) {
    fallback.channelNote = "槽位执行异常：" + String(e);
    return fallback;
  }
}

// ===== 基线环境探针 =====
phase("开局准备：环境、数据与测试通道");
const apiProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
  "-c",
  "import urllib.request,json\nr=urllib.request.urlopen('" + APIURL + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')",
]);
const feProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
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
  const reApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
    "-c",
    "import urllib.request,json\nr=urllib.request.urlopen('" + APIURL + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')",
  ]);
  const reFe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request\nr=urllib.request.urlopen('" + FEURL + "',timeout=10)\nprint(r.status)"]);
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
const baselineRun = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
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
  if (round >= 3) {
    const isoApiProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
      "-c",
      "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')",
    ]);
    const isoFeProbe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
      "-c",
      "import urllib.request\nr=urllib.request.urlopen('" + ISOFE + "',timeout=10)\nprint(r.status)",
    ]);
    let isoOk = isoApiProbe.exitCode === 0 && isoApiProbe.stdout.includes("READY") && isoFeProbe.exitCode === 0;
    if (!isoOk) {
      await agent("隔离环境守护员-R" + round, { system: ISO_GUARD_RULE }).ask(
        "隔离测试环境不可用（API探针：" + isoApiProbe.stdout.trim() + " exit=" + isoApiProbe.exitCode +
        "；前端探针 exit=" + isoFeProbe.exitCode + "）。请恢复：\n" +
        "1. 运行时目录 " + ISORT_ABS + " 已一次性建好通常无需重建；仅当整目录丢失时才从 " + ISO_SRC_RT +
        " 重建（sqlite3 逐库 .backup 复制除 medical_monitoring_ai.sqlite3 外的 *.sqlite3；rsync -a --exclude '*.sqlite3*' --exclude medical_monitoring_r7 复制其余）\n" +
        "2. API重启：" + ISO_RESTART_API + "\n3. vite重启：" + ISO_RESTART_VITE + "\n" +
        "4. 各等15秒自检：http://127.0.0.1:8911/api/runtime-readiness ready:true；http://localhost:5178/monitoring 200；" +
        "http://localhost:5178/runtime-build.json 的 expectedBackendBuildId 与 8911 的 backend_build_id 一致\n" +
        "5. 把时间戳与结果写入 " + LOOP + "/ISO_ENV_LOG.md",
      );
      const reApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
        "-c",
        "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')",
      ]);
      const reFe = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
        "-c",
        "import urllib.request\nr=urllib.request.urlopen('" + ISOFE + "',timeout=10)\nprint(r.status)",
      ]);
      isoOk = reApi.exitCode === 0 && reApi.stdout.includes("READY") && reFe.exitCode === 0;
      if (!isoOk) {
        stagnationEscalation = "升级：隔离测试环境（8911/5178）两次恢复失败，循环在第" + round + "轮前中止，需要人工介入。";
        break;
      }
    }
    log("隔离测试环境就绪（独立API 8911 + 独立vite 5178，写作舰队 8910/5177 不受影响），开始派发");
  }
  if (round === 9) {
    const shelvedPolish = registry.filter((f) => f.status === "待修复" && f.severity === "low");
    for (const f of shelvedPolish) {
      f.status = "搁置";
      f.confirmNote += "；R9分类处置（用户拍板）：纯打磨低级类打包搁置，上线前统一清";
    }
    log("R9分类处置：纯打磨低级类 " + shelvedPolish.length + " 条打包搁置（上线前统一清）");
  }
  if (round >= 8) {
    const reseed = await agent("开考预置守护员-R" + round, {
      system:
        "你负责为本轮开考位（D位）在隔离测试环境上预置「字段映射已确认+facts就绪、界面可开始运行监查」的项目。你是运维/工程师身份，允许且只允许用 API 与脚本操作隔离环境 http://127.0.0.1:8911（严禁碰 8910/5177）。允许为完成预置而修复已定位的产品缺陷（最小修复+重启只动隔离对+留痕 ISO_ENV_LOG.md）。AI 质量门必须自然通过，严禁人为跳过或伪造状态。受阻就如实报，不绕过不造假。",
    }).ask<SeedResult>(
      (round <= 18
        ? "为第" + round + "轮D位开考做准备，目标项目名必须是「MX循R" + round + "D-CSU」（每轮独立命名，本轮测试者提示词指定此名）：\n" +
          "1. 先探障：GET /r7/project/open 若返回 blocked/CORRUPT（症状：界面『暂时无法安全打开此项目』），按既有定位先修复——services/api/app/main.py:4850 附近建项时 _init_monitoring_runtime_dbs 以现行v5 DDL创建 launch_registry.sqlite3 却写入过期v4 marker，schema检验按marker匹配v4形状即 shape_mismatch；修复方向：种子marker改取 launch_registry_contracts 现行 SCHEMA_VERSION，存量隔离库可原地v4→v5升级；修完重启隔离API（只动8911/5178）并自检\n" +
          "2. 创建项目（project_name=MX循R" + round + "D-CSU、indication=慢性自发性荨麻疹、product_name=MG-K10、modules 含 medical_monitoring、idempotency_key 唯一）并上传 implementation/workbench/tester_staging_0927/synth_csu/ 三件套\n"
        : "为D位开考做准备，目标是**常驻开考项目「MX循开考-CSU」**（跨轮持久存在，复盘按轮次前缀归档不会删它——杜绝每轮重种同数据的浪费）：\n" +
          "0. 先查存量：若该项目已存在且 mapping confirmed + facts ready + project/open current，直接返回就绪（stateNote 注明『复用常驻项目』，本轮零重复预置）；仅补齐缺失环节\n" +
          "1. 若需修复项目打不开缺陷沿用既有定位（main.py:4925-4936 种子marker=launch_registry_contracts.SCHEMA_VERSION）；若需新建：project_name=MX循开考-CSU、indication=慢性自发性荨麻疹、product_name=MG-K10、modules 含 medical_monitoring、幂等键唯一，材料=implementation/workbench/tester_staging_0927/synth_csu/ 三件套\n" +
          "2. API序列沿用（scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md + 既有裁决卡决策表幂等驱动），AI质量门自然通过，不跳门不造假\n" +
          "3. 推进至字段映射 confirmed + facts 物化、界面可开始运行监查即停（**不启动监查**——运行启动交给随后的攻坚验证做）\n") +
      "3. API 序列参考 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md 与同目录幂等脚本；推进至字段映射 confirmed + facts 物化，停住\n" +
      "4. 完成后自验并把项目ID与各步状态证据追加到 scripts/tester_loop_0927/R5_SEEDED_PROJECT.md（按轮次分节），返回 {projectId, stateNote, blockedNote}（受阻时 blockedNote 写清卡点）",
    );
    log("R" + round + "开考预置：" + (reseed.blockedNote ? "受阻——" + reseed.blockedNote : "就绪（" + reseed.stateNote + "）"));
  }
  if (round >= 10) {
    phase("全链预检：链路不绿不外派（用户0930指令）");
    let preflightOk = false;
    let preflightBlock = "";
    let tierSkip = false;
    if (round >= 21) {
      preflightOk = true;
      tierSkip = true;
      log("预检与攻坚合并（组织反思二轮）：全链门改由攻坚验证在常驻项目上执行（运行完成→发布→结果可读）；一次性预检项目停用——每轮省约 2-2.5M tokens 与 1.5-6.7 小时；从零路径由测试者旅程覆盖");
    } else if (round >= 19) {
      const tierCheck = await world.run("bash", [
        "-c",
        "M=implementation/workbench/scripts/tester_loop_0927/PREFLIGHT_LAST_GREEN.json; " +
        "if [ -f \"$M\" ]; then LB=$(python3 -c \"import json;print(json.load(open('$M')).get('build_id',''))\" 2>/dev/null); " +
        "CB=$(curl -s --max-time 8 http://127.0.0.1:8911/api/runtime-readiness | python3 -c \"import json,sys;print(json.load(sys.stdin).get('backend_build_id',''))\" 2>/dev/null); " +
        "if [ -n \"$LB\" ] && [ \"$LB\" = \"$CB\" ] && curl -s -o /dev/null --max-time 8 http://127.0.0.1:8911/api/health; then echo QUICK; exit 0; fi; fi; echo FULL",
      ]);
      if (tierCheck.exitCode === 0 && tierCheck.stdout.includes("QUICK")) {
        preflightOk = true;
        tierSkip = true;
        log("预检分级（组织反思落地）：后端代码未变且上次全绿仍有效——本轮快检通过，跳过全链预检（省约1-3小时与百万级tokens）");
      }
    }
    for (let pfAttempt = 1; pfAttempt <= 3 && !preflightOk; pfAttempt++) {
      const pf = await agent("全链预检工程师-R" + round + "-第" + pfAttempt + "次", {
        system:
          "你是全链预检工程师（任务所有者指令：链路端到端跑通之前不派发任何测试者）。你在隔离环境 http://127.0.0.1:8911 上以运维/工程师身份（允许API与脚本，严禁碰 8910/5177）用一次性预检项目把整条链从零真跑一遍，逐阶段计时、逐AI节点核路由。遇到缺陷如实记录卡点——你的职责是证明链路通或不通，不是修复；不许绕过或伪造状态。所有证据写入 scripts/tester_loop_0927/PREFLIGHT_LOG.md（按轮次分节）。",
      }).ask<PreflightResult>(
        "第" + round + "轮全链预检（第" + pfAttempt + "次）。要求：\n" +
        "1. 新建一次性预检项目：project_name=「MX循R" + round + "P-CSU」（P=预检，会被复盘归档），indication=慢性自发性荨麻疹、product_name=MG-K10、modules 含 medical_monitoring、幂等键唯一\n" +
        "2. 用 tester_staging_0927/synth_csu 三件套，按 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md 的API序列把全链跑到底：建项→上传→文档权威→映射确认→facts→**运行监查（必须真正完成，不是创建即算）→发布（必须 available）→结果可读（overview 非空、受试者/发现数>0）**\n" +
        "3. 每个阶段记录 ok/秒数/备注（stages）；已知状态碎片化家族（后端confirmed vs 监查侧unconfirmed）大概率在运行启动处拦截——若命中，把 console/API 双侧状态证据记入 blockedAt\n" +
        "4. 逐个AI节点核路由（aiNodes）：文档权威主+盲核、映射主+盲核、裁决、监查分析——从AI台账（/api/ai/queue 或 sqlite）读各节点实际 provider/model 与终态，确认无作业滞留、无静默失败\n" +
        "5. chainOk 仅当：八阶段全ok 且 运行完成且发布available且结果可读；否则 blockedAt 写清阶段+现象\n" +
        "6. 返回 PreflightResult（stages/aiNodes 全填）。跑完把项目留在原地（归档交给复盘官）。",
      );
      preflightOk = pf.chainOk;
      preflightBlock = pf.blockedAt;
      if (pf.chainOk) {
        log("全链预检通过（第" + pfAttempt + "次）：端到端跑通+AI节点正常，" + pf.evidenceNote);
      } else {
        log("全链预检第" + pfAttempt + "次未通过：" + pf.blockedAt + " ——先修再检，本轮测试者暂不派发");
        await fixer.ask<FixResult>(
          "全链预检拦截（第" + round + "轮第" + pfAttempt + "次，任务所有者指令：链路不通不外派测试者）。请修复以下阻断点后交预检复验：\n" +
          JSON.stringify({ blockedAt: pf.blockedAt, stages: pf.stages, aiNodes: pf.aiNodes }) + "\n" +
          "修复纪律见你的角色设定；最小根因修复+相关pytest+git提交（『测试循环R" + round + "预检:』）；重启只动隔离对（8911/5178）：\nAPI：" + ISO_RESTART_API + "\nvite：" + ISO_RESTART_VITE + "\n返回FixResult。",
        );
      }
    }
    if (!preflightOk) {
      stagnationEscalation = "升级：第" + round + "轮全链预检三次未通过（" + preflightBlock + "）——链路端到端跑通前不派发测试者（用户0930指令），需要任务所有者决策。";
      break;
    }
    if (preflightOk && round >= 19 && !tierSkip) {
      await world.run("bash", [
        "-c",
        "B=$(curl -s --max-time 8 http://127.0.0.1:8911/api/runtime-readiness | python3 -c \"import json,sys;print(json.load(sys.stdin).get('backend_build_id',''))\" 2>/dev/null); " +
        "printf '{\"build_id\":\"%s\",\"round\":" + round + ",\"at\":\"%s\"}\\n' \"$B\" \"$(date -u +%FT%TZ)\" > implementation/workbench/scripts/tester_loop_0927/PREFLIGHT_LAST_GREEN.json && cat implementation/workbench/scripts/tester_loop_0927/PREFLIGHT_LAST_GREEN.json",
      ]);
    }
  }
  let siegeOk = false;
  let siegeBlock = "";
  if (round >= 19) {
    phase("攻坚验证：让常驻项目真正跑通一次监查（组织反思落地）");
    for (let sgAttempt = 1; sgAttempt <= 3 && !siegeOk; sgAttempt++) {
      const sg = await agent("攻坚工程师-R" + round + "-第" + sgAttempt + "次", {
        system:
          "你是运行启动死锁攻坚工程师（工程验证身份，允许API驱动与代码修复——这不是替代测试：测试者在墙破后回归全量轮）。任务：让常驻开考项目「MX循开考-CSU」从『开始运行监查』真正走到运行完成→发布available→结果可读。背景：此墙自R8起10轮未破（8次创建运行全部卡『等待开始』，状态碎片化8证：预置台confirmed vs 界面unconfirmed），而预检在一次性新项目上8连绿——差异就在常驻/预置项目的状态读取路径。工程纪律：最小根因修复+相关pytest+git提交（『测试循环R" + round + "攻坚:』）+重启只动8911/5178；严禁跳门/伪造状态/绕过界面层缺陷不修。证据写入 scripts/tester_loop_0927/SIEGE_LOG.md（按轮分节）。",
      }).ask<PreflightResult>(
        "第" + sgAttempt + "次攻坚：①复现——在「MX循开考-CSU」上发起运行，完整记录从 run-setup/options→workspace/bootstrap→prepare-and-start→progress 每一步的请求/响应/状态与耗时；若被拒或卡『等待开始』，对照同一时刻后端 mapping/facts/project/open 的真实状态，把『两侧口径差』钉到具体代码行；②修复——修复该根因（若属上游门禁矛盾，沿链验证下一道门）；③重验——同项目再走一次到结果可读。返回 PreflightResult（chainOk 仅当运行真完成+发布available+结果可读；blockedAt 写具体卡点与代码行）。若你判断需要更大改动超出最小修复，如实返回并说明。",
      );
      siegeOk = sg.chainOk;
      siegeBlock = sg.blockedAt;
      if (siegeOk) {
        await world.run("bash", [
          "-c",
          "B=$(curl -s --max-time 8 http://127.0.0.1:8911/api/runtime-readiness | python3 -c \"import json,sys;print(json.load(sys.stdin).get('backend_build_id',''))\" 2>/dev/null); " +
          "printf '{\"build_id\":\"%s\",\"round\":" + round + ",\"siege\":true,\"at\":\"%s\"}\\n' \"$B\" \"$(date -u +%FT%TZ)\" > implementation/workbench/scripts/tester_loop_0927/PREFLIGHT_LAST_GREEN.json",
        ]);
        log("攻坚成功（第" + sgAttempt + "次）：常驻项目运行真完成——墙破，恢复全量测试者轮（下一批测试者应能走通运行→发布→结果）");
      } else if (sgAttempt < 3) {
        log("攻坚第" + sgAttempt + "次未破：" + siegeBlock + " ——转修复员攻坚后重验");
        await fixer.ask<FixResult>(
          "攻坚工程师复现并定位的运行启动死锁（第" + round + "轮第" + sgAttempt + "次）请修复：\n" +
          JSON.stringify({ blockedAt: sg.blockedAt, stages: sg.stages, aiNodes: sg.aiNodes }) + "\n" +
          "这是十轮未破的主墙（8次创建0执行+状态碎片化8证）；修复纪律见你的角色设定与任务书⑥；修完相关pytest+提交。返回FixResult。",
        );
      }
    }
    if (!siegeOk) {
      log("攻坚第" + round + "轮三次未破（" + siegeBlock + "）——本轮转工程轮：不派发测试者（避免再花20+小时重复撞已知墙），分诊/修复/复盘照常推进存量");
    }
  }
  if (round === 5) {
    phase("批量修复冲刺：清存量与修病根");
    let sprintBatch = 0;
    while (sprintBatch < 8) {
      const sprintTargets = registry.filter((f) => f.status === "待修复");
      if (sprintTargets.length === 0) break;
      sprintBatch += 1;
      const sr = await fixer.ask<FixResult>(
        "第5轮开考前·批量修复冲刺（第" + sprintBatch + "批）。任务所有者已拍板：授权一次性批修全部存量（含轻微项），不再「量力而为」。\n\n" +
        "剩余待修复 " + sprintTargets.length + " 条。优先级顺序（用户拍板）：\n" +
        "① 病根最优先——后台长任务「不推进、不报错、不超时」（R4四个卡点同源：方案核对45/109分钟挂起、字段识别124字段冻结、字段确认接口409死循环而后台队列实际空闲）。验收标准：CSU合成数据（591行）从导入到字段确认 ≤15分钟自动完成、全程无需人工盯守，用隔离环境实测计时证明。\n" +
        "② R3-09 比对基准失真：安全门不得用系统内部随机流水号（MW-III-xxx/-DRAFT）作为研究编号比对基准。\n" +
        "③ R1 老问题中的中等项（R1-07/08/09/10 与 R1-05 收尾）。\n" +
        "④ 其余按严重度降序；轻微项（文案/标注/布局类）最后打包收尾。\n\n" +
        "清单：\n" + JSON.stringify(sprintTargets.map((f) => ({ id: f.id, title: f.title, severity: f.severity, where: f.where, what: f.what, evidence: f.evidence, repro: f.repro, fixHint: f.fixHint }))) + "\n\n" +
        "每批修完跑相关 pytest 并 git 提交（信息前缀『测试循环R5冲刺:』，不 push）。重启只允许动隔离环境（8911/5178）：\n" +
        "API：" + ISO_RESTART_API + "\nvite：" + ISO_RESTART_VITE + "\n" +
        "（两个都要重启时先双双重启再自检 8911 ready + 5178 200 + 指纹一致；严禁重启或触碰 8910/5177；留痕 ISO_ENV_LOG.md）\n" +
        "skipped 仅允许「修不动需升级」并写明原因，不允许「时间不够」。返回 FixResult。",
      );
      for (const id of sr.fixedIds ?? []) {
        const f = registry.find((x) => x.id === id);
        if (f) f.status = "待复测";
      }
      for (const sk of sr.skipped ?? []) {
        const f = registry.find((x) => x.id === sk.id);
        if (f && f.status === "待修复") f.status = "搁置";
      }
      const sGate = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
        "-c",
        "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
      ], { timeoutMs: 3600000 });
      const sNewly = newFailures(failedSet(sGate.stdout), baselineFailures);
      if (sNewly.length > 0) {
        await fixer.ask("冲刺修复引入新测试失败（相对第0轮基线），必须处理（修好或回滚）：\n" + sNewly.join("\n") + "\n失败输出尾部：\n" + sGate.stdout.slice(-4000));
        const sGate2 = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
          "-c",
          "import os,subprocess,sys\nos.chdir('implementation/workbench')\nr=subprocess.run([sys.executable,'-m','pytest','tests/medical_monitoring','-q','-p','no:cacheprovider'],capture_output=True,text=True)\nsys.stdout.write(r.stdout[-30000:])\nsys.stderr.write(r.stderr[-4000:])\nsys.exit(r.returncode)",
        ], { timeoutMs: 3600000 });
        if (newFailures(failedSet(sGate2.stdout), baselineFailures).length > 0) {
          for (const id of sr.fixedIds ?? []) {
            const f = registry.find((x) => x.id === id);
            if (f && f.status === "待复测") f.status = "待修复";
          }
          log("冲刺第" + sprintBatch + "批回归门二次拦截，本批修复退回待修复");
        }
      }
      log("冲刺第" + sprintBatch + "批完成：修复 " + (sr.fixedIds ?? []).length + " 条，剩余待修复 " + registry.filter((f) => f.status === "待修复").length + " 条");
      if ((sr.fixedIds ?? []).length === 0 && (sr.skipped ?? []).length === 0) {
        log("冲刺批次零进展，提前结束修复交由开赛准备");
        break;
      }
    }
    log("批量修复冲刺收账：剩余待修复 " + registry.filter((f) => f.status === "待修复").length + " 条，搁置 " + registry.filter((f) => f.status === "搁置").length + " 条，待复测 " + registry.filter((f) => f.status === "待复测").length + " 条");

    phase("开赛准备：修测试工具、澄清口径、预置项目");
    await agent("测试工具修理工", {
      system:
        "你负责修复测试派发工具的两个反复发作缺陷（任务所有者已授权的跨系统公共工具小修）。只改指定文件、最小修复、先读代码再动手、修完必须实测验证。向后兼容：绝对路径调用方式行为不得改变。没做到就直说，不夸大不编造。",
    }).ask(
      "修复 /Users/smkzw/.codex/tools/conference_session_runner.py 两个缺陷：\n" +
      "① 路径解析：--prompt/--output/--stdout/--workdir 等收相对路径时解析基座错误，导致外部测试者启动即失败（四轮里四次复发）。应在启动外部会话前把相对路径按 --workdir（若提供）或启动时工作目录解析为绝对路径后再使用。\n" +
      "② 报告覆盖：会话收尾时把 --output 指定的测试者报告文件覆盖成一段收尾消息（前三轮三次发生，靠人工从日志抢救）。收尾消息必须写到独立文件（如 <output>.closing.txt 或 stdout 日志），绝不允许写入 --output 本身。\n" +
      "验证：在临时目录构造一个最小探针任务（提示文件与输出都用相对路径），实际运行一次 runner，证明 ①相对路径正确解析 ②收尾后 --output 内容保持为测试者写入的原文。把改动说明与验证证据写入 implementation/workbench/scripts/tester_loop_0927/TOOL_FIX_20260929.md。",
    );
    const clar = await agent("口径澄清员", {
      system:
        "你负责查清一个数字疑案并按任务所有者拍板落地界面口径说明。只做这一件事；结论必须有代码级与数据级依据；改前端走最小改动并 git 提交（不 push）。查不清就如实说查不清。",
    }).ask<ClarifyResult>(
      "查清第4轮发现 R4-03：同一页面「导入 59 张数据表」vs 字段识别区「已识别 22 张数据表」的口径差（证据：scripts/tester_loop_0927/round_04/report_B.md）。两种可能：22 是正确剔除了代码对照表/名册页等非临床表（反过拟合排除逻辑生效——若是，这是系统泛化能力的第一个正面证据，用户已拍板在界面加口径说明）；或 22 是漏识别（新缺陷，按严重度修复）。\n" +
      "步骤：①读数据导入与字段识别的排除/分类逻辑代码（提示：反过拟合名册排除、表形态分类相关模块）②逐表核对 59-22=37 张表每一张的被排除理由（用 round_04 记录或本地重算）③按结果落地：正确→前端两处数字旁各加一句口径说明（例如「其中 N 张为临床数据表，其余为代码对照表/名册页等辅助表，已按规则排除」）并提交；缺陷→修复或如实登记。\n" +
      "把结论与证据写入 scripts/tester_loop_0927/R4_03_CLARIFY.md，返回 {verdict, isDefect, note}。",
    );
    log("口径澄清（R4-03）：" + clar.verdict + (clar.isDefect ? "——按缺陷处理" : "——排除逻辑方向"));
    const seeder = await agent("开赛门槛预置员", {
      system:
        "你负责在隔离测试环境上为第5轮开考位预置一个「字段映射已确认、可开始运行监查」的项目。你是运维/工程师身份，允许且只允许用 API 与脚本操作隔离环境 http://127.0.0.1:8911（严禁碰 8910/5177）。过程遇到产品缺陷阻断就如实记录并停止——不要绕过或造假，阻断本身就是发现。所有操作留痕。没做到就直说。",
    }).ask<SeedResult>(
      "任务：在隔离环境（API http://127.0.0.1:8911；运行时目录 runs/tester_loop_iso_20260928/runtime；环境说明与启动命令见 scripts/tester_loop_0927/ISO_ENV_LOG.md）预置项目：\n" +
      "1. 创建项目：project_name=「MX循R5D-CSU」、indication=慢性自发性荨麻疹、product_name=MG-K10、modules 含 medical_monitoring、idempotency_key 唯一\n" +
      "2. 上传材料：tester_staging_0927/synth_csu/ 三件套（合成测试数据xlsx+临床研究方案docx+eCRF填写指南docx，绝对路径在 implementation/workbench 下）\n" +
      "3. 以 API 推进全链至「字段映射 confirmed + facts 物化完成、界面可开始运行监查」停住。API 序列参考 scripts/fullchain_sar_rerun_20260926/HANDOFF_SAR_RERUN_20260926.md 与同目录幂等脚本；文档权威与映射的 AI 作业会真实产生（双队列），等待其自然完成，严禁人为跳过质量门或伪造状态。\n" +
      "4. 全链若耗时较长，轮询等待并在 ISO_ENV_LOG.md 留痕（起止时间、作业数）。\n" +
      "5. 完成后自验：字段确认状态=已确认、facts 就绪、无待人工处理项；把项目ID与各步状态证据写入 scripts/tester_loop_0927/R5_SEEDED_PROJECT.md，返回 {projectId, stateNote, blockedNote}（受阻时 blockedNote 写清卡在哪一步、界面/接口现象）。",
    );
    log("开赛门槛预置：" + (seeder.blockedNote ? "受阻——" + seeder.blockedNote : "项目已就绪（" + seeder.stateNote + "）"));
    const postSprintApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + ISOAPI + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
    if (!(postSprintApi.exitCode === 0 && postSprintApi.stdout.includes("READY"))) {
      await agent("隔离环境守护员-R5冲刺后", { system: ISO_GUARD_RULE }).ask("冲刺与预置后隔离API(8911)未就绪，请恢复：" + ISO_RESTART_API + " ；随后自检 ready:true；严禁动 8910/5177");
    }
  }
  let outcomes: TesterOutcome[];
  if (round >= 19 && !siegeOk) {
    const engDir = LOOP + "/round_" + (round < 10 ? "0" + round : round);
    outcomes = CHANNELS.map((ch) => ({
      tester: ch.label,
      channel: "engineering-round",
      reportFile: engDir + "/no-tester-dispatch.md",
      projectName: "-",
      stagesReached: [],
      blockedAt: "攻坚门未过（" + siegeBlock + "），本轮为工程攻坚轮，不派发测试者",
      stallMinutes: 0,
      pass: false,
      findings: [],
      coverageNotes: "",
      channelNote: "工程攻坚轮（组织反思R1005落地：墙未破不外派）",
    }));
    log("第" + round + "轮以工程轮收卷（0/4 派发，攻坚证据见 SIEGE_LOG.md）");
  } else {
    const outcomesP = CHANNELS.map((ch, s) => {
      const seeded = round >= 5 && ch.slot === "D";
      const csuDs = DATASETS.find((x) => x.key === "CSU");
      const ds = seeded && csuDs ? csuDs : DATASETS[(round + s) % DATASETS.length];
      const externalUsable = ch.kind !== "external" || (channelOk.get(ch.model) ?? false);
      return runSlot(round, s, ds, (round + s) % PERSONAS.length, (round * 2 + s) % FOCUSES.length, (round * 3 + s) % SPECIALS.length, externalUsable, strategyNote, seeded);
    });
    outcomes = await Promise.all(outcomesP);
  }
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
    if (f && f.status === "待复测") {
      f.status = "已验证"; f.confirmNote += "；R" + round + "复测通过：" + upg.note;
      if (round >= 8) report({ key: f.id, status: f.status, title: f.title, severity: f.severity, round: f.round, category: f.category, sources: f.sources.join("/") }, "findings-board");
    }
  }
  const fresh = registry.filter((f) => f.round === round);
  if (round >= 8) {
    for (const f of fresh) {
      report({ key: f.id, status: f.status, title: f.title, severity: f.severity, round: f.round, category: f.category, sources: f.sources.join("/") }, "findings-board");
    }
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
  const agedFix = (f: Finding) => round - f.round >= 2;
  const fixTargets = round <= 8
    ? registry.filter((f) => f.confirmed && f.status === "待修复" && (f.severity === "critical" || f.severity === "high" || f.severity === "medium"))
    : registry.filter((f) => f.status === "待修复" && f.severity !== "low" && (f.confirmed || agedFix(f)))
        .sort((a, b) => {
          const rank = (x: Finding) => (x.severity === "critical" ? 0 : x.severity === "high" ? 1 : agedFix(x) ? 2 : 3);
          return rank(a) - rank(b) || b.round - a.round;
        });
  log("分诊完成：新发现 " + fresh.length + " 条（已确认P0/P1 " + newConfirmed01.length + "）；未决P0/P1 累计 " + open01.length + " 条");

  phase("修复缺陷并守住回归门");
  let fixResult: FixResult | null = null;
  if (fixTargets.length > 0) {
    const restartBlock = round <= 2
      ? "修复需重启时命令：\n" +
        "API：" + RESTART_API + "\nvite：" + RESTART_VITE + "\n（两个都要重启，重启后 curl 自检 runtime-readiness ready:true 与 5177=200）"
      : "修复需重启时只允许重启隔离测试环境（与医学写作舰队完全隔离）：\n" +
        "API：" + ISO_RESTART_API + "\nvite：" + ISO_RESTART_VITE + "\n" +
        "（两个都要重启；重启后自检 http://127.0.0.1:8911/api/runtime-readiness ready:true 与 http://localhost:5178/monitoring 200，" +
        "并核对 http://localhost:5178/runtime-build.json 与 8911 的 backend_build_id 一致；" +
        "严禁重启或触碰 8910/5177——那是医学写作舰队正在使用的服务；重启留痕写入 " + LOOP + "/ISO_ENV_LOG.md）";
    fixResult = await fixer.ask<FixResult>(
      (round <= 8
        ? "第" + round + "轮分诊后待修复清单（按严重度优先，量力而为，critical/high 必须处理）：\n"
        : "第" + round + "轮分诊后待修复清单（任务所有者已拍板新机制：①每轮修复配额约 6 条 ②清单中轮龄≥2轮未轮到的条目自动插队、已排在前面 ③critical/high 必须处理 ④纯打磨 low 级已批量搁置不进本清单" + (round >= 10 ? " ⑤R9复盘锁定的『状态碎片化』家族为最高优先——后端已确认(confirmed/ready)与监查侧未确认(unconfirmed)并存，R8/R9双证、R9预置台console 15:00全绿→15:08界面unconfirmed；它是引擎首跑的唯一拦路虎，修通它主考题即开考" : "") + (round >= 13 ? " ⑥任务所有者铁律（10-03）：测试永远以用户视角经界面进行，严禁以直连后端替代测试——界面不可用即修到走通，不得绕行；当前唯一主攻=运行层『等待开始』死锁族（R8/R10/R11/R12 四次创建零执行）及其上游复核死锁，修到测试者能从界面点通『运行→发布→结果』为止 ⑦前端设计语言对齐康哲设计规范（用户10-03指令）：凡触及前端代码，先读 /Users/smkzw/.zcode/skills/kangzhe-design/SKILL.md 及其 design_specs 核心篇（00-authority/01-core/03-typography），以 Liquid Glass 统一材质、字体层级、玻璃卡片、禁彩色边缘装饰条、数据图用 ECharts 等语言为准——原则是功能性优先、美观统一其次、不追求100%遵循（该规范面向演示场景，应用界面只取设计语言精神，不套演示轨规则）；渐进对齐：新改的界面按规范写，存量界面随修复顺手统一，不为美观牺牲可用性；测试者继续把界面美观性/易用性当必测项" : "") + "）：\n") +
      JSON.stringify(fixTargets.map((f) => ({ id: f.id, title: f.title, severity: f.severity, where: f.where, what: f.what, evidence: f.evidence, repro: f.repro, fixHint: f.fixHint }))) + "\n" +
      (strategyNote ? "上轮复盘策略提示：" + strategyNote + "\n" : "") +
      "修复纪律见你的角色设定。修完把 fixedIds/skipped/commitHash/testsRun/frontendTouched 如实返回。" + restartBlock,
    );
    for (const id of fixResult.fixedIds ?? []) {
      const f = registry.find((x) => x.id === id);
      if (f) {
        f.status = "待复测";
        if (round >= 8) report({ key: f.id, status: f.status, title: f.title, severity: f.severity, round: f.round, category: f.category, sources: f.sources.join("/") }, "findings-board");
      }
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
        "修复引入了新的测试失败（相对第0轮基线），必须处理（修好或回滚）：\n" + newlyFailed.join("\n") + "\n失败输出尾部：\n" + gate.stdout.slice(-4000),
      );
      const gate2 = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", [
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
    const postApiUrl = round <= 2 ? APIURL : ISOAPI;
    const postApi = await world.run("/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/.venv/bin/python", ["-c", "import urllib.request,json\nr=urllib.request.urlopen('" + postApiUrl + "',timeout=10)\nd=json.load(r)\nprint('READY' if d.get('ready') else 'NOTREADY')"]);
    if (!(postApi.exitCode === 0 && postApi.stdout.includes("READY"))) {
      await agent("环境守护员-R" + round).ask(
        round <= 2
          ? "修复后API未就绪，请按标准命令恢复并记录：" + RESTART_API + " ；随后自检 ready:true"
          : "修复后隔离API(8911)未就绪，请恢复：" + ISO_RESTART_API + " ；随后自检 ready:true；严禁动 8910/5177",
      );
    }
  }

  phase("复盘认账并归档本轮");
  const projBase = round <= 2 ? "http://127.0.0.1:8910" : "http://127.0.0.1:8911";
  const recap = await retrospector.ask<Recap>(
    "第" + round + "轮复盘。输入：\n" +
    "- 测试者结果：" + JSON.stringify(outcomes.map((o) => ({ tester: o.tester, projectName: o.projectName, pass: o.pass, blockedAt: o.blockedAt, stages: o.stagesReached ?? [], stallMinutes: o.stallMinutes, channelNote: o.channelNote }))) + "\n" +
    "- 分诊：" + JSON.stringify({ 新发现: fresh.map((f) => f.id + " " + f.title + " " + f.severity + (f.confirmed ? "(已确认)" : "(未确认)")), synthAssessment: verdict.synthAssessment, coverageGaps: verdict.coverageGaps }) + "\n" +
    "- 修复：" + (fixResult ? JSON.stringify({ fixed: fixResult.fixedIds, skipped: fixResult.skipped, commit: fixResult.commitHash }) : "本轮无需修复") + "\n" +
    "- 全部未决：" + JSON.stringify(registry.filter((f) => f.status === "待修复" || f.status === "待复测").map((f) => ({ id: f.id, title: f.title, round: f.round, status: f.status }))) + "\n\n" +
    "职责：\n" +
    "1. 根因归类与下一轮策略（同一发现连续2轮未决→必须给出与之前不同的策略）\n" +
    "2. 归档本轮测试项目：curl -s " + projBase + "/api/projects 列出后，只对项目名以 MX循R" + round + " 开头的执行 curl -X DELETE " + projBase + "/api/projects/<id>（软删除；绝不碰其他前缀）\n" +
    (round >= 3 ? "   （本轮起项目API在隔离实例 " + projBase + "；同时核对各测试报告是否含『收尾清理』一节，缺失的在轮次报告里如实注明）\n" : "") +
    "3. 写轮次报告到 " + LOOP + "/round_" + (round < 10 ? "0" + round : round) + "/REPORT.md（章节：本轮概览/各测试者旅程/发现与分诊/修复与回归/复盘与策略/遗留清单；面向医学背景负责人的平实语言）\n" +
    "4. 更新 " + LOOP + "/STATE.json（轮次、未决数、连续清洁轮数）\n" +
    "5. git add " + LOOP + " 的本轮目录与 STATE、提交（信息『测试循环R" + round + "轮次归档』）并 push\n" +
    "返回 Recap。",
  );
  strategyNote = recap.strategyNote;
  const allReachedEnd = outcomes.every((o) => (o.stagesReached ?? []).indexOf("结果验收") >= 0);
  const roundClean = allReachedEnd && newConfirmed01.length === 0 && open01.length === 0;
  cleanStreak = roundClean ? cleanStreak + 1 : 0;
  if (round >= 7) {
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
  }
  try {
    await artifact.file("round-report", recap.roundReportPath, { title: "第" + round + "轮验收报告", description: recap.rootCauses.slice(0, 200) });
  } catch {
    log("轮次报告发布失败（文件缺失），复盘官报告路径：" + recap.roundReportPath);
  }
  const stagnated = recap.stagnatedIds ?? [];
  const hardStuck = registry.filter((f) => stagnated.indexOf(f.id) >= 0 && f.round <= round - 3 && (f.status === "待修复" || (f.status === "待复测" && round <= 4)) && (round <= 9 || f.severity === "critical" || f.severity === "high"));
  if (hardStuck.length > 0 && round >= 10) {
    stagnationEscalation = "升级：发现 " + hardStuck.map((f) => f.id).join(",") + " 连续≥3轮仍未修复（轮龄插队机制也未能解决的最重级问题），需要任务所有者再次决策。";
    break;
  }
  if (round >= MINROUNDS && cleanStreak >= CLEANSTREAKNEED) { convergeReached = true; break; }
}

// ===== 总交付 =====
phase("收敛判定与总交付");
const openAtEnd = registry.filter((f) => f.status === "待修复" || f.status === "待复测");
const finalizer = agent("收官撰稿人", {
  system: "你负责把整个测试循环写成最终交付报告，读 " + LOOP + " 下各轮 REPORT.md 与 STATE.json 汇总（R3起为隔离环境口径，环境记录见 " + LOOP + "/ISO_ENV_LOG.md），输出到 " + LOOP + "/DELIVERY.md。" +
    "面向医学背景负责人：非工程化语言、四段式（做了什么/没做什么/踩了哪些坑/下一步建议）、每个结论附证据出处。" + HONESTY,
});
const delivery = await finalizer.ask<{ deliveryPath: string; summary: string }>(
  "写总交付报告到 " + LOOP + "/DELIVERY.md：共" + roundsDone + "轮、是否收敛（" + (convergeReached ? "是" : stagnationEscalation ? "否-升级" : "否-轮次上限") + "）、" +
  "累计发现/修复/验证数、未决清单、" + (stagnationEscalation || "") + " 附各轮报告路径。返回 deliveryPath 与 summary。",
);
try {
  await artifact.file("final-report", delivery.deliveryPath, { title: "多测试者质量循环·总交付报告", description: delivery.summary.slice(0, 300), primary: true });
} catch {
  await artifact.markdown("final-report-fallback", "## 总交付报告文件发布失败\n汇总摘要：\n" + delivery.summary, { title: "多测试者质量循环·汇总（降级版）" });
}

// ===== 收尾：停隔离测试环境（只动8911/5178，写作舰队8910/5177不受影响） =====
phase("收尾：停隔离测试环境并留痕");
const isoTeardown = await world.run("bash", [
  "-c",
  "lsof -ti:8911 | xargs kill 2>/dev/null; lsof -ti:5178 | xargs kill 2>/dev/null; sleep 2; " +
  "(lsof -ti:8911 >/dev/null 2>&1 && echo '8911_STILL_UP' || echo '8911_down'); " +
  "(lsof -ti:5178 >/dev/null 2>&1 && echo '5178_STILL_UP' || echo '5178_down'); " +
  "echo \"$(date '+%Y-%m-%d %H:%M') 循环收尾：隔离测试环境已停止（运行时目录保留取证）\" >> '" +
  "/Users/smkzw/Documents/康哲项目资料/AI/医学经理工作台/implementation/workbench/scripts/tester_loop_0927/ISO_ENV_LOG.md'",
]);
log("隔离测试环境收尾：" + isoTeardown.stdout.trim().split("\n").join("，"));

// ===== 收尾清理（用户2026-09-30指令：测试素材与运行时用完即清，防磁盘堆积） =====
phase("收尾：清理测试素材与运行时");
const cleanupRun = await world.run("bash", [
  "-c",
  "before=$(df -k / | awk 'NR==2{print $3}')\n" +
  "rm -rf /tmp/tester_channel_probe /tmp/channel_probe_final 2>/dev/null || true\n" +
  "rm -f /tmp/mm_api_8911.log /tmp/mm_vite_5178.log 2>/dev/null || true\n" +
  "find implementation/workbench/scripts/tester_loop_0927/logs -maxdepth 1 -type d -name 'round_*' 2>/dev/null | sort | head -n -3 | xargs rm -rf 2>/dev/null || true\n" +
  "after=$(df -k / | awk 'NR==2{print $3}')\n" +
  "echo \"清理完成，约释放 $(( (before - after) / 1024 )) MB；保留：各轮报告/台账/证据（scripts/tester_loop_0927/round_*与*.md/json/jsonl）与最近三轮过程日志；隔离运行时(tester_loop_iso_20260928)与测试材料(tester_staging_0927)本轮保留——移交单轮制循环v2继续使用，最终清理由v2收敛时执行\"",
]);
log("测试素材清理：" + cleanupRun.stdout.trim());

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
    roundsDone + " 轮 × 4 测试位独立从零 E2E（外部通道 " + (precheck.channels ?? []).filter((c) => c.ok).length + "/3 就绪，其余内部测试者代打）",
    "每轮发现经分诊官合并去重，单源critical/high经独立复核",
    "R3起测试全部跑在隔离环境（独立API 8911 + 独立vite 5178 + 独立运行时副本），与医学写作舰队共用的 8910/5177 全程隔离，环境操作留痕见 ISO_ENV_LOG.md",
    "R3起每轮派发前隔离环境就绪门（API/前端/指纹配对三检），测试者任务含浏览器任务空间与缓存清理纪律",
  ],
  notCovered: [
    "前端 node --test 未作脚本级回归门（由修复员自行运行并在结果中报告）",
    "医学准确率无独立金标准测量（合成数据植入违规仅作类别级对照）",
    "A24 浏览器宽屏三档系统性走查未单独执行（由各轮测试者自然覆盖部分）",
  ],
};
