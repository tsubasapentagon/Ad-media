import type { Metadata } from "next";
import { Dashboard } from "./Dashboard";
import { requireChatGPTUser } from "./chatgpt-auth";

export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "小林広告分析ver.2",
  description: "3メディアの広告パフォーマンスを分析する社内ダッシュボード",
};

export default async function Home() {
  const user = await requireChatGPTUser("/");
  void user;
  return <Dashboard />;
}
