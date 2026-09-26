/** Logic-only transcription of selected exports at 872a4514 (turn270file0).
 * Comments/formatting simplified; no production application imported or rendered.
 */
const DAY_MS=24*60*60*1000;
const PRIORITY=Object.freeze({critical:0,high:1,medium:2,low:3});
export function parseTimelineDate(value) {
  if(value===null||value===undefined||value==="")return null;
  const raw=String(value).trim();
  if(/[^\d-]/.test(raw))return null;
  const match=/^(\d{4})-(\d{2})(?:-(\d{2}))?/.exec(raw);
  if(!match)return null;
  const year=Number(match[1]),month=Number(match[2]),day=match[3]?Number(match[3]):1;
  if(!Number.isInteger(year)||month<1||month>12||day<1||day>31)return null;
  const parsed=Date.UTC(year,month-1,day),checked=new Date(parsed);
  if(checked.getUTCFullYear()!==year||checked.getUTCMonth()!==month-1||checked.getUTCDate()!==day)return null;
  return parsed;
}
export function visitAxisDate(visit){
  if(!visit)return null;
  const actual=visit.actual_date??visit.actualDate??null;
  if(actual)return actual;
  const dateState=visit.date_state??visit.dateState??null;
  if(dateState==="missing")return null;
  return visit.nominal_date??visit.nominalDate??null;
}
export function eventIsPendingDate(event){
  if(!event)return true;
  const dateState=event.dateState||event.date_state;
  if(dateState==="missing"||dateState==="conflicted")return true;
  const start=event.start??event.start_date??null;
  if(!start)return true;
  if(event.date_precision==="partial")return true;
  if(parseTimelineDate(start)==null)return true;
  return false;
}
export function eventGeometry(event){
  if(eventIsPendingDate(event))return "pending";
  const start=event.start??event.start_date??null,end=event.end??event.end_date??null;
  if(end&&start&&String(end)!==String(start))return "interval";
  if(event.ongoing===true||event.end_state==="ongoing")return "ongoing";
  if(event.end_state==="unknown"||event.end_unknown===true)return "end_unknown";
  return "point";
}
function pxPerDayForZoom(zoomLevel){if(zoomLevel===-1)return 5;if(zoomLevel===1)return 14;return 8;}
export function buildTimelineScale({windowStart,windowEnd,visits=[],events=[],zoomLevel=0,containerWidth=null}={}){
  const dated=[];
  for(const visit of visits){const ms=parseTimelineDate(visitAxisDate(visit));if(ms!=null)dated.push(ms);}
  for(const event of events){
    if(eventIsPendingDate(event))continue;
    const startMs=parseTimelineDate(event.start??event.start_date),endMs=parseTimelineDate(event.end??event.end_date);
    if(startMs!=null)dated.push(startMs);if(endMs!=null)dated.push(endMs);
  }
  let startMs=parseTimelineDate(windowStart),endMs=parseTimelineDate(windowEnd);
  if(startMs==null&&dated.length)startMs=Math.min(...dated);
  if(endMs==null&&dated.length)endMs=Math.max(...dated);
  const hasValidDates=startMs!=null&&endMs!=null;
  if(startMs==null)startMs=Date.UTC(2026,0,1);
  if(endMs==null||endMs<=startMs)endMs=startMs+30*DAY_MS;
  const spanMs=Math.max(endMs-startMs,DAY_MS),pad=72;
  let pxPerDay=pxPerDayForZoom(zoomLevel),rawContentWidth=Math.ceil(spanMs/DAY_MS)*pxPerDay;
  let width=Math.max(640,rawContentWidth+pad*2);
  if(zoomLevel===0&&typeof containerWidth==="number"&&containerWidth>pad*2+200){
    width=Math.max(640,Math.floor(containerWidth));rawContentWidth=width-pad*2;pxPerDay=rawContentWidth/Math.ceil(spanMs/DAY_MS);
  }
  const contentWidth=width-pad*2;
  function xFor(iso){
    const ms=parseTimelineDate(iso);if(ms==null)return null;
    const clamped=Math.min(Math.max(ms,startMs),endMs),beyond=ms<startMs?"before":ms>endMs?"after":null;
    const x=pad+((clamped-startMs)/spanMs)*contentWidth;
    return beyond?{x,beyond}:x;
  }
  return Object.freeze({windowStartIso:new Date(startMs).toISOString().slice(0,10),windowEndIso:new Date(endMs).toISOString().slice(0,10),startMs,endMs,spanMs,width,pad,contentWidth,pxPerDay,hasValidDates,xFor});
}
function isPriorityRisk(severity){return severity==="critical"||severity==="high"||severity==="medium";}
export function assignLaneStacks(marks,{collisionPx=16}={}){
  const sorted=[...marks].sort((left,right)=>{const dx=(left.x??0)-(right.x??0);if(dx)return dx;return (PRIORITY[left.severity]??9)-(PRIORITY[right.severity]??9);});
  const rows=[];
  return sorted.map(mark=>{
    const width=mark.geometry==="interval"?Math.max(mark.width||0,collisionPx):Math.max(mark.collisionWidth||0,collisionPx);
    const left=mark.geometry==="interval"?mark.x??0:(mark.x??0)-width/2,right=left+width;
    let row=0;while(rows[row]?.some(placed=>!(right<=placed.left||left>=placed.right)))row+=1;
    if(!rows[row])rows[row]=[];rows[row].push({left,right});return {...mark,stackRow:row};
  });
}
export function layoutJourneyTimeline({domains=[],events=[],visits=[],risks=[],pendingDates=[],windowStart=null,windowEnd=null,zoomLevel=0,containerWidth=null}={}){
  const risksByAnchor=new Map(risks.map(risk=>[risk.riskAnchorRef||risk.risk_anchor_ref,risk]));
  const pendingRefSet=new Set(pendingDates.map(item=>typeof item==="string"?item:item?.item_ref||item?.event_ref).filter(Boolean));
  const enriched=events.map(event=>{
    const risk=(event.riskAnchorRefs||event.risk_anchor_refs||[]).map(ref=>risksByAnchor.get(ref)).filter(Boolean).sort((left,right)=>(PRIORITY[left.severity]??9)-(PRIORITY[right.severity]??9))[0]||null;
    return {...event,visitRef:event.visitRef||event.visit_ref||"",risk,severity:risk?.severity||null,geometry:eventGeometry(event)};
  });
  const pendingEvents=enriched.filter(event=>event.geometry==="pending"||pendingRefSet.has(event.eventRef));
  const pendingEventRefs=new Set(pendingEvents.map(event=>event.eventRef));
  const datedEvents=enriched.filter(event=>!pendingEventRefs.has(event.eventRef));
  const positionedVisits=[],pendingVisits=[];
  for(const visit of visits){const iso=visitAxisDate(visit);if(!iso){pendingVisits.push(visit);continue;}positionedVisits.push({visit,iso});}
  const scale=buildTimelineScale({windowStart,windowEnd,visits:positionedVisits.map(item=>item.visit),events:datedEvents,zoomLevel,containerWidth});
  const _x=v=>typeof v==="object"&&v!==null?v.x:v;
  const _beyond=v=>typeof v==="object"&&v!==null?v.beyond:null;
  const visitMarks=positionedVisits.map(({visit,iso})=>{const raw=scale.xFor(iso);return {visitRef:visit.visit_ref||visit.visitRef,iso,x:_x(raw),beyond:_beyond(raw),visit};}).filter(mark=>mark.x!=null);
  const lanes=domains.map(domain=>{
    const domainKey=domain.domain,domainEvents=datedEvents.filter(event=>event.domain===domainKey);
    const priorityEvents=domainEvents.filter(event=>isPriorityRisk(event.severity)),otherEvents=domainEvents.filter(event=>!isPriorityRisk(event.severity));
    const visible=zoomLevel===1?[...domainEvents]:[...priorityEvents],aggregates=[];
    if(zoomLevel!==1){
      const buckets=new Map();
      for(const event of otherEvents){const bucket=String(event.start||event.start_date||"").slice(0,10)||"undated";if(!buckets.has(bucket))buckets.set(bucket,[]);buckets.get(bucket).push(event);}
      for(const [bucket,group] of buckets){
        if(zoomLevel===0&&group.length===1){visible.push(group[0]);continue;}
        const x=scale.xFor(group[0].start||group[0].start_date);if(x==null)continue;
        aggregates.push({aggregateKey:`${domainKey}:${bucket}`,domain:domainKey,count:group.length,x,label:`另有 ${group.length} 条低风险或常规记录`,eventRefs:group.map(event=>event.eventRef)});
      }
    }
    const marks=[];
    for(const event of visible){
      const startIso=event.start||event.start_date,endIso=event.end||event.end_date||startIso,rawX0=scale.xFor(startIso),x0=_x(rawX0);
      if(x0==null)continue;
      const x1=_x(scale.xFor(endIso)),beyond=_beyond(rawX0),geometry=event.geometry;
      const width=geometry==="interval"?Math.max(10,(x1??x0)-x0):0;
      marks.push({eventRef:event.eventRef,domain:domainKey,geometry,x:x0,beyond,width,collisionWidth:event.risk?(zoomLevel===1?220:zoomLevel===0?90:40):(zoomLevel===1?150:24),event,severity:event.severity,risk:event.risk});
    }
    const stacked=assignLaneStacks(marks),maxStack=stacked.reduce((max,mark)=>Math.max(max,mark.stackRow),0),aggregatedCount=aggregates.reduce((sum,item)=>sum+item.count,0);
    return {domain:domainKey,encoding:domain,marks:stacked,aggregates,eventCount:domainEvents.length,riskAnchorCount:domainEvents.reduce((count,event)=>count+(event.riskAnchorRefs?.length||event.risk_anchor_refs?.length||0),0),hiddenLowRiskCount:aggregatedCount,stackRows:Math.max(1,maxStack+1)};
  });
  return Object.freeze({scale,visitMarks,pendingVisits,pendingEvents,pendingDates,lanes,datedEventCount:datedEvents.length,pendingEventCount:pendingEvents.length});
}
