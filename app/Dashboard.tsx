"use client";
/* eslint-disable @next/next/no-img-element */

import { useEffect, useMemo, useState } from "react";
import { emptySnapshot, formatRate, mediaLabels, rate, type AdPerformance, type DashboardSnapshot, type MediaKey } from "@/lib/dashboard";
import { AppFrame } from "./_components/AppFrame";

type MediaFilter="all"|MediaKey;
type Period="7"|"4weeks"|"this_week"|"last_week"|"two_weeks"|"three_weeks"|"month"|"last_month"|"custom";
export type DashboardView="overview"|"weekly"|"ads"|"direct"|"article";
const logo:Record<MediaKey,string>={digmedia:"/digmedia-logo.png",market:"/shukatsu-logo.png",venture:"/venture-logo.png"};

function iso(date:Date){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`}
function addDays(date:Date,days:number){const copy=new Date(date);copy.setDate(copy.getDate()+days);return copy}
function rangeFor(period:Period,customStart:string,customEnd:string){
  const today=new Date(),yesterday=addDays(today,-1),day=(today.getDay()+6)%7,monday=addDays(today,-day);
  if(period==="custom") return {startDate:customStart,endDate:customEnd};
  if(period==="4weeks") return {startDate:iso(addDays(monday,-21)),endDate:iso(yesterday)};
  if(period==="this_week") return {startDate:iso(monday>yesterday?yesterday:monday),endDate:iso(yesterday)};
  if(period==="last_week") return {startDate:iso(addDays(monday,-7)),endDate:iso(addDays(monday,-1))};
  if(period==="two_weeks") return {startDate:iso(addDays(monday,-14)),endDate:iso(addDays(monday,-8))};
  if(period==="three_weeks") return {startDate:iso(addDays(monday,-21)),endDate:iso(addDays(monday,-15))};
  if(period==="month"){const first=new Date(today.getFullYear(),today.getMonth(),1);return {startDate:iso(first>yesterday?yesterday:first),endDate:iso(yesterday)}}
  if(period==="last_month") return {startDate:iso(new Date(today.getFullYear(),today.getMonth()-1,1)),endDate:iso(new Date(today.getFullYear(),today.getMonth(),0))};
  return {startDate:iso(addDays(yesterday,-6)),endDate:iso(yesterday)};
}

export function Dashboard({view="overview"}:{view?:DashboardView}){
  const initialPeriod:Period=view==="weekly"?"4weeks":"7",initialRange=rangeFor(initialPeriod,"","");
  const [snapshot,setSnapshot]=useState<DashboardSnapshot>(emptySnapshot),[loading,setLoading]=useState(true),[error,setError]=useState(""),[page,setPage]=useState(0);
  const [media,setMedia]=useState<MediaFilter>("all"),[category,setCategory]=useState("all"),[subcategory,setSubcategory]=useState("all"),[placement,setPlacement]=useState("all"),[search,setSearch]=useState("");
  const [period,setPeriod]=useState<Period>(initialPeriod),[customStart,setCustomStart]=useState(initialRange.startDate),[customEnd,setCustomEnd]=useState(initialRange.endDate);
  useEffect(()=>{const range=rangeFor(period,customStart,customEnd);if(!range.startDate||!range.endDate||range.startDate>range.endDate)return;const controller=new AbortController(),params=new URLSearchParams(range);if(media!=="all")params.set("media",mediaLabels[media]);if(category!=="all")params.set("category",category);if(subcategory!=="all")params.set("subcategory",subcategory);if(placement!=="all")params.set("placement",placement);if(view==="ads")params.set("scope","standard");if(view==="direct")params.set("scope","direct");if(view==="article")params.set("scope","article");if(search.trim())params.set("search",search.trim());params.set("offset",String(page*100));async function load(){setLoading(true);setError("");try{const response=await fetch(`/api/dashboard?${params}`,{signal:controller.signal}),body=await response.json();if(!response.ok)throw new Error(body.error??"取得に失敗しました");setSnapshot(body as DashboardSnapshot)}catch(e){if(e instanceof Error&&e.name!=="AbortError"){setSnapshot(emptySnapshot);setError(e.message)}}finally{setLoading(false)}}void load();return()=>controller.abort()},[media,category,subcategory,placement,period,customStart,customEnd,search,page,view]);
  const data=useMemo(()=>[...snapshot.rows].sort((a,b)=>b.clicks-a.clicks),[snapshot.rows]);
  const t=snapshot.totals,kpis=[["表示回数",t.impressions.toLocaleString("ja-JP")],["クリック数",t.clicks.toLocaleString("ja-JP")],["CTR",formatRate(rate(t.clicks,t.impressions))],["CV数",t.cv.toLocaleString("ja-JP")],["CVR",formatRate(rate(t.cv,t.clicks))],["28卒CV",t.gradCv.toLocaleString("ja-JP")],["28卒CV率",formatRate(rate(t.gradCv,t.cv))]];
  const maxWeekly=Math.max(1,...snapshot.weekly.flatMap(w=>[w.clicks,w.cv]));
  const updated=snapshot.lastUpdated?new Date(snapshot.lastUpdated).toLocaleString("ja-JP",{month:"numeric",day:"numeric",hour:"2-digit",minute:"2-digit"}):"取得中",selectedRange=rangeFor(period,customStart,customEnd),rangeError=selectedRange.startDate>selectedRange.endDate?"開始日は終了日以前にしてください":"";
  const pageTitle=view==="overview"?"広告分析概要":view==="weekly"?"週次分析":view==="direct"?"直L・直LP":view==="article"?"記事内広告":"広告一覧";
  return <AppFrame><section className="filter-panel"><div className="media-tabs"><button className={media==="all"?"active all":""} onClick={()=>{setMedia("all");setCategory("all");setSubcategory("all")}}>全メディア</button>{(Object.keys(mediaLabels) as MediaKey[]).map(key=><button key={key} className={media===key?"active":""} onClick={()=>{setMedia(key);setCategory("all");setSubcategory("all")}}>{/* vinextの固定ロゴは通常のimgで確実に表示する */}<img src={logo[key]} alt={mediaLabels[key]} width="125" height="28"/></button>)}</div><div className="filter-row">
    <label><span>期間</span><select value={period} onChange={e=>setPeriod(e.target.value as Period)}><option value="7">直近7日間</option><option value="4weeks">直近4週間</option><option value="this_week">今週（月〜昨日）</option><option value="last_week">先週（月〜日）</option><option value="two_weeks">2週間前（月〜日）</option><option value="three_weeks">3週間前（月〜日）</option><option value="month">今月</option><option value="last_month">先月</option><option value="custom">任意期間</option></select></label>
    <label><span>カテゴリ</span><select value={category} onChange={e=>{setCategory(e.target.value);setSubcategory("all")}}><option value="all">すべて</option>{snapshot.options.categories.map(x=><option key={x}>{x}</option>)}</select></label>
    <label><span>小カテゴリ</span><select value={subcategory} onChange={e=>setSubcategory(e.target.value)}><option value="all">すべて</option>{snapshot.options.subcategories.map(x=><option key={x}>{x}</option>)}</select></label>
    <label><span>設置場所</span><select value={placement} onChange={e=>setPlacement(e.target.value)}><option value="all">すべて</option>{snapshot.options.placements.map(x=><option key={x}>{x}</option>)}</select></label>
    <label className="search"><span>広告を検索</span><input value={search} onChange={e=>{setSearch(e.target.value);setPage(0)}} placeholder="ID・設置場所・遷移先・コメント"/></label>
  </div>{period==="custom"&&<div className="custom-range"><label>開始日<input type="date" value={customStart} onChange={e=>setCustomStart(e.target.value)}/></label><span>〜</span><label>終了日<input type="date" value={customEnd} onChange={e=>setCustomEnd(e.target.value)}/></label></div>}</section>
  <main id="dashboard"><header><div><h1>{pageTitle}</h1><p>{snapshot.startDate&&`${snapshot.startDate} 〜 ${snapshot.endDate}`}・掲載期間内の広告実績</p></div><div className="header-actions">{loading&&<span className="loading">更新中</span>}<span className="updated"><i/>最終更新 {updated}</span><div className="avatar">小</div></div></header>
  {(error||rangeError)&&<div className="data-error">{error||rangeError}<button onClick={()=>location.reload()}>再読み込み</button></div>}
  {view==="overview"&&<><section className="kpi-grid">{kpis.map(([label,value])=><article className="kpi" key={label}><span>{label}</span><strong>{value}</strong><small>{snapshot.startDate||"接続中"}</small></article>)}</section><section className="summary-grid"><div className="trend"><div className="section-title"><h2>週次推移</h2><span><i className="blue"/>クリック <i className="coral"/>CV</span></div><div className="bars">{snapshot.weekly.length?snapshot.weekly.map(w=><div className="week" key={w.weekStart}><div><b style={{height:`${Math.max(3,w.clicks/maxWeekly*140)}px`}}/><em style={{height:`${Math.max(3,w.cv/maxWeekly*140)}px`}}/></div><span>{new Date(w.weekStart).toLocaleDateString("ja-JP",{month:"numeric",day:"numeric"})}</span></div>):<div className="empty-chart">選択期間の週次データはありません</div>}</div></div><aside className="changes"><div className="section-title"><h2>現在の集計条件</h2></div><div className="condition"><span>対象広告</span><strong>{snapshot.rowCount.toLocaleString("ja-JP")}件</strong></div><div className="condition"><span>卒年</span><strong>28卒</strong></div></aside></section></>}
  {(view==="ads"||view==="direct"||view==="article")&&<PerformanceTable data={data} total={snapshot.rowCount} page={page} onPage={setPage}/>} {view==="weekly"&&<WeeklyAnalysis data={snapshot.placementWeekly}/>} </main></AppFrame>
}

function PerformanceTable({data,total,page,onPage}:{data:AdPerformance[];total:number;page:number;onPage:(page:number)=>void}){const displayDate=(date:string|null)=>date?date.replaceAll("-","/"):"未設定";return <section id="ads" className="table-card"><div className="section-title"><div><h2>広告パフォーマンス</h2><p>選択期間と掲載期間が重なる広告のみ表示</p></div><span>{total.toLocaleString("ja-JP")}件中 {total?`${page*100+1}〜${Math.min((page+1)*100,total)}件`:"0件"}</span></div><div className="table-wrap"><table><thead><tr><th>設置場所 / 広告</th><th>カテゴリ / 小カテゴリ</th><th>端末</th><th>掲載期間</th><th>表示回数</th><th>クリック</th><th>CTR</th><th>CV</th><th>CVR</th><th>28卒CV</th><th>28卒CV率</th><th>状態</th></tr></thead><tbody>{data.map(r=><tr key={`${r.media}-${r.id}`}><td><div className="ad-cell"><i className={`media ${r.media}`}/><div><b>{r.placement||"未設定"}</b><small>{r.id}{r.comment&&`・${r.comment}`}</small></div></div></td><td><b>{r.category}</b><small>{r.subcategory}</small></td><td><span className={`device ${r.device.toLowerCase()}`}>{r.device}</span></td><td><b className="period-cell">{displayDate(r.startDate)}</b><small>〜 {displayDate(r.endDate)}</small></td><td>{r.impressions.toLocaleString("ja-JP")}</td><td>{r.clicks.toLocaleString("ja-JP")}</td><td><b>{formatRate(rate(r.clicks,r.impressions))}</b></td><td>{r.cv}</td><td><b>{formatRate(rate(r.cv,r.clicks))}</b></td><td>{r.gradCv}</td><td>{formatRate(rate(r.gradCv,r.cv))}</td><td><span className={`status ${r.status==="稼働中"?"live":"ended"}`}>{r.status||"未設定"}</span></td></tr>)}</tbody></table></div><div className="pagination"><button disabled={page===0} onClick={()=>onPage(page-1)}>前へ</button><span>{page+1}ページ</span><button disabled={(page+1)*100>=total} onClick={()=>onPage(page+1)}>次へ</button></div></section>}

type WeeklyMetric="impressions"|"clicks"|"ctr"|"cv"|"cvr"|"gradCv"|"gradRate";
type WeeklyTotal={impressions:number;clicks:number;cv:number;gradCv:number};
const weeklyMetrics:[WeeklyMetric,string][]=[["impressions","表示回数"],["clicks","クリック"],["ctr","CTR"],["cv","CV"],["cvr","CVR"],["gradCv","28卒CV"],["gradRate","28卒CV率"]];
function weeklyValue(total:WeeklyTotal,metric:WeeklyMetric){if(metric==="ctr")return rate(total.clicks,total.impressions);if(metric==="cvr")return rate(total.cv,total.clicks);if(metric==="gradRate")return rate(total.gradCv,total.cv);return total[metric]}
function formatWeekly(value:number,metric:WeeklyMetric){return ["ctr","cvr","gradRate"].includes(metric)?formatRate(value):Math.round(value).toLocaleString("ja-JP")}
function headlineOf(value:string){const normalized=value.normalize("NFKC").replace(/\s/g,"");const match=normalized.match(/見出し([12357])/);return match?`見出し${match[1]}`:null}

function WeeklyAnalysis({data}:{data:DashboardSnapshot["placementWeekly"]}){
  const [mode,setMode]=useState<"category"|"headline">("category"),[metric,setMetric]=useState<WeeklyMetric>("clicks");
  const weeks=useMemo(()=>[...new Set(data.map(row=>row.weekStart))].sort(),[data]);
  const grouped=useMemo(()=>{
    const map=new Map<string,Map<string,WeeklyTotal>>();
    for(const row of data){
      const label=mode==="category"?row.category:headlineOf(row.placement);
      if(!label)continue;
      const byWeek=map.get(label)??new Map<string,WeeklyTotal>(),total=byWeek.get(row.weekStart)??{impressions:0,clicks:0,cv:0,gradCv:0};
      total.impressions+=row.impressions;total.clicks+=row.clicks;total.cv+=row.cv;total.gradCv+=row.gradCv;
      byWeek.set(row.weekStart,total);map.set(label,byWeek);
    }
    const headlineOrder=["見出し1","見出し2","見出し3","見出し5","見出し7"];
    return [...map.entries()].sort((a,b)=>mode==="headline"?headlineOrder.indexOf(a[0])-headlineOrder.indexOf(b[0]):weeklyValue(b[1].get(weeks.at(-1)??"")??{impressions:0,clicks:0,cv:0,gradCv:0},metric)-weeklyValue(a[1].get(weeks.at(-1)??"")??{impressions:0,clicks:0,cv:0,gradCv:0},metric));
  },[data,mode,metric,weeks]);
  const max=Math.max(1,...grouped.flatMap(([,values])=>weeks.map(week=>weeklyValue(values.get(week)??{impressions:0,clicks:0,cv:0,gradCv:0},metric))));
  return <section className="weekly-analysis"><div className="weekly-toolbar"><div><h2>週次推移</h2><p>{mode==="category"?"カテゴリごとの数字の動き":"見出し1・2・3・5・7の数字の動き"}を比較</p></div><div className="weekly-mode"><button className={mode==="category"?"active":""} onClick={()=>setMode("category")}>カテゴリ別</button><button className={mode==="headline"?"active":""} onClick={()=>setMode("headline")}>見出し別</button></div><label>指標<select value={metric} onChange={e=>setMetric(e.target.value as WeeklyMetric)}>{weeklyMetrics.map(([value,label])=><option key={value} value={value}>{label}</option>)}</select></label></div>
  <div className="weekly-matrix"><table><thead><tr><th>{mode==="category"?"カテゴリ":"設置場所"}</th>{weeks.map(week=><th key={week}>{new Date(week).toLocaleDateString("ja-JP",{month:"numeric",day:"numeric"})}週</th>)}<th>前週比</th></tr></thead><tbody>{grouped.map(([label,values])=>{const current=weeklyValue(values.get(weeks.at(-1)??"")??{impressions:0,clicks:0,cv:0,gradCv:0},metric),previous=weeklyValue(values.get(weeks.at(-2)??"")??{impressions:0,clicks:0,cv:0,gradCv:0},metric),change=previous?((current-previous)/previous)*100:null;return <tr key={label}><td><b>{label}</b></td>{weeks.map(week=>{const value=weeklyValue(values.get(week)??{impressions:0,clicks:0,cv:0,gradCv:0},metric);return <td key={week}><div className="weekly-number"><span>{formatWeekly(value,metric)}</span><i style={{width:`${Math.max(value?4:0,value/max*100)}%`}}/></div></td>})}<td><span className={change===null?"flat":change>=0?"up":"down"}>{change===null?"—":`${change>=0?"+":""}${change.toFixed(1)}%`}</span></td></tr>})}</tbody></table>{!grouped.length&&<div className="empty-chart">選択条件の週次データはありません</div>}</div></section>
}
