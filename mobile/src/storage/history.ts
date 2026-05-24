import AsyncStorage from '@react-native-async-storage/async-storage';
import type { AnalysisReport } from '@/api/client';

const KEY = '@signal/history/v1';

export type HistoryEntry = {
  id: string;            // report id
  createdAt: number;     // epoch ms
  thumbnails: string[];  // local file URIs (for collage)
  imageCount: number;
  mode: string;
  observation: string;
  report: AnalysisReport;
};

export async function loadHistory(): Promise<HistoryEntry[]> {
  try {
    const raw = await AsyncStorage.getItem(KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as HistoryEntry[];
    return parsed.sort((a, b) => b.createdAt - a.createdAt);
  } catch {
    return [];
  }
}

export async function appendEntry(entry: HistoryEntry): Promise<void> {
  const cur = await loadHistory();
  const next = [entry, ...cur].slice(0, 60); // cap to last 60
  await AsyncStorage.setItem(KEY, JSON.stringify(next));
}

export async function removeEntry(id: string): Promise<void> {
  const cur = await loadHistory();
  await AsyncStorage.setItem(KEY, JSON.stringify(cur.filter(e => e.id !== id)));
}

export async function clearHistory(): Promise<void> {
  await AsyncStorage.removeItem(KEY);
}

export function groupByDay(entries: HistoryEntry[]): { label: string; items: HistoryEntry[] }[] {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  const yesterday = today - 86_400_000;
  const lastWeek = today - 7 * 86_400_000;
  const groups: Record<string, HistoryEntry[]> = {
    Today: [],
    Yesterday: [],
    'This Week': [],
    Earlier: [],
  };
  for (const e of entries) {
    if (e.createdAt >= today) groups.Today.push(e);
    else if (e.createdAt >= yesterday) groups.Yesterday.push(e);
    else if (e.createdAt >= lastWeek) groups['This Week'].push(e);
    else groups.Earlier.push(e);
  }
  return Object.entries(groups)
    .filter(([, items]) => items.length > 0)
    .map(([label, items]) => ({ label, items }));
}
