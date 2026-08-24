import { SectionPage } from "../_components/SectionPage";
import { requireChatGPTUser } from "../chatgpt-auth";
export const dynamic="force-dynamic";
export default async function Page(){await requireChatGPTUser("/categories");return <SectionPage title="カテゴリ設定" description="メディアごとのカテゴリを共通カテゴリへ割り当てます"/>}
