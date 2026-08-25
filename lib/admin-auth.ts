export function requireAdmin(request:Request):Response|null{
  const expectedEmail=process.env.DASHBOARD_LOGIN_EMAIL?.toLowerCase(),expectedPassword=process.env.DASHBOARD_LOGIN_PASSWORD;
  const authorization=request.headers.get("authorization");
  if(!expectedEmail||!expectedPassword||!authorization?.startsWith("Basic "))return Response.json({error:"管理者のみ利用できます"},{status:403});
  try{const decoded=atob(authorization.slice(6)),separator=decoded.indexOf(":"),email=decoded.slice(0,separator).toLowerCase(),password=decoded.slice(separator+1);if(separator>0&&email===expectedEmail&&password===expectedPassword&&request.headers.get("x-dashboard-admin")==="1")return null}catch{/* invalid authorization */}
  return Response.json({error:"管理者のみ利用できます"},{status:403});
}
