import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
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

test("server-renders the advertising dashboard", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>小林広告分析ver\.2<\/title>/i);
  assert.match(html, /小林広告分析/);
  assert.match(html, /広告パフォーマンス/);
  assert.match(html, /設置場所別・週次分析/);
  assert.doesNotMatch(html, /UI PROTOTYPE|画面案を切り替え/);
});

test("keeps the selected design and removes prototype variants", async () => {
  const [dashboard, page] = await Promise.all([
    readFile(new URL("../app/Dashboard.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
  ]);
  assert.match(dashboard, /カテゴリ/);
  assert.match(dashboard, /小カテゴリ/);
  assert.match(dashboard, /sidebar/);
  assert.doesNotMatch(dashboard, /VariantA|VariantB|VariantC|prototype-switcher/);
  assert.match(page, /<Dashboard \/>/);
});
