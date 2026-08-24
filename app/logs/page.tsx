import { SectionPage } from "../_components/SectionPage";
import { requireChatGPTUser } from "../chatgpt-auth";
export const dynamic="force-dynamic";
export default async function Page(){await requireChatGPTUser("/logs");return <SectionPage title="更新ログ" description="毎朝の自動更新と手動更新の結果を確認します"/>}
