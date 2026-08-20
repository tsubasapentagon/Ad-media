"use client";

import { useMemo, useState } from "react";
import { demoRows, formatRate, mediaLabels, rate, type MediaKey } from "@/lib/dashboard";

type MediaFilter = "all" | MediaKey;
type IconName = "dashboard" | "weekly" | "ads" | "category" | "log" | "users";

const logo: Record<MediaKey, string> = { digmedia:"/digmedia-logo.png", market:"/shukatsu-logo.png", venture:"/venture-logo.png" };
const weeks = [
  ["6/29",2631,381],["7/6",2852,406],["7/13",2720,421],["7/20",3098,439],
  ["7/27",3224,481],["8/3",3012,468],["8/10",3478,518],["8/17",3622,609],
] as const;

function Icon({ name }: { name: IconName }) {
  const paths: Record<IconName, React.ReactNode> = {
    dashboard:<><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></>,
    weekly:<><path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/></>,
    ads:<><path d="M4 5h16v14H4zM8 9h8M8 13h5"/></>,
    category:<><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/></>,
    log:<><path d="M12 8v5l3 2M21 12a9 9 0 1 1-3-6.7M21 4v6h-6"/></>,
    users:<><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 20c0-4 2-6 6-6s6 2 6 6M15 15c4 0 6 2 6 5"/></>,
  };
  return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>;
}

function Sidebar() {
  const nav = [
    ["dashboard","概要","dashboard"],["weekly","週次分析","weekly"],["ads","広告一覧","ads"],
    ["category","カテゴリ設定","settings"],["log","更新ログ","logs"],["users","ユーザー権限","settings"],
  ] as const;
  return <aside className="sidebar"><div className="brand"><span>K</span><strong>小林広告分析 <small>ver.2</small></strong></div><nav aria-label="主なメニュー">
    {nav.map(([icon,label,target],i)=><button key={label} className={i===0?"active":""} onClick={()=>document.getElementById(target)?.scrollIntoView({behavior:"smooth"})}><Icon name={icon}/><span>{label}</span></button>)}
  </nav><div className="sidebar-status"><i/>正常<span>次回 9:00</span></div></aside>;
}

export function Dashboard() {
  const [media,setMedia] = useState<MediaFilter>("all");
  const [category,setCategory] = useState("all");
  const [subcategory,setSubcategory] = useState("all");
  const [placement,setPlacement] = useState("all");
  const [grad,setGrad] = useState("28卒");
  const [search,setSearch] = useState("");
  const categories = useMemo(()=>[...new Set(demoRows.filter(r=>media==="all"||r.media===media).map(r=>r.category))],[media]);
  const subcategories = useMemo(()=>[...new Set(demoRows.filter(r=>(media==="all"||r.media===media)&&(category==="all"||r.category===category)).map(r=>r.subcategory))],[media,category]);
  const placements = [...new Set(demoRows.map(r=>r.placement))];
  const data = useMemo(()=>demoRows.filter(r=>(media==="all"||r.media===media)&&(category==="all"||r.category===category)&&(subcategory==="all"||r.subcategory===subcategory)&&(placement==="all"||r.placement===placement)&&(!search||`${r.id} ${r.placement} ${r.destination} ${r.comment}`.toLowerCase().includes(search.toLowerCase()))).sort((a,b)=>a.placement.localeCompare(b.placement,"ja")||b.device.localeCompare(a.device)),[media,category,subcategory,placement,search]);
  const totals = data.reduce((a,r)=>({imp:a.imp+r.impressions,click:a.click+r.clicks,cv:a.cv+r.cv,grad:a.grad+r.gradCv}),{imp:0,click:0,cv:0,grad:0});
  const kpis = [["表示回数",totals.imp.toLocaleString("ja-JP")],["クリック数",totals.click.toLocaleString("ja-JP")],["CTR",formatRate(rate(totals.click,totals.imp))],["CV数",totals.cv.toLocaleString("ja-JP")],["CVR",formatRate(rate(totals.cv,totals.click))],[`${grad}CV`,totals.grad.toLocaleString("ja-JP")],[`${grad}CV率`,formatRate(rate(totals.grad,totals.cv))]];
  return <div className="app-shell"><Sidebar/><div className="content">
    <section className="filter-panel"><div className="media-tabs"><button className={media==="all"?"active all":""} onClick={()=>setMedia("all")}>全メディア</button>{(Object.keys(mediaLabels) as MediaKey[]).map(key=><button key={key} className={media===key?"active":""} onClick={()=>setMedia(key)}>{/* vinextではnext/imageのクライアント実行に互換性問題があるため固定ロゴはimgを使用 */}<img src={logo[key]} alt={mediaLabels[key]} width="125" height="28"/></button>)}</div><div className="filter-row">
      <label><span>期間</span><select defaultValue="7"><option value="7">直近7日間</option><option>今週（月〜日）</option><option>先週（月〜日）</option><option>今月</option><option>先月</option><option>任意期間</option></select></label>
      <label><span>カテゴリ</span><select value={category} onChange={e=>{setCategory(e.target.value);setSubcategory("all")}}><option value="all">すべて</option>{categories.map(x=><option key={x}>{x}</option>)}</select></label>
      <label><span>小カテゴリ</span><select value={subcategory} onChange={e=>setSubcategory(e.target.value)}><option value="all">すべて</option>{subcategories.map(x=><option key={x}>{x}</option>)}</select></label>
      <label><span>設置場所</span><select value={placement} onChange={e=>setPlacement(e.target.value)}><option value="all">すべて</option>{placements.map(x=><option key={x}>{x}</option>)}</select></label>
      <label><span>注目卒年</span><select value={grad} onChange={e=>setGrad(e.target.value)}><option>28卒</option><option>29卒</option><option>30卒</option></select></label>
      <label className="search"><span>広告を検索</span><input value={search} onChange={e=>setSearch(e.target.value)} placeholder="ID・設置場所・遷移先・コメント"/></label>
    </div></section>
    <main id="dashboard"><header><div><h1>小林広告分析 <small>ver.2</small></h1><p>3メディアの広告実績</p></div><div className="header-actions"><span className="demo">デモデータ</span><span className="updated"><i/>最終更新 8/20 09:04</span><div className="avatar">小</div></div></header>
      <section className="kpi-grid">{kpis.map(([label,value],i)=><article className="kpi" key={label}><span>{label}</span><strong>{value}</strong><small className={i===2?"down":"up"}>{i===2?"-0.2pt":"+8.6%"} <i>前期間比</i></small></article>)}</section>
      <section className="summary-grid"><div className="trend"><div className="section-title"><h2>直近8週間の推移</h2><span><i className="blue"/>クリック <i className="coral"/>CV</span></div><div className="bars">{weeks.map((w,i)=><div className="week" key={w[0]}><div><b style={{height:`${w[1]/42}px`}}/><em style={{height:`${w[2]/7}px`}}/></div><span>{w[0]}</span>{i===7&&<strong>+17.6%</strong>}</div>)}</div></div><aside className="changes"><div className="section-title"><h2>前期間からの変化</h2><span>3件</span></div>{[["見出し5・SP","CV数","+24.8%","up"],["記事中段・PC","CTR","-0.6pt","down"],["ファーストビュー・SP",`${grad}CV率`,"79.0%","up"]].map(x=><div className="change" key={x[0]}><div><b>{x[0]}</b><small>{x[1]}</small></div><strong className={x[3]}>{x[2]}</strong></div>)}</aside></section>
      <PerformanceTable data={data} grad={grad}/>
      <section id="weekly" className="weekly"><div className="section-title"><div><h2>設置場所別・週次分析</h2><p>選択中の条件で、月曜日〜日曜日の実績を比較</p></div><select defaultValue="current"><option value="current">今週</option><option>先週</option><option>2週間前</option><option>3週間前</option></select></div><PerformanceTable data={data} grad={grad} nested/></section>
      <section id="logs" className="log-panel"><div><i/>最終更新は正常に完了しました</div><span>広告 8件・日次集計 56件を更新</span><button>更新履歴を見る</button></section>
      <div id="settings"/>
    </main></div></div>;
}

function PerformanceTable({data,grad,nested=false}:{data:typeof demoRows;grad:string;nested?:boolean}) {
  const table = <div className="table-wrap"><table><thead><tr><th>設置場所 / 広告</th><th>カテゴリ / 小カテゴリ</th><th>端末</th><th>表示回数</th><th>クリック</th><th>CTR</th><th>CV</th><th>CVR</th><th>{grad}CV</th><th>{grad}CV率</th><th>状態</th></tr></thead><tbody>{data.map(r=><tr key={r.id}><td><div className="ad-cell"><i className={`media ${r.media}`}/><div><b>{r.placement}</b><small>{r.id}・{r.comment}</small></div></div></td><td><b>{r.category}</b><small>{r.subcategory}</small></td><td><span className={`device ${r.device.toLowerCase()}`}>{r.device}</span></td><td>{r.impressions.toLocaleString("ja-JP")}</td><td>{r.clicks.toLocaleString("ja-JP")}</td><td><b>{formatRate(rate(r.clicks,r.impressions))}</b></td><td>{r.cv}</td><td><b>{formatRate(rate(r.cv,r.clicks))}</b></td><td>{r.gradCv}</td><td>{formatRate(rate(r.gradCv,r.cv))}</td><td><span className={`status ${r.status==="稼働中"?"live":"ended"}`}>{r.status}</span></td></tr>)}</tbody></table></div>;
  if(nested) return table;
  return <section id="ads" className="table-card"><div className="section-title"><h2>広告パフォーマンス</h2><span>{data.length}件を表示</span></div>{table}</section>;
}
