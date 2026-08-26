import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { isCompanyUser } from "@/lib/auth-policy";

export async function GET(request: NextRequest) {
  const code = request.nextUrl.searchParams.get("code");
  const next = safeNext(request.nextUrl.searchParams.get("next"));
  const supabase = await createClient();
  if (code) {
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      const { data } = await supabase.auth.getUser();
      if (isCompanyUser(data.user)) return NextResponse.redirect(new URL(next, request.url));
      await supabase.auth.signOut();
      return NextResponse.redirect(new URL("/login?error=domain", request.url));
    }
  }
  return NextResponse.redirect(new URL("/login?error=oauth", request.url));
}

function safeNext(value: string | null) {
  if (!value?.startsWith("/") || value.startsWith("//")) return "/analysis";
  return value;
}
