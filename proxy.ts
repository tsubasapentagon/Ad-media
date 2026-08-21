import { NextRequest, NextResponse } from "next/server";

function sameText(left: string, right: string): boolean {
  if (left.length !== right.length) return false;
  let difference = 0;
  for (let index = 0; index < left.length; index += 1) {
    difference |= left.charCodeAt(index) ^ right.charCodeAt(index);
  }
  return difference === 0;
}

export function proxy(request: NextRequest) {
  const allowedEmail = process.env.DASHBOARD_LOGIN_EMAIL;
  const allowedPassword = process.env.DASHBOARD_LOGIN_PASSWORD;

  if (!allowedEmail || !allowedPassword) {
    return new NextResponse("ログイン設定がありません", { status: 503 });
  }

  const authorization = request.headers.get("authorization");
  if (authorization?.startsWith("Basic ")) {
    try {
      const decoded = atob(authorization.slice(6));
      const separator = decoded.indexOf(":");
      const email = decoded.slice(0, separator).toLowerCase();
      const password = decoded.slice(separator + 1);
      if (
        separator > 0 &&
        sameText(email, allowedEmail.toLowerCase()) &&
        sameText(password, allowedPassword)
      ) {
        return NextResponse.next();
      }
    } catch {
      // Invalid Basic authentication payload.
    }
  }

  return new NextResponse("ログインしてください", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="小林広告分析ver.2", charset="UTF-8"' },
  });
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.svg).*)"],
};
