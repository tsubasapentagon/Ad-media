import { fetchDashboardSnapshot } from "@/lib/supabase-dashboard";
export const dynamic = "force-dynamic";

export async function GET(request:Request){
  const url=new URL(request.url),startDate=url.searchParams.get("startDate")??"",endDate=url.searchParams.get("endDate")??"";
  if(!/^\d{4}-\d{2}-\d{2}$/.test(startDate)||!/^\d{4}-\d{2}-\d{2}$/.test(endDate)) return Response.json({error:"期間が正しくありません"},{status:400});
  if(startDate>endDate) return Response.json({error:"開始日は終了日以前にしてください"},{status:400});
  const offset=Math.max(0,Number(url.searchParams.get("offset")||0));
  const scope=url.searchParams.get("scope");
  const scopePlacement=scope==="standard"?"__standard__":scope==="direct"?"__direct__":scope==="article"?"記事内":undefined;
  const placements=url.searchParams.getAll("placement"),placement=placements.length?`__multi__:${JSON.stringify(placements)}`:scopePlacement;
  try{return Response.json(await fetchDashboardSnapshot({startDate,endDate,media:url.searchParams.get("media")||undefined,category:url.searchParams.get("category")||undefined,subcategory:url.searchParams.get("subcategory")||undefined,placement,search:url.searchParams.get("search")||undefined,limit:100,offset}));}
  catch(error){return Response.json({error:error instanceof Error?error.message:"分析データを取得できませんでした"},{status:500});}
}
