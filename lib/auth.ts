import { createClient } from "@/lib/supabase/server";
import { isCompanyUser } from "@/lib/auth-policy";
export { ADMIN_EMAIL, COMPANY_DOMAIN, isAdminEmail } from "@/lib/auth-policy";

export async function getAuthenticatedUser() {
  const supabase = await createClient();
  const { data, error } = await supabase.auth.getUser();
  if (error || !isCompanyUser(data.user)) return null;
  return data.user;
}
