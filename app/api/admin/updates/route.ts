import {requireAdmin} from "@/lib/admin-auth";

const allowed=new Set(["ad_master","pv","clicks","cv"]);

export async function POST(request:Request){
  const denied=requireAdmin(request);if(denied)return denied;
  try{
    const body=await request.json() as {mode?:string;targets?:string[];startDate?:string;endDate?:string};
    const targets=body.mode==="all"?["all"]:Array.isArray(body.targets)?[...new Set(body.targets)]:[];
    if(!targets.length||(targets[0]!=="all"&&targets.some(value=>!allowed.has(value))))return Response.json({error:"更新対象が不正です"},{status:400});
    if(targets.some(value=>value!=="ad_master")){
      const start=new Date(`${body.startDate}T00:00:00Z`),end=new Date(`${body.endDate}T00:00:00Z`),yesterday=new Date();yesterday.setUTCHours(0,0,0,0);yesterday.setUTCDate(yesterday.getUTCDate()-1);
      const days=(end.getTime()-start.getTime())/86400000+1;
      if(!body.startDate||!body.endDate||Number.isNaN(start.getTime())||Number.isNaN(end.getTime())||start.toISOString().slice(0,10)!==body.startDate||end.toISOString().slice(0,10)!==body.endDate||days<1||days>62||end>yesterday)return Response.json({error:"更新期間は昨日までの62日以内で指定してください"},{status:400});
    }
    const token=process.env.GITHUB_ACTIONS_TOKEN;
    if(!token)return Response.json({error:"VercelにGITHUB_ACTIONS_TOKENを登録してください"},{status:503});
    const response=await fetch("https://api.github.com/repos/tsubasapentagon/Ad-media/actions/workflows/daily-sync.yml/dispatches",{
      method:"POST",headers:{Authorization:`Bearer ${token}`,Accept:"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json"},
      body:JSON.stringify({ref:"main",inputs:{sync_targets:targets.join(","),start_date:body.startDate??"",end_date:body.endDate??""}}),
    });
    if(!response.ok)return Response.json({error:"更新処理を開始できませんでした"},{status:502});
    return Response.json({ok:true});
  }catch{return Response.json({error:"更新内容を確認できませんでした"},{status:400})}
}
