import { getAuthenticatedUser, isAdminEmail } from "@/lib/auth";

export async function requireAdmin(): Promise<Response | null> {
  const user = await getAuthenticatedUser();
  if (user && isAdminEmail(user.email)) return null;
  return Response.json({ error: "管理者のみ利用できます" }, { status: 403 });
}
