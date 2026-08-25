import { SectionPage } from "../_components/SectionPage";
import { UpdateLogs } from "./UpdateLogs";
export const dynamic="force-dynamic";
export default function Page(){return <SectionPage title="更新ログ" description="毎朝の自動更新と手動更新の結果を確認します"><UpdateLogs/></SectionPage>}
