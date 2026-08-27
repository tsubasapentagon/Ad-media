import { createServerClient } from "@supabase/ssr";
import { NextRequest, NextResponse } from "next/server";
import { isAdminEmail, isCompanyUser } from "@/lib/auth-policy";

const PUBLIC_PATHS = new Set(["/login", "/auth/google", "/auth/callback", "/auth/signout"]);
const ADMIN_PATHS = new Set(["/categories", "/updates", "/logs", "/users"]);

export async function proxy(request: NextRequest) {
  let response = NextResponse.next({ request });
  const pathname = request.nextUrl.pathname;
  if (PUBLIC_PATHS.has(pathname)) return response;
  const supabase = createServerClient(
    requiredEnv("SUPABASE_URL"),
    requiredEnv("SUPABASE_PUBLISHABLE_KEY"),
    {
      cookies: {
        getAll: () => request.cookies.getAll(),
        setAll: (cookiesToSet) => {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value));
          response = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) => response.cookies.set(name, value, options));
        },
      },
    },
  );

  const { data } = await supabase.auth.getUser();
  if (!isCompanyUser(data.user)) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", `${pathname}${request.nextUrl.search}`);
    return NextResponse.redirect(loginUrl);
  }
  const { data: profile } = await supabase.from("profiles").select("role").eq("user_id", data.user.id).maybeSingle();
  const isAdmin = isAdminEmail(data.user.email) || profile?.role === "admin";
  if (ADMIN_PATHS.has(pathname) && !isAdmin) {
    return NextResponse.redirect(new URL("/analysis", request.url));
  }

  const headers = new Headers(request.headers);
  headers.delete("x-dashboard-admin");
  headers.delete("x-authenticated-user-email");
  headers.set("x-authenticated-user-email", data.user.email!.toLowerCase());
  if (isAdmin) headers.set("x-dashboard-admin", "1");
  const authorizedResponse = NextResponse.next({ request: { headers } });
  response.cookies.getAll().forEach(cookie => authorizedResponse.cookies.set(cookie));
  return authorizedResponse;
}

function requiredEnv(name: "SUPABASE_URL" | "SUPABASE_PUBLISHABLE_KEY") {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is not configured`);
  return value;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.svg|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
