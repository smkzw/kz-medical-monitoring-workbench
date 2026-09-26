import {pathToFileURL} from 'node:url';
import path from 'node:path';
const repoIndex=process.argv.indexOf('--repo');
const target=repoIndex>=0?path.resolve(process.argv[repoIndex+1],'frontend/src/features/medical-monitoring/medicalMonitoringJourneyTimeline.mjs'):path.resolve(import.meta.dirname,'../source_excerpts/timeline_excerpt.mjs');
const m=await import(pathToFileURL(target));
const out=[];
function record(id,description,observed,healthy){out.push({id,description,observed,criterion_met:healthy,evidence_level:repoIndex>=0?'actual_repo_pure_module':'source_logic_excerpt'});}
const iso=v=>v==null?null:new Date(v).toISOString().slice(0,10);
let v=m.parseTimelineDate('2025-09-UK');record('J01','UK日不补造',iso(v),v===null);
v=m.parseTimelineDate('2025-02-30');record('J02','非法日历日拒绝',iso(v),v===null);
v=m.parseTimelineDate('2025-09');record('J03','仅年月不返回精确日',iso(v),v===null);
v=m.parseTimelineDate('2025-09-01-99');record('J04','仅数字和连字符的非法后缀拒绝',iso(v),v===null);
v=m.eventIsPendingDate({dateState:'partial',start:'2025-09'});record('J05','公开dateState=partial应保留不确定精度',v,v===true);
let s=m.buildTimelineScale({windowStart:'2025-01-01',windowEnd:'2025-12-31',containerWidth:1000});record('J06','常规宿主默认fit已接通',s.width,s.width===1000);
s=m.buildTimelineScale({windowStart:'2025-01-01',windowEnd:'2025-12-31',containerWidth:500});record('J07','有效小绘图区不可被640下限撑大',s.width,s.width<=500);
s=m.buildTimelineScale();record('J08','无有效日期元数据',s.hasValidDates,s.hasValidDates===false);
record('J09','无有效日期不返回可被UI误用的假日期窗',{start:s.windowStartIso,end:s.windowEndIso},!s.windowStartIso&&!s.windowEndIso);
const base={domains:[{domain:'ae'}],windowStart:'2025-01-01',windowEnd:'2025-01-31',containerWidth:1000};
let l=m.layoutJourneyTimeline({...base,events:[{eventRef:'syn-a',domain:'ae',start:'2025-02-02'},{eventRef:'syn-b',domain:'ae',start:'2025-02-02'}]});
const a=l.lanes[0].aggregates[0];record('J10','窗外聚合坐标必须为有限数值',{x:a?.x,css:`${a?.x}px`},Number.isFinite(a?.x));
l=m.layoutJourneyTimeline({...base,events:[{eventRef:'syn-ongoing',domain:'ae',start:'2025-01-05',ongoing:true}]});let mark=l.lanes[0].marks[0];record('J11','持续事件需有持续几何而非零宽点',{geometry:mark.geometry,width:mark.width},mark.geometry==='ongoing'&&mark.width>0);
l=m.layoutJourneyTimeline({...base,visits:[{visit_ref:'syn-invalid-visit',actual_date:'2025-02-30'}]});record('J12','非法访视不得从可访问集合消失',{positioned:l.visitMarks.length,pending:l.pendingVisits.length},l.visitMarks.length+l.pendingVisits.length===1);
l=m.layoutJourneyTimeline({...base,events:[{eventRef:'syn-partial',domain:'ae',start:'2025-01-UK'}]});record('J13','无日期事件仍在pending集合',l.pendingEvents.map(e=>e.eventRef),l.pendingEvents.some(e=>e.eventRef==='syn-partial'));
// J14已退役（E1，20260927）：原为记录器形态探针——在探针文件内转录
// Workspace.jsx的聚合展开/收起布尔表达式并断言其缺陷，不触达实际实现。
// 该判定已提取为真实模块函数 medicalMonitoringJourneyTimeline.mjs::
// isAggregateExpanded，直接回归见 tests/test_mm_r27_probe_retirement_and_worklist.py
// （node导入真实模块验证：选中联动自动展开、显式收起优先、用户展开保持）。
console.log(JSON.stringify({suite:'timeline_excerpt_probes',target,scope:'No browser/production API. J14 retired (E1): recorder-form JSX expression probe replaced by a direct regression on the real module function isAggregateExpanded.',results:out},null,2));
