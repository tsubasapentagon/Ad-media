import { getAuthenticatedProfile } from "@/lib/auth";

export async function requireAdmin(): Promise<Response | null> {
  const profile = await getAuthenticatedProfile();
  if (profile?.role === "admin") return null;
  return Response.json({ error: "管理者のみ利用できます" }, { status: 403 });
}
