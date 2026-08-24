import { SectionPage } from "../_components/SectionPage";
import { requireChatGPTUser } from "../chatgpt-auth";
export const dynamic="force-dynamic";
export default async function Page(){await requireChatGPTUser("/users");return <SectionPage title="ユーザー権限" description="閲覧者と管理者の権限を管理します"/>}
