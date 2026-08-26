import { LoginButton } from "./LoginButton";

export const dynamic = "force-dynamic";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string; error?: string }>;
}) {
  const params = await searchParams;
  const next = safeNext(params.next);
  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-brand"><span>K</span><div><strong>小林広告分析</strong><small>ver.2</small></div></div>
        <div className="login-copy">
          <p>社内広告の数字を、ひとつの画面で。</p>
          <h1>会社アカウントでログイン</h1>
          <p>分析画面は、HR teamのGoogleアカウントをお持ちの方のみ利用できます。</p>
        </div>
        {params.error === "domain" && <p className="login-error">会社のGoogleアカウントを選択してください。</p>}
        {params.error === "oauth" && <p className="login-error">ログインを完了できませんでした。もう一度お試しください。</p>}
        <LoginButton next={next} />
        <p className="login-domain">利用可能：@hr-team.co.jp</p>
      </section>
    </main>
  );
}

function safeNext(value?: string) {
  if (!value?.startsWith("/") || value.startsWith("//")) return "/analysis";
  return value;
}
