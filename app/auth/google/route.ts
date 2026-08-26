import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

export async function GET(request: NextRequest) {
  const next = safeNext(request.nextUrl.searchParams.get("next"));
  const callback = new URL("/auth/callback", request.url);
  callback.searchParams.set("next", next);
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: {
      redirectTo: callback.toString(),
      scopes: "openid https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
      queryParams: { hd: "hr-team.co.jp", prompt: "select_account" },
    },
  });
  if (error || !data.url) return NextResponse.redirect(new URL("/login?error=oauth", request.url));
  return NextResponse.redirect(data.url);
}

function safeNext(value: string | null) {
  if (!value?.startsWith("/") || value.startsWith("//")) return "/analysis";
  return value;
}
