import { createClient } from "@/lib/supabase/server";
import { isAdminEmail, isCompanyUser } from "@/lib/auth-policy";
export { ADMIN_EMAIL, COMPANY_DOMAIN, isAdminEmail } from "@/lib/auth-policy";

export async function getAuthenticatedUser() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !isCompanyUser(data.user)) return null;
  return data.user;
}

export async function getAuthenticatedProfile() {
  const supabase = await createClient();
  const { data: auth, error } = await supabase.auth.getUser();
  if (error || !isCompanyUser(auth.user)) return null;
  const { data: profile } = await supabase.from("profiles").select("role").eq("user_id", auth.user.id).maybeSingle();
  return { user: auth.user, role: profile?.role === "admin" || isAdminEmail(auth.user.email) ? "admin" as const : "viewer" as const };
}
