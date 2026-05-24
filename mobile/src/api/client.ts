import Constants from 'expo-constants';
import { Platform } from 'react-native';

const FALLBACK = 'http://localhost:8000';

const extraUrl = (Constants.expoConfig?.extra as { apiUrl?: string } | undefined)?.apiUrl;

const runtimeUrl =
  typeof globalThis !== 'undefined' &&
  typeof (globalThis as { SIGNAL_API_URL?: string }).SIGNAL_API_URL === 'string'
    ? (globalThis as { SIGNAL_API_URL?: string }).SIGNAL_API_URL
    : undefined;

export const API_BASE: string =
  runtimeUrl || process.env.EXPO_PUBLIC_API_URL || extraUrl || FALLBACK;

export type Mode =
  | 'product_study'
  | 'store_walk'
  | 'moodboard'
  | 'assortment_review'
  | 'single_image';

export type Similarity = 'Strong' | 'Adjacent' | 'Moderate' | 'Weak';

export type BrandSignal = {
  brand: string;
  similarity: Similarity;
  rationale: string;
  citations: string[];
};

export type Direction = {
  label: 'Safe Commercial' | 'Trend Forward' | 'Differentiated Route';
  title: string;
  description: string;
  price_band_inr?: string;
  complexity?: 'easy' | 'medium' | 'hard' | '';
  timing?: string;
};

export type ShotType =
  | 'flatlay' | 'store_walk' | 'lookbook' | 'runway' | 'model_shot' | 'unknown';

export type CategoryGroup =
  | 'top' | 'bottom' | 'outerwear' | 'dress' | 'ethnic'
  | 'footwear' | 'accessory' | 'co_ord' | 'unknown';

export type ImageRead = {
  index: number;
  attributes: {
    category: string;
    silhouette: string;
    colors: string[];
    fabric_guess: string;
    styling: string[];
    trims: string[];
    aesthetic: string;
    market_segment: string;
    notes: string;
    shot_type?: ShotType;
    category_group?: CategoryGroup;
  };
  keywords: string[];
};

export type GroupReport = {
  group_id: CategoryGroup;
  label: string;
  image_indices: number[];
  observation: string;
  summary: string;
  brand_signals: BrandSignal[];
  commentary: string;
  directions: Direction[];
  keywords: string[];
};

export type AnalysisReport = {
  id: string;
  mode: Mode;
  mode_confidence: number;
  image_count: number;
  observation: string;
  summary: string;
  brand_signals: BrandSignal[];
  commentary: string;
  directions: Direction[];
  keywords: string[];
  reads: ImageRead[];
  groups?: GroupReport[];
  // Phase 4 actionable layer
  palette?: string[];
  price_strategy?: string;
  production_notes?: string;
  merchandising?: string;
};

export type UploadImage = { uri: string; name: string; mime: string };

export async function analyze(images: UploadImage[]): Promise<AnalysisReport> {
  const form = new FormData();
  for (let i = 0; i < images.length; i++) {
    const img = images[i];
    const name = img.name || `image_${i}.jpg`;
    if (Platform.OS === 'web') {
      // Browsers' FormData rejects {uri,name,type} shorthand — fetch the
      // blob: / data: URL the web image picker hands back and append a real Blob.
      const blob = await (await fetch(img.uri)).blob();
      form.append('images', blob, name);
    } else {
      // React Native's FormData accepts {uri, name, type} for binary uploads.
      const part = { uri: img.uri, name, type: img.mime || 'image/jpeg' } as unknown as Blob;
      form.append('images', part);
    }
  }

  const resp = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    body: form,
    headers: { Accept: 'application/json' },
  });

  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`analyze failed (${resp.status}): ${body || resp.statusText}`);
  }
  return (await resp.json()) as AnalysisReport;
}

export async function exportReport(
  report: AnalysisReport,
): Promise<{ report_id: string; download_url: string }> {
  const resp = await fetch(`${API_BASE}/export-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report }),
  });
  if (!resp.ok) throw new Error(`export failed (${resp.status})`);
  return resp.json();
}

export async function emailReport(
  report: AnalysisReport,
  email: string,
): Promise<{ ok: boolean; message: string; download_url: string }> {
  const resp = await fetch(`${API_BASE}/email-report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ report, email }),
  });
  if (!resp.ok) throw new Error(`email failed (${resp.status})`);
  return resp.json();
}

export async function analyzeBrief(brief: string): Promise<AnalysisReport> {
  const resp = await fetch(`${API_BASE}/analyze-text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify({ brief }),
  });
  if (!resp.ok) {
    const body = await resp.text().catch(() => '');
    throw new Error(`analyze-text failed (${resp.status}): ${body || resp.statusText}`);
  }
  return (await resp.json()) as AnalysisReport;
}

export async function health(): Promise<{ ok: boolean; llm_configured: boolean; search_configured: boolean }> {
  const resp = await fetch(`${API_BASE}/`);
  return resp.json();
}
