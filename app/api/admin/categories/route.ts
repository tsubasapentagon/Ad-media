import { adminRpc } from "@/lib/admin-dashboard";
import { requireAdmin } from "@/lib/admin-auth";
export const dynamic="force-dynamic";

export async function GET(request:Request){const denied=requireAdmin(request);if(denied)return denied;try{return Response.json(await adminRpc("read_category_settings"))}catch(error){return Response.json({error:error instanceof Error?error.message:"カテゴリ設定を取得できませんでした"},{status:500})}}

export async function POST(request:Request){
  const denied=requireAdmin(request);if(denied)return denied;
  try{
    const body=await request.json() as {action?:string;categoryId?:number|null;subcategoryId?:number|null;name?:string;media?:string;originalCategory?:string;originalSubcategory?:string};
    if(!["category","subcategory","mapping"].includes(body.action??""))return Response.json({error:"操作が正しくありません"},{status:400});
    await adminRpc("write_category_setting",{body:{p_action:body.action,p_payload:{category_id:body.categoryId,subcategory_id:body.subcategoryId,name:body.name,media:body.media,original_category:body.originalCategory,original_subcategory:body.originalSubcategory}}});
    return Response.json(await adminRpc("read_category_settings"));
  }catch(error){return Response.json({error:error instanceof Error?error.message:"カテゴリ設定を保存できませんでした"},{status:500})}
}
