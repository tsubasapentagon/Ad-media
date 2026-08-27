import { SectionPage } from "../_components/SectionPage";
import { UserPermissions } from "./UserPermissions";
import { getAuthenticatedProfile } from "@/lib/auth";
import { redirect } from "next/navigation";
export const dynamic="force-dynamic";
export default async function Page(){const profile=await getAuthenticatedProfile();if(profile?.role!=="admin")redirect("/analysis");return <SectionPage title="ユーザー権限" description="社内アカウントの閲覧・管理権限を管理します"><UserPermissions/></SectionPage>}
