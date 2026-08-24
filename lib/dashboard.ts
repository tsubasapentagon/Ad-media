export type MediaKey = "digmedia" | "market" | "venture";
export type Device = "SP" | "PC" | "不明";

export type AdPerformance = {
  id: string; media: MediaKey; category: string; subcategory: string;
  placement: string; destination: string; comment: string; device: Device;
  impressions: number; clicks: number; cv: number; gradCv: number; status: string;
  startDate: string | null; endDate: string | null;
};

export type DashboardSnapshot = {
  rows: AdPerformance[];
  totals: { impressions: number; clicks: number; cv: number; gradCv: number };
  weekly: { weekStart: string; clicks: number; cv: number }[];
  placementWeekly: { weekStart:string;media:MediaKey;placement:string;device:Device;category:string;subcategory:string;impressions:number;clicks:number;cv:number;gradCv:number }[];
  options: { categories: string[]; subcategories: string[]; placements: string[] };
  lastUpdated: string | null; rowCount: number; startDate: string; endDate: string;
};

export const mediaLabels: Record<MediaKey, string> = {
  digmedia: "Digmedia", market: "就活市場", venture: "ベンチャー就活ナビ",
};

export const emptySnapshot: DashboardSnapshot = {
  rows:[],totals:{impressions:0,clicks:0,cv:0,gradCv:0},weekly:[],placementWeekly:[],
  options:{categories:[],subcategories:[],placements:[]},lastUpdated:null,rowCount:0,startDate:"",endDate:"",
};

export function rate(numerator: number, denominator: number) { return denominator === 0 ? null : (numerator / denominator) * 100; }
export function formatRate(value: number | null) { return value === null ? "—" : `${value.toFixed(1)}%`; }
