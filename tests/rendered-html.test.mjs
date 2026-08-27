import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/login", { headers: { accept: "text/html" } }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the company Google login", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>小林広告分析ver\.2<\/title>/i);
  assert.match(html, /小林広告分析/);
  assert.match(html, /会社アカウントでログイン/);
  assert.match(html, /Googleアカウントでログイン/);
  assert.match(html, /@hr-team\.co\.jp/);
  assert.doesNotMatch(html, /UI PROTOTYPE|画面案を切り替え/);
});

test("keeps the selected design and removes prototype variants", async () => {
  const [dashboard, sidebar, page, adsPage, weeklyPage, categoriesPage, logsPage, updatesPage, updateMenu, usersPage, userPermissions, schema, styles] = await Promise.all([
    readFile(new URL("../app/Dashboard.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/_components/AppFrame.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/ads/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/weekly/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/categories/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/logs/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/updates/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/updates/UpdateMenu.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/users/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/users/UserPermissions.tsx", import.meta.url), "utf8"),
    readFile(new URL("../supabase/schema.sql", import.meta.url), "utf8"),
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
  ]);
  assert.match(dashboard, /カテゴリ/);
  assert.match(dashboard, /小カテゴリ/);
  assert.match(dashboard, /掲載期間/);
  assert.match(sidebar, /\/categories/);
  assert.match(sidebar, /\/logs/);
  assert.match(sidebar, /\/updates/);
  assert.match(sidebar, /\/users/);
  assert.doesNotMatch(dashboard, /VariantA|VariantB|VariantC|prototype-switcher/);
  assert.match(page, /redirect\("\/analysis"\)/);
  assert.match(adsPage, /view="ads"/);
  assert.match(weeklyPage, /view="weekly"/);
  assert.match(categoriesPage, /CategorySettings/);
  assert.match(logsPage, /UpdateLogs/);
  assert.match(updatesPage, /UpdateMenu/);
  assert.match(updateMenu, /広告マスター/);
  assert.match(updateMenu, /カスタム更新/);
  assert.match(dashboard, /共通カテゴリ/);
  assert.match(dashboard, /設定・追加/);
  assert.match(dashboard, /placement-options/);
  assert.match(usersPage, /UserPermissions/);
  assert.match(userPermissions, /閲覧者/);
  assert.match(userPermissions, /管理者/);
  assert.match(styles, /input\[type="checkbox"\]/);
  assert.match(schema, /with candidate_ads as materialized/);
  assert.match(schema, /select distinct placement from candidate_ads/);
});
