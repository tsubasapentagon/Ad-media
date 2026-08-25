type RpcOptions={method?:"GET"|"POST";body?:unknown};

export async function adminRpc<T>(name:string,options:RpcOptions={}):Promise<T>{
  const url=process.env.SUPABASE_URL,key=process.env.SUPABASE_PUBLISHABLE_KEY,token=process.env.DASHBOARD_API_TOKEN;
  if(!url||!key||!token)throw new Error("管理画面の接続設定がありません");
  const response=await fetch(`${url.replace(/\/$/,"")}/rest/v1/rpc/${name}`,{
    method:options.method??"POST",headers:{apikey:key,"Content-Type":"application/json"},
    body:JSON.stringify({p_access_token:token,...(options.body as object??{})}),cache:"no-store",
  });
  if(!response.ok){const detail=await response.text();throw new Error(`管理データの取得に失敗しました (${response.status}) ${detail.slice(0,180)}`)}
  return response.json() as Promise<T>;
}
