export function requireAdmin(request:Request):Response|null{
  return request.headers.get("x-dashboard-admin")==="1"?null:Response.json({error:"管理者のみ利用できます"},{status:403});
}
