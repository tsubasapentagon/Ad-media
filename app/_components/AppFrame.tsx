"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

type IconName="dashboard"|"weekly"|"ads"|"direct"|"article"|"category"|"update"|"log"|"users";
const nav:[IconName,string,string,boolean][]=[
  ["dashboard","概要","/analysis",false],
  ["weekly","週次分析","/weekly",false],
  ["ads","広告一覧","/ads",false],
  ["direct","直L","/direct",false],
  ["article","記事内","/in-article",false],
  ["category","カテゴリ設定","/categories",true],
  ["update","データ更新","/updates",true],
  ["log","更新ログ","/logs",true],
  ["users","ユーザー権限","/users",true],
];

function Icon({name}:{name:IconName}){const paths:Record<IconName,ReactNode>={dashboard:<><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></>,weekly:<><path d="M4 19V9M10 19V5M16 19v-7M22 19H2"/></>,ads:<><path d="M4 5h16v14H4zM8 9h8M8 13h5"/></>,direct:<><path d="M5 12h12M13 8l4 4-4 4M4 5v14"/></>,article:<><path d="M5 3h14v18H5zM8 7h8M8 11h8M8 15h5"/></>,category:<><path d="M4 4h6v6H4zM14 4h6v6h-6zM4 14h6v6H4zM14 14h6v6h-6z"/></>,update:<><path d="M20 7v5h-5M4 17v-5h5"/><path d="M6.1 8a7 7 0 0 1 11.7-2L20 8M4 16l2.2 2a7 7 0 0 0 11.7-2"/></>,log:<><path d="M12 8v5l3 2M21 12a9 9 0 1 1-3-6.7M21 4v6h-6"/></>,users:<><circle cx="9" cy="8" r="3"/><circle cx="17" cy="9" r="2"/><path d="M3 20c0-4 2-6 6-6s6 2 6 6M15 15c4 0 6 2 6 5"/></>};return <svg viewBox="0 0 24 24" aria-hidden="true">{paths[name]}</svg>}

export function AppFrame({children}:{children:ReactNode}){
  const pathname=usePathname();
  const [account,setAccount]=useState<{email:string;isAdmin:boolean}|null>(null);
  useEffect(()=>{fetch("/api/auth/me").then(response=>response.ok?response.json():null).then(setAccount).catch(()=>setAccount(null))},[]);
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><span>K</span><strong>小林広告分析 <small>ver.2</small></strong></div><nav aria-label="主なメニュー">{nav.filter(([, , ,adminOnly])=>!adminOnly||account?.isAdmin).map(([icon,label,href])=><Link key={href} href={href} className={pathname===href?"active":""}><Icon name={icon}/><span>{label}</span></Link>)}</nav><div className="sidebar-account">{account&&<><span>{account.isAdmin?"管理者":"閲覧者"}</span><small>{account.email}</small></>}<form action="/auth/signout" method="post"><button type="submit">ログアウト</button></form></div><div className="sidebar-status"><i/>正常<span>次回 9:00</span></div></aside><div className="content">{children}</div></div>;
}
