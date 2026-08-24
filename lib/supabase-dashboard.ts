import type { AdPerformance, DashboardSnapshot, MediaKey } from "./dashboard";

type RawSnapshot = { rows?:Array<Record<string,unknown>>;totals?:Record<string,unknown>;weekly?:Array<Record<string,unknown>>;placementWeekly?:Array<Record<string,unknown>>;options?:{categories?:string[];subcategories?:string[];placements?:string[]};lastUpdated?:string|null;rowCount?:number;startDate?:string;endDate?:string };
const mediaKeys: Record<string,MediaKey> = { Digmedia:"digmedia","就活市場":"market","ベンチャー就活":"venture","ベンチャー就活ナビ":"venture" };
const number = (value:unknown)=>Number(value ?? 0);

export async function fetchDashboardSnapshot(params:{startDate:string;endDate:string;media?:string;category?:string;subcategory?:string;placement?:string;search?:string;limit?:number;offset?:number}):Promise<DashboardSnapshot>{
  const url=process.env.SUPABASE_URL,key=process.env.SUPABASE_PUBLISHABLE_KEY,accessToken=process.env.DASHBOARD_API_TOKEN;
  if(!url||!key||!accessToken) throw new Error("Supabaseの画面接続設定がありません");
  const endpoint=`${url.replace(/\/$/,"")}/rest/v1/rpc/`,headers={apikey:key,"Content-Type":"application/json"};
  const filters={p_access_token:accessToken,p_start_date:params.startDate,p_end_date:params.endDate,p_media:params.media||null,p_category:params.category||null,p_subcategory:params.subcategory||null,p_placement:params.placement||null,p_graduation_year:2028};
  const [performance,trends]=await Promise.all([
    fetch(`${endpoint}read_dashboard_performance`,{method:"POST",headers,body:JSON.stringify({...filters,p_search:params.search||null,p_limit:params.limit??100,p_offset:params.offset??0}),cache:"no-store"}),
    fetch(`${endpoint}read_dashboard_trends`,{method:"POST",headers,body:JSON.stringify(filters),cache:"no-store"})
  ]);
  if(!performance.ok||!trends.ok) throw new Error(`分析データの取得に失敗しました (${performance.status}/${trends.status})`);
  const raw={...await performance.json(),...await trends.json()} as RawSnapshot;
  const rows:AdPerformance[]=(raw.rows??[]).map(row=>({id:String(row.ad_id??""),media:mediaKeys[String(row.media)]??"digmedia",category:String(row.category??"未設定"),subcategory:String(row.subcategory??"未設定"),placement:String(row.placement??""),destination:String(row.destination??""),comment:String(row.comment??""),device:String(row.device??"不明") as AdPerformance["device"],status:String(row.status??""),startDate:row.start_date?String(row.start_date):null,endDate:row.end_date?String(row.end_date):null,impressions:number(row.impressions),clicks:number(row.clicks),cv:number(row.cv),gradCv:number(row.grad_cv)}));
  return {rows,totals:{impressions:number(raw.totals?.impressions),clicks:number(raw.totals?.clicks),cv:number(raw.totals?.cv),gradCv:number(raw.totals?.gradCv)},weekly:(raw.weekly??[]).map(row=>({weekStart:String(row.week_start),clicks:number(row.clicks),cv:number(row.cv)})),placementWeekly:(raw.placementWeekly??[]).map(row=>({weekStart:String(row.week_start),media:mediaKeys[String(row.media)]??"digmedia",placement:String(row.placement??""),device:String(row.device??"不明") as AdPerformance["device"],category:String(row.category??"未設定"),subcategory:String(row.subcategory??"未設定"),impressions:number(row.impressions),clicks:number(row.clicks),cv:number(row.cv),gradCv:number(row.grad_cv)})),options:{categories:raw.options?.categories??[],subcategories:raw.options?.subcategories??[],placements:raw.options?.placements??[]},lastUpdated:raw.lastUpdated??null,rowCount:number(raw.rowCount),startDate:String(raw.startDate??params.startDate),endDate:String(raw.endDate??params.endDate)};
}
