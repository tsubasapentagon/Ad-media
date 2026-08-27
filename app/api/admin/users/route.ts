import { requireAdmin } from "@/lib/admin-auth";
import { ADMIN_EMAIL } from "@/lib/auth-policy";
import { createClient } from "@/lib/supabase/server";

export const dynamic = "force-dynamic";

export async function GET() {
  const denied = await requireAdmin();
  if (denied) return denied;
  return listProfiles();
}

export async function POST(request: Request) {
  const denied = await requireAdmin();
  if (denied) return denied;
  try {
    const body = await request.json() as { userId?: string; role?: string };
    if (!body.userId || !/^[0-9a-f-]{36}$/i.test(body.userId) || !["viewer", "admin"].includes(body.role ?? "")) {
      return Response.json({ error: "ユーザーまたは権限が正しくありません" }, { status: 400 });
    }
    const supabase = await createClient();
    const { data: target } = await supabase.from("profiles").select("email").eq("user_id", body.userId).maybeSingle();
    if (!target) return Response.json({ error: "ユーザーが見つかりません" }, { status: 404 });
    if (target.email === ADMIN_EMAIL && body.role !== "admin") {
      return Response.json({ error: "メイン管理者の権限は解除できません" }, { status: 400 });
    }
    const { error } = await supabase.from("profiles").update({ role: body.role }).eq("user_id", body.userId);
    if (error) throw error;
    return listProfiles();
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : "権限を変更できませんでした" }, { status: 500 });
  }
}

async function listProfiles() {
  const supabase = await createClient();
  const { data, error } = await supabase.from("profiles").select("user_id,email,role,created_at").order("created_at", { ascending: true });
  if (error) return Response.json({ error: "ユーザー一覧を取得できませんでした" }, { status: 500 });
  return Response.json({ users: data ?? [], primaryAdmin: ADMIN_EMAIL });
}
