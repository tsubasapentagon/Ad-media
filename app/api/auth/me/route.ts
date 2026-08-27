import { getAuthenticatedProfile } from "@/lib/auth";

export async function GET() {
  const profile = await getAuthenticatedProfile();
  if (!profile) return Response.json({ error: "ログインが必要です" }, { status: 401 });
  return Response.json({ email: profile.user.email, isAdmin: profile.role === "admin" });
}
