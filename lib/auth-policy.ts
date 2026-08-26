import type { User } from "@supabase/supabase-js";

export const COMPANY_DOMAIN = "hr-team.co.jp";
export const ADMIN_EMAIL = "t-kobayashi@hr-team.co.jp";

export function isCompanyUser(user: User | null): user is User {
  const email = user?.email?.trim().toLowerCase();
  return Boolean(email && user?.email_confirmed_at && email.endsWith(`@${COMPANY_DOMAIN}`));
}

export function isAdminEmail(email: string | null | undefined) {
  return email?.trim().toLowerCase() === ADMIN_EMAIL;
}
