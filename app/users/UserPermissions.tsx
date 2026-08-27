"use client";

import { useEffect, useMemo, useState } from "react";

type Role = "viewer" | "admin";
type Profile = { user_id:string; email:string; role:Role; created_at:string };
type Data = { users:Profile[]; primaryAdmin:string };

export function UserPermissions() {
  const [data,setData]=useState<Data>({users:[],primaryAdmin:""}),[loading,setLoading]=useState(true),[saving,setSaving]=useState(""),[error,setError]=useState("");
  const load=async()=>{setLoading(true);setError("");try{const response=await fetch("/api/admin/users",{cache:"no-store"}),json=await response.json();if(!response.ok)throw new Error(json.error);setData(json)}catch(e){setError(e instanceof Error?e.message:"ユーザーを取得できませんでした")}finally{setLoading(false)}};
  useEffect(()=>{void (async()=>{try{const response=await fetch("/api/admin/users",{cache:"no-store"}),json=await response.json();if(!response.ok)throw new Error(json.error);setData(json)}catch(e){setError(e instanceof Error?e.message:"ユーザーを取得できませんでした")}finally{setLoading(false)}})()},[]);
  const counts=useMemo(()=>({admin:data.users.filter(user=>user.role==="admin").length,viewer:data.users.filter(user=>user.role==="viewer").length}),[data.users]);
  const update=async(userId:string,role:Role)=>{const current=data.users.find(user=>user.user_id===userId);if(current?.role==="admin"&&role==="viewer"&&!window.confirm(`${current.email}を閲覧者へ変更しますか？`))return;setSaving(userId);setError("");try{const response=await fetch("/api/admin/users",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({userId,role})}),json=await response.json();if(!response.ok)throw new Error(json.error);setData(json)}catch(e){setError(e instanceof Error?e.message:"権限を変更できませんでした")}finally{setSaving("")}};
  return <>{error&&<div className="data-error">{error}<button onClick={load}>再読み込み</button></div>}
    <section className="permission-summary"><div><span>登録ユーザー</span><strong>{data.users.length}</strong></div><div><span>管理者</span><strong>{counts.admin}</strong></div><div><span>閲覧者</span><strong>{counts.viewer}</strong></div></section>
    <section className="admin-card permission-card"><div className="admin-card-title"><div><h2>社内ユーザー</h2><p>初回Googleログイン後に自動で一覧へ追加されます</p></div><button className="quiet-button" onClick={load} disabled={loading}>{loading?"更新中…":"一覧を更新"}</button></div>
      <div className="permission-head"><span>アカウント</span><span>初回ログイン</span><span>権限</span></div>
      <div className="permission-list">{data.users.map(user=><article key={user.user_id}><div className="permission-user"><i>{user.email.slice(0,1).toUpperCase()}</i><div><b>{user.email}</b><small>{user.email===data.primaryAdmin?"メイン管理者":"HR teamアカウント"}</small></div></div><time>{new Date(user.created_at).toLocaleDateString("ja-JP")}</time><div className="role-switch" aria-label={`${user.email}の権限`}><button className={user.role==="viewer"?"active":""} disabled={saving===user.user_id||user.email===data.primaryAdmin} onClick={()=>update(user.user_id,"viewer")}>閲覧者</button><button className={user.role==="admin"?"active admin":""} disabled={saving===user.user_id} onClick={()=>update(user.user_id,"admin")}>管理者</button></div></article>)}{!loading&&!data.users.length&&<div className="empty-admin"><b>ユーザーはまだいません</b><p>会社のGoogleアカウントでログインすると表示されます。</p></div>}</div>
    </section></>;
}
