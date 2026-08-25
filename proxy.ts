import { NextRequest, NextResponse } from "next/server";

function sameText(left:string,right:string){if(left.length!==right.length)return false;let difference=0;for(let index=0;index<left.length;index+=1)difference|=left.charCodeAt(index)^right.charCodeAt(index);return difference===0}

export function proxy(request:NextRequest){
  const allowedEmail=process.env.DASHBOARD_LOGIN_EMAIL,allowedPassword=process.env.DASHBOARD_LOGIN_PASSWORD;
  if(!allowedEmail||!allowedPassword)return new NextResponse("ログイン設定がありません",{status:503});
  const authorization=request.headers.get("authorization");
  if(authorization?.startsWith("Basic ")){try{const decoded=atob(authorization.slice(6)),separator=decoded.indexOf(":"),email=decoded.slice(0,separator).toLowerCase(),password=decoded.slice(separator+1);if(separator>0&&sameText(email,allowedEmail.toLowerCase())&&sameText(password,allowedPassword)){const headers=new Headers(request.headers);headers.set("x-dashboard-admin","1");return NextResponse.next({request:{headers}})}}catch{/* Invalid credentials. */}}
  return new NextResponse("ログインしてください",{status:401,headers:{"WWW-Authenticate":'Basic realm="Kobayashi Ad Analytics", charset="UTF-8"'}});
}
export const config={matcher:["/((?!_next/static|_next/image|favicon.svg).*)"]};
