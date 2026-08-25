import { SectionPage } from "../_components/SectionPage";
import { CategorySettings } from "./CategorySettings";
export const dynamic="force-dynamic";
export default function Page(){return <SectionPage title="カテゴリ設定" description="メディアごとのカテゴリを共通カテゴリへ割り当てます"><CategorySettings/></SectionPage>}
