export type MediaKey = "digmedia" | "market" | "venture";
export type Device = "SP" | "PC";

export type AdPerformance = {
  id: string;
  media: MediaKey;
  category: string;
  subcategory: string;
  placement: string;
  destination: string;
  comment: string;
  device: Device;
  impressions: number;
  clicks: number;
  cv: number;
  gradCv: number;
  status: "稼働中" | "終了";
};

export const mediaLabels: Record<MediaKey, string> = {
  digmedia: "Digmedia",
  market: "就活市場",
  venture: "ベンチャー就活",
};

export const demoRows: AdPerformance[] = [
  { id:"CenterD2003_sp",media:"digmedia",category:"自己分析",subcategory:"ES作成",placement:"見出し5",destination:"会員登録",comment:"ES AI添削",device:"SP",impressions:18420,clicks:978,cv:142,gradCv:98,status:"稼働中" },
  { id:"CenterD2003_pc",media:"digmedia",category:"自己分析",subcategory:"ES作成",placement:"見出し5",destination:"会員登録",comment:"ES AI添削",device:"PC",impressions:7894,clicks:301,cv:36,gradCv:24,status:"稼働中" },
  { id:"TopD3252_sp",media:"digmedia",category:"ES対策",subcategory:"ガクチカ",placement:"見出し1",destination:"適性診断",comment:"挑戦したこと",device:"SP",impressions:12340,clicks:692,cv:88,gradCv:61,status:"稼働中" },
  { id:"CenterS1842_sp",media:"market",category:"企業研究",subcategory:"企業選び",placement:"記事中段",destination:"企業一覧",comment:"優良企業特集",device:"SP",impressions:15780,clicks:631,cv:73,gradCv:52,status:"稼働中" },
  { id:"CenterS1842_pc",media:"market",category:"企業研究",subcategory:"企業選び",placement:"記事中段",destination:"企業一覧",comment:"優良企業特集",device:"PC",impressions:6762,clicks:209,cv:21,gradCv:13,status:"稼働中" },
  { id:"TopS0911_sp",media:"market",category:"面接対策",subcategory:"一次面接",placement:"ファーストビュー",destination:"面接診断",comment:"面接力チェック",device:"SP",impressions:10220,clicks:511,cv:81,gradCv:64,status:"稼働中" },
  { id:"CenterV0737_sp",media:"venture",category:"ES対策",subcategory:"自己PR",placement:"見出し7",destination:"会員登録",comment:"自己分析",device:"SP",impressions:13900,clicks:722,cv:105,gradCv:78,status:"稼働中" },
  { id:"CenterV0737_pc",media:"venture",category:"ES対策",subcategory:"自己PR",placement:"見出し7",destination:"会員登録",comment:"自己分析",device:"PC",impressions:5957,clicks:201,cv:22,gradCv:15,status:"稼働中" },
];

export function rate(numerator: number, denominator: number) {
  return denominator === 0 ? null : (numerator / denominator) * 100;
}

export function formatRate(value: number | null) {
  return value === null ? "—" : `${value.toFixed(1)}%`;
}
