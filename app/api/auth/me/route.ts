import { getAuthenticatedUser, isAdminEmail } from "@/lib/auth";

export async function GET() {
  const user = await getAuthenticatedUser();
  if (!user) return Response.json({ error: "ログインが必要です" }, { status: 401 });
  return Response.json({ email: user.email, isAdmin: isAdminEmail(user.email) });
}
