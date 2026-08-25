"use client";
import {useMemo,useState} from "react";

const options=[
  {id:"ad_master",title:"広告マスター",description:"3媒体の広告ID・カテゴリ・設置場所・掲載期間などをスプレッドシートから全件更新します。",items:["広告情報を全件入れ替え","PV・クリック・CV・日別実績は変更しない"]},
  {id:"all",title:"分析データをすべて更新",description:"広告マスターを先に同期し、PV・クリック・CVを取得して広告ID別の日別データまで再計算します。",items:["広告マスターを全件更新","GA4のPVとクリックを再取得","会員登録・LINEのCVを再取得","統合した広告日別データを更新"]},
] as const;
type Target=typeof options[number]["id"];
function iso(date:Date){return date.toISOString().slice(0,10)}

export function UpdateMenu(){
  const yesterday=useMemo(()=>{const d=new Date();d.setDate(d.getDate()-1);return iso(d)},[]),first=useMemo(()=>{const d=new Date();d.setMonth(d.getMonth()-1,1);return iso(d)},[]);
  const [target,setTarget]=useState<Target>("all"),[startDate,setStartDate]=useState(first),[endDate,setEndDate]=useState(yesterday),[loading,setLoading]=useState(false),[message,setMessage]=useState("");
  const selected=options.find(option=>option.id===target)!;
  const run=async()=>{if(!confirm(`${selected.title}を実行しますか？`))return;setLoading(true);setMessage("");try{const response=await fetch("/api/admin/updates",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({target,startDate,endDate})}),json=await response.json();if(!response.ok)throw new Error(json.error);setMessage("更新を開始しました。進行状況は更新ログで確認できます。")}catch(error){setMessage(error instanceof Error?error.message:"更新を開始できませんでした")}finally{setLoading(false)}};
  return <><section className="update-notice"><b>通常は毎朝9時に「すべて更新」されます</b><p>手動更新は、元データを修正した直後や再集計したいときに使います。</p></section><section className="update-menu"><div className="update-targets">{options.map(option=><button key={option.id} className={target===option.id?"active":""} onClick={()=>setTarget(option.id)}><span>{target===option.id?"選択中":"更新対象"}</span><h2>{option.title}</h2><p>{option.description}</p><ul>{option.items.map(item=><li key={item}>{item}</li>)}</ul></button>)}</div><aside className="update-run-card"><span>手動更新</span><h2>{selected.title}</h2>{target!=="ad_master"&&<div className="update-period"><label>開始日<input type="date" value={startDate} max={endDate} onChange={e=>setStartDate(e.target.value)}/></label><label>終了日<input type="date" value={endDate} min={startDate} max={yesterday} onChange={e=>setEndDate(e.target.value)}/></label></div>}<div className="update-impact"><b>この操作で更新されるもの</b>{selected.items.map(item=><p key={item}>✓ {item}</p>)}</div><button className="primary-button" disabled={loading||startDate>endDate} onClick={run}>{loading?"開始しています…":"この内容で更新する"}</button>{message&&<p className="update-message">{message}</p>}<a href="/logs">更新ログを見る →</a></aside></section></>}
