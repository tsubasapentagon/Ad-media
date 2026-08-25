import { adminRpc } from "@/lib/admin-dashboard";
import { requireAdmin } from "@/lib/admin-auth";
export const dynamic="force-dynamic";
export async function GET(request:Request){const denied=requireAdmin(request);if(denied)return denied;try{return Response.json(await adminRpc("read_sync_history",{body:{p_limit:50}}))}catch(error){return Response.json({error:error instanceof Error?error.message:"更新ログを取得できませんでした"},{status:500})}}
