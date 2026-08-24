import { AppFrame } from "./AppFrame";

export function SectionPage({title,description,children}:{title:string;description:string;children?:React.ReactNode}){
  return <AppFrame><main className="standalone-page"><header><div><h1>{title}</h1><p>{description}</p></div><div className="avatar">小</div></header>{children??<section className="coming-card"><span>準備中</span><h2>{title}</h2><p>ページを分離しました。ここへ専用機能を追加していきます。</p></section>}</main></AppFrame>;
}
