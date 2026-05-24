import React, { useState } from 'react';
import {
  ActivityIndicator,
  Image,
  KeyboardAvoidingView,
  Linking,
  Modal,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, CommonActions } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Kicker } from '@/components/Kicker';
import { SimilarityPill } from '@/components/SimilarityPill';
import { colors, radii, spacing, type } from '@/theme';
import type { RootStackParamList } from '@/navigation';
import { refineDirection, type Direction } from '@/api/client';

type Props = NativeStackScreenProps<RootStackParamList, 'Results'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'Results'>;

const HERO_HEIGHT = 360;

const REFINE_SUGGESTIONS = [
  'but in linen',
  'push the proportion more',
  'shift to festive',
  'drop the price by 30%',
  'add an embroidered placement',
];

export function ResultsScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { report, thumbnails } = route.params;
  const [showDetail, setShowDetail] = useState(false);

  // Local state for directions so we can replace one after refine.
  const [directions, setDirections] = useState<Direction[]>(report.directions);

  // Refine modal state
  const [refineFor, setRefineFor] = useState<Direction | null>(null);
  const [refineText, setRefineText] = useState('');
  const [refineBusy, setRefineBusy] = useState(false);
  const [refineError, setRefineError] = useState<string | null>(null);

  const openRefine = (d: Direction) => {
    setRefineFor(d);
    setRefineText('');
    setRefineError(null);
  };
  const closeRefine = () => {
    if (refineBusy) return;
    setRefineFor(null);
    setRefineText('');
    setRefineError(null);
  };
  const submitRefine = async () => {
    if (!refineFor) return;
    const text = refineText.trim();
    if (text.length < 2) {
      setRefineError('Add a bit more detail.');
      return;
    }
    setRefineBusy(true);
    setRefineError(null);
    try {
      const updated = await refineDirection({
        direction: refineFor,
        refinement: text,
        observation: report.observation,
        commentary: report.commentary,
        palette: report.palette,
      });
      setDirections((prev) => prev.map((d) => (d.label === updated.label ? updated : d)));
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      setRefineFor(null);
      setRefineText('');
    } catch (e: any) {
      setRefineError(e?.message ?? 'Refinement failed.');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
    } finally {
      setRefineBusy(false);
    }
  };

  const modeLabel = report.mode.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  const hasHeroImage = thumbnails.length > 0;
  const hero = thumbnails[0];
  const extraThumbs = thumbnails.slice(1, 5);

  return (
    <SafeAreaView style={styles.container} edges={['left', 'right']}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
        stickyHeaderIndices={[]}
      >
        {/* ─── HERO ─────────────────────────────────────────────── */}
        <View style={styles.hero}>
          {hasHeroImage ? (
            <Image source={{ uri: hero }} style={styles.heroImg} resizeMode="cover" />
          ) : (
            <View style={[styles.heroImg, styles.heroFallback]} />
          )}
          <View style={styles.heroOverlay} />
          {/* Floating header chips */}
          <SafeAreaView edges={['top']} style={styles.heroChromeWrap} pointerEvents="box-none">
            <View style={styles.heroChrome}>
              <Pressable
                onPress={() => nav.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'Tabs' }] }))}
                style={styles.heroBtn}
                hitSlop={12}
              >
                <Text style={styles.heroBtnText}>←</Text>
              </Pressable>
              <Pressable
                onPress={() => nav.navigate('Export', { report })}
                style={styles.heroBtnWide}
                hitSlop={12}
              >
                <Text style={styles.heroBtnText}>Export ↗</Text>
              </Pressable>
            </View>
          </SafeAreaView>
          {/* Bottom-anchored editorial title */}
          <View style={styles.heroBottom}>
            <Text style={styles.heroKicker}>SIGNAL · {modeLabel.toUpperCase()}</Text>
            <Text style={styles.heroObservation}>{report.observation}</Text>
            {report.summary ? (
              <Text style={styles.heroSummary}>{report.summary}</Text>
            ) : null}
          </View>
        </View>

        {/* ─── ADDITIONAL UPLOADED IMAGES (strip) ───────────────── */}
        {extraThumbs.length > 0 ? (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.thumbStrip}
          >
            {extraThumbs.map((uri, idx) => (
              <Image key={uri + idx} source={{ uri }} style={styles.thumbStripImg} />
            ))}
            {thumbnails.length > 5 ? (
              <View style={[styles.thumbStripImg, styles.thumbStripMore]}>
                <Text style={styles.thumbStripMoreText}>+{thumbnails.length - 5}</Text>
              </View>
            ) : null}
          </ScrollView>
        ) : null}

        {/* ─── DATA-SOURCE BANNER (when AI was partial / unreachable) ──── */}
        {report.data_source && report.data_source !== 'live' ? (
          <View style={[styles.padX, { marginTop: spacing.md }]}>
            <View style={[
              styles.dataBanner,
              report.data_source === 'fallback' ? styles.dataBannerWarn : styles.dataBannerInfo,
            ]}>
              <Text style={styles.dataBannerKicker}>
                {report.data_source === 'fallback' ? 'OFFLINE BRIEF' : 'PARTIAL READ'}
              </Text>
              <Text style={styles.dataBannerText}>
                {report.data_source === 'fallback'
                  ? "The AI commentary service didn't respond — this brief is generated from the vision read alone. Sections will be less specific than a live read."
                  : "The AI read returned partial commentary; missing sections were backfilled from the vision read. Re-run for the full take."}
              </Text>
            </View>
          </View>
        ) : null}

        {/* ─── THE INDIA TRANSLATION (main hook) ────────────────── */}
        <View style={styles.padX}>
          <View style={{ height: spacing.xl }} />
          <View style={styles.sectionLabelRow}>
            <View style={styles.accentBar} />
            <Text style={styles.sectionLabel}>The India Translation</Text>
          </View>

          {report.why_now ? (
            <View style={styles.whyCard}>
              <Text style={styles.whyKicker}>WHY NOW</Text>
              <Text style={styles.whyText}>{report.why_now}</Text>
            </View>
          ) : null}

          {report.consumer ? (
            <View style={styles.consumerCard}>
              <Text style={styles.consumerKicker}>WHO BUYS · WHEN WORN</Text>
              <Text style={styles.consumerText}>{report.consumer}</Text>
            </View>
          ) : null}
        </View>

        {/* ─── COMMENTARY (the WHY in prose) ────────────────────── */}
        {report.commentary ? (
          <View style={styles.padX}>
            <View style={styles.sectionLabelRow}>
              <View style={styles.accentBar} />
              <Text style={styles.sectionLabel}>The Read</Text>
            </View>
            <Text style={styles.commentaryText}>{report.commentary}</Text>
          </View>
        ) : null}

        {/* ─── INTERNATIONAL ANCHORS (horizontal carousel) ──────── */}
        <View>
          <View style={[styles.padX, styles.sectionLabelRow]}>
            <View style={styles.accentBar} />
            <Text style={styles.sectionLabel}>International Anchors</Text>
          </View>
          <Text style={[styles.padX, styles.sectionSub]}>
            The aspirational reference set. Translate from these.
          </Text>
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.brandStrip}
            decelerationRate="fast"
            snapToInterval={244}
            snapToAlignment="start"
          >
            {report.brand_signals.map((sig, idx) => (
              <View key={sig.brand} style={[styles.brandCard, idx === 0 ? { marginLeft: spacing.xl } : null]}>
                <View style={styles.brandCardTop}>
                  <Text style={styles.brandCardNum}>{String(idx + 1).padStart(2, '0')}</Text>
                  <SimilarityPill value={sig.similarity} />
                </View>
                <Text style={styles.brandCardName}>{sig.brand}</Text>
                <Text style={styles.brandCardRationale}>{sig.rationale}</Text>
              </View>
            ))}
          </ScrollView>
        </View>

        {/* ─── PRICE LADDER (3-up) ─────────────────────────────── */}
        {(report.price_anchor_inr || report.price_floor_inr || report.price_target_inr) ? (
          <View style={styles.padX}>
            <View style={styles.sectionLabelRow}>
              <View style={styles.accentBar} />
              <Text style={styles.sectionLabel}>Price Ladder</Text>
            </View>

            <View style={styles.ladderRow}>
              <View style={[styles.ladderCol, styles.ladderColAnchor]}>
                <Text style={styles.ladderTag}>ASPIRATIONAL ANCHOR</Text>
                <Text style={styles.ladderValue}>{report.price_anchor_inr || '—'}</Text>
                <Text style={styles.ladderSub}>The global look</Text>
              </View>
              <View style={styles.ladderArrow}>
                <Text style={styles.ladderArrowText}>→</Text>
              </View>
              <View style={[styles.ladderCol, styles.ladderColFloor]}>
                <Text style={styles.ladderTag}>INDIA VALUE FLOOR</Text>
                <Text style={styles.ladderValue}>{report.price_floor_inr || '—'}</Text>
                <Text style={styles.ladderSub}>Where it lands today</Text>
              </View>
              <View style={styles.ladderArrow}>
                <Text style={styles.ladderArrowText}>→</Text>
              </View>
              <View style={[styles.ladderCol, styles.ladderColTarget]}>
                <Text style={[styles.ladderTag, { color: '#fff', opacity: 0.85 }]}>YOUR MRP</Text>
                <Text style={[styles.ladderValue, { color: '#fff' }]}>{report.price_target_inr || '—'}</Text>
                <Text style={[styles.ladderSub, { color: '#fff', opacity: 0.85 }]}>Recommended</Text>
              </View>
            </View>

            {report.price_strategy ? (
              <Text style={styles.ladderProse}>{report.price_strategy}</Text>
            ) : null}
          </View>
        ) : null}

        {/* ─── INDIA PLAY (HOW to launch) ──────────────────────── */}
        {report.india_play ? (
          <View style={styles.padX}>
            <View style={styles.indiaPlayCard}>
              <Text style={styles.indiaPlayKicker}>HOW TO LAUNCH</Text>
              <Text style={styles.indiaPlayText}>{report.india_play}</Text>
            </View>
          </View>
        ) : null}

        {/* ─── PALETTE ─────────────────────────────────────────── */}
        {report.palette && report.palette.length > 0 ? (
          <View>
            <View style={[styles.padX, styles.sectionLabelRow]}>
              <View style={styles.accentBar} />
              <Text style={styles.sectionLabel}>Palette</Text>
            </View>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.paletteStrip}
            >
              {report.palette.map((c, idx) => {
                const hex = colorToHex(c);
                return (
                  <View key={c + idx} style={[styles.swatchWrap, idx === 0 ? { marginLeft: spacing.xl } : null]}>
                    <View style={[styles.swatch, { backgroundColor: hex }]} />
                    <Text style={styles.swatchLabel}>{c}</Text>
                    <Text style={styles.swatchHex}>{hex.toUpperCase()}</Text>
                  </View>
                );
              })}
            </ScrollView>
          </View>
        ) : null}

        {/* ─── PRODUCTION + MERCHANDISING ──────────────────────── */}
        {report.production_notes || report.merchandising ? (
          <View style={styles.padX}>
            <View style={styles.sectionLabelRow}>
              <View style={styles.accentBar} />
              <Text style={styles.sectionLabel}>On the Floor</Text>
            </View>
            <View style={styles.opsRow}>
              {report.production_notes ? (
                <View style={styles.opsCol}>
                  <Text style={styles.opsKicker}>PRODUCTION</Text>
                  <Text style={styles.opsText}>{report.production_notes}</Text>
                </View>
              ) : null}
              {report.merchandising ? (
                <View style={styles.opsCol}>
                  <Text style={styles.opsKicker}>MERCHANDISING</Text>
                  <Text style={styles.opsText}>{report.merchandising}</Text>
                </View>
              ) : null}
            </View>
          </View>
        ) : null}

        {/* ─── DIRECTIONS ──────────────────────────────────────── */}
        <View style={styles.padX}>
          <View style={styles.sectionLabelRow}>
            <View style={styles.accentBar} />
            <Text style={styles.sectionLabel}>Three Routes Forward</Text>
          </View>
          {directions.map((d) => {
            const meta = DIRECTION_META[d.label] || DIRECTION_META.fallback;
            const metaBits = [
              d.price_band_inr,
              d.complexity ? `${d.complexity} build` : '',
              d.timing,
            ].filter(Boolean) as string[];
            return (
              <View key={d.label} style={[styles.dirCard, { backgroundColor: meta.tint }]}>
                {d.image_url ? (
                  <View style={styles.dirImageWrap}>
                    <Image
                      source={{ uri: d.image_url }}
                      style={styles.dirImage}
                      resizeMode="cover"
                    />
                  </View>
                ) : null}
                <View style={styles.dirBody}>
                  <View style={styles.dirCardHead}>
                    <Text style={styles.dirCardGlyph}>{meta.glyph}</Text>
                    <Text style={[styles.dirCardLabel, { color: meta.color }]}>{d.label.toUpperCase()}</Text>
                  </View>
                  <Text style={styles.dirCardTitle}>{d.title}</Text>
                  <Text style={styles.dirCardDesc}>{d.description}</Text>
                  {metaBits.length ? (
                    <View style={styles.dirMetaRow}>
                      {metaBits.map((m, idx) => (
                        <View key={idx} style={styles.dirMetaPill}>
                          <Text style={styles.dirMetaText}>{m}</Text>
                        </View>
                      ))}
                    </View>
                  ) : null}
                  <Pressable
                    onPress={() => openRefine(d)}
                    style={({ pressed }) => [styles.refineBtn, pressed && { opacity: 0.7 }]}
                    hitSlop={8}
                  >
                    <Text style={styles.refineBtnText}>✎  Refine this direction</Text>
                  </Pressable>
                </View>
              </View>
            );
          })}
        </View>

        {/* ─── PER-CATEGORY BREAKDOWN ──────────────────────────── */}
        {report.groups && report.groups.length > 1 ? (
          <View style={styles.padX}>
            <View style={styles.sectionLabelRow}>
              <View style={styles.accentBar} />
              <Text style={styles.sectionLabel}>By Category</Text>
            </View>
            <Text style={styles.byCatLead}>
              {report.groups.length} categories detected. Each gets its own signal and direction.
            </Text>
            {report.groups.map((g) => (
              <Card key={g.group_id + g.label} style={{ marginTop: spacing.md }}>
                <View style={styles.groupHead}>
                  <Text style={styles.groupLabel}>{g.label}</Text>
                  <Text style={styles.groupCount}>
                    {g.image_indices.length} image{g.image_indices.length === 1 ? '' : 's'}
                  </Text>
                </View>
                <Text style={styles.groupObs}>{g.observation}</Text>
                {g.summary ? <Text style={styles.groupSummary}>{g.summary}</Text> : null}
                {g.brand_signals.length ? (
                  <View style={styles.groupBrands}>
                    {g.brand_signals.slice(0, 4).map((sig) => (
                      <View key={sig.brand} style={styles.groupBrandRow}>
                        <Text style={styles.groupBrandName}>{sig.brand}</Text>
                        <SimilarityPill value={sig.similarity} />
                      </View>
                    ))}
                  </View>
                ) : null}
                {g.commentary ? <Text style={styles.groupCommentary}>{g.commentary}</Text> : null}
              </Card>
            ))}
          </View>
        ) : null}

        {/* ─── DETAIL DRAWER ───────────────────────────────────── */}
        <View style={styles.padX}>
          <Pressable onPress={() => setShowDetail((v) => !v)} style={styles.detailToggle}>
            <Text style={styles.detailToggleText}>
              {showDetail ? '— Hide full intelligence' : '+ See full intelligence'}
            </Text>
          </Pressable>

          {showDetail ? (
            <Card flat style={[styles.detailCard, { marginBottom: spacing.xl }]}>
              <Kicker>Detection</Kicker>
              <Text style={styles.metaLine}>
                {modeLabel} · confidence {(report.mode_confidence * 100).toFixed(0)}% · {report.image_count} image
                {report.image_count === 1 ? '' : 's'}
              </Text>

              {report.keywords.length ? (
                <>
                  <View style={{ height: spacing.lg }} />
                  <Kicker>Keywords ({report.keywords.length})</Kicker>
                  <View style={styles.chipRow}>
                    {report.keywords.map((k) => (
                      <View key={k} style={styles.chip}>
                        <Text style={styles.chipText}>{k}</Text>
                      </View>
                    ))}
                  </View>
                </>
              ) : null}

              {report.brand_signals.some((s) => s.citations.length) ? (
                <>
                  <View style={{ height: spacing.lg }} />
                  <Kicker>Brand Citations</Kicker>
                  {report.brand_signals.filter((s) => s.citations.length).map((s) => (
                    <View key={s.brand} style={styles.citeBlock}>
                      <Text style={styles.citeBrand}>{s.brand}</Text>
                      {s.citations.map((url, idx) => (
                        <Pressable key={url + idx} onPress={() => Linking.openURL(url).catch(() => {})}>
                          <Text style={styles.citeLink} numberOfLines={1}>
                            {url.replace(/^https?:\/\//, '')}
                          </Text>
                        </Pressable>
                      ))}
                    </View>
                  ))}
                </>
              ) : null}

              <View style={{ height: spacing.lg }} />
              <Kicker>Per-Image Reads ({report.reads.length})</Kicker>
              {report.reads.map((r) => (
                <View key={r.index} style={styles.readBlock}>
                  <Text style={styles.readHead}>
                    Image {r.index + 1} — {r.attributes.category || 'apparel'}
                  </Text>
                  {r.attributes.silhouette ? <ReadRow label="Silhouette" value={r.attributes.silhouette} /> : null}
                  {r.attributes.fabric_guess ? <ReadRow label="Fabric" value={r.attributes.fabric_guess} /> : null}
                  {r.attributes.colors.length ? <ReadRow label="Colors" value={r.attributes.colors.join(', ')} /> : null}
                  {r.attributes.styling.length ? <ReadRow label="Styling" value={r.attributes.styling.join(', ')} /> : null}
                  {r.attributes.trims.length ? <ReadRow label="Trims" value={r.attributes.trims.join(', ')} /> : null}
                  {r.attributes.aesthetic ? <ReadRow label="Aesthetic" value={r.attributes.aesthetic} /> : null}
                  {r.attributes.market_segment ? <ReadRow label="Tier" value={r.attributes.market_segment} /> : null}
                  {r.attributes.notes ? <ReadRow label="Notes" value={r.attributes.notes} /> : null}
                </View>
              ))}
            </Card>
          ) : null}
        </View>

        <View style={[styles.padX, styles.ctaRow]}>
          <Button label="Export Brief" onPress={() => nav.navigate('Export', { report })} style={{ flex: 1 }} />
        </View>
      </ScrollView>

      {/* ─── REFINE MODAL ──────────────────────────────────────── */}
      <Modal
        visible={refineFor !== null}
        animationType="slide"
        transparent
        onRequestClose={closeRefine}
      >
        <Pressable style={styles.modalBackdrop} onPress={closeRefine}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : undefined}
            style={styles.modalKeyboardWrap}
          >
            <Pressable onPress={(e) => e.stopPropagation()} style={styles.modalSheet}>
              <View style={styles.modalHandle} />
              <Text style={styles.modalKicker}>REFINE</Text>
              <Text style={styles.modalTitle}>{refineFor?.title}</Text>
              <Text style={styles.modalSubtle}>
                Describe the change in plain English. We'll rewrite the brief and regenerate the image.
              </Text>

              <TextInput
                value={refineText}
                onChangeText={(t) => { setRefineText(t); if (refineError) setRefineError(null); }}
                placeholder="e.g. but in linen, drop the print"
                placeholderTextColor={colors.textSubtle}
                style={styles.modalInput}
                multiline
                numberOfLines={3}
                editable={!refineBusy}
                autoFocus
              />

              {refineError ? <Text style={styles.modalError}>{refineError}</Text> : null}

              <View style={styles.modalChipRow}>
                {REFINE_SUGGESTIONS.map((s) => (
                  <Pressable
                    key={s}
                    onPress={() => !refineBusy && setRefineText(s)}
                    style={({ pressed }) => [styles.modalChip, pressed && { opacity: 0.7 }]}
                  >
                    <Text style={styles.modalChipText}>{s}</Text>
                  </Pressable>
                ))}
              </View>

              <View style={styles.modalActions}>
                <Pressable onPress={closeRefine} style={styles.modalCancel} hitSlop={8}>
                  <Text style={styles.modalCancelText}>Cancel</Text>
                </Pressable>
                <Button
                  label={refineBusy ? 'Refining…' : 'Apply refinement'}
                  onPress={submitRefine}
                  loading={refineBusy}
                  disabled={refineBusy}
                  style={{ flex: 1 }}
                />
              </View>

              {refineBusy ? (
                <View style={styles.modalBusy}>
                  <ActivityIndicator size="small" color={colors.emerald} />
                  <Text style={styles.modalBusyText}>
                    Rewriting + regenerating image…
                  </Text>
                </View>
              ) : null}
            </Pressable>
          </KeyboardAvoidingView>
        </Pressable>
      </Modal>
    </SafeAreaView>
  );
}

// ─── color helpers ───────────────────────────────────────────────
const NAMED_COLORS: Record<string, string> = {
  'ecru': '#E8DFCB', 'cream': '#F1E8D1', 'off-white': '#F5F1E6', 'ivory': '#F6EFDB',
  'sand': '#D9C4A0', 'stone': '#B8AE9E', 'taupe': '#A89484', 'mushroom': '#A89C8A',
  'charcoal': '#3A3A38', 'jet': '#1A1A18', 'black': '#0F0F0E', 'white': '#FFFFFF',
  'rust': '#A74C2A', 'terracotta': '#B96B47', 'burnt sienna': '#9D4A2A',
  'sienna': '#A0522D', 'brick': '#9C4A3B', 'clay': '#B07758', 'camel': '#B9925A',
  'tobacco': '#7A4A2D', 'umber': '#6B4423',
  'olive': '#6B6A2E', 'sage': '#9CAA8A', 'forest': '#2D4F3A', 'kerala green': '#1F5F4A',
  'moss': '#7A8A4A', 'mint': '#B5D4C3', 'fern': '#5B7A4A',
  'indigo': '#2D3E70', 'navy': '#1F2C4A', 'denim': '#4A6D8C', 'sky': '#8AB0CC',
  'cobalt': '#2D4FB8', 'rinse': '#243B5A', 'midnight': '#0F1B2E',
  'blush': '#E8C2BC', 'rose': '#C77A7A', 'dusty rose': '#C4928D', 'coral': '#E37868',
  'salmon': '#E0866A', 'peach': '#F0BFA0',
  'mustard': '#C99B30', 'gold': '#C5A04B', 'ochre': '#C28A30', 'butter': '#E8D085',
  'plum': '#6B3A55', 'aubergine': '#3F2438', 'lavender': '#B7AAC8',
  'red': '#B23A2E', 'burgundy': '#7A2A2A', 'wine': '#5C1F1F', 'tomato': '#C84A33',
  'grey': '#8A8780', 'gray': '#8A8780', 'dove': '#B7B3A8', 'graphite': '#4D4D49',
};

function colorToHex(name: string): string {
  const k = name.trim().toLowerCase();
  if (NAMED_COLORS[k]) return NAMED_COLORS[k];
  for (const key of Object.keys(NAMED_COLORS).sort((a, b) => b.length - a.length)) {
    if (k.includes(key)) return NAMED_COLORS[key];
  }
  return '#C9C2B0';
}

const DIRECTION_META: Record<string, { tint: string; color: string; glyph: string }> = {
  'Safe Commercial':      { tint: colors.safeTint,    color: colors.emerald,  glyph: '◆' },
  'Trend Forward':        { tint: colors.trendTint,   color: colors.burgundy, glyph: '↗' },
  'Differentiated Route': { tint: colors.diffTint,    color: colors.text,     glyph: '★' },
  fallback:               { tint: colors.surfaceMuted, color: colors.text,    glyph: '◆' },
};

function ReadRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.readRow}>
      <Text style={styles.readRowLabel}>{label}</Text>
      <Text style={styles.readRowValue}>{value}</Text>
    </View>
  );
}

// ─── styles ──────────────────────────────────────────────────────
const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { paddingBottom: spacing.xxxl },
  padX: { paddingHorizontal: spacing.xl },

  // HERO
  hero: { width: '100%', height: HERO_HEIGHT, backgroundColor: colors.text, position: 'relative' },
  heroImg: { ...StyleSheet.absoluteFillObject, width: '100%', height: HERO_HEIGHT },
  heroFallback: { backgroundColor: colors.emeraldDeep },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15,15,14,0.45)',
  },
  heroChromeWrap: { position: 'absolute', top: 0, left: 0, right: 0 },
  heroChrome: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: spacing.lg, paddingTop: spacing.md,
  },
  heroBtn: {
    width: 40, height: 40, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center', justifyContent: 'center',
  },
  heroBtnWide: {
    paddingHorizontal: spacing.md, height: 40, borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.18)',
    alignItems: 'center', justifyContent: 'center', flexDirection: 'row',
  },
  heroBtnText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  heroBottom: {
    position: 'absolute', left: 0, right: 0, bottom: 0,
    paddingHorizontal: spacing.xl, paddingBottom: spacing.xl,
  },
  heroKicker: {
    color: 'rgba(255,255,255,0.75)',
    fontSize: 11, letterSpacing: 1.8, fontWeight: '600', marginBottom: spacing.sm,
  },
  heroObservation: {
    color: '#fff', fontSize: 34, lineHeight: 38, fontWeight: '700', letterSpacing: -0.8,
  },
  heroSummary: {
    color: 'rgba(255,255,255,0.85)', fontSize: 14, lineHeight: 20, marginTop: spacing.sm,
  },

  // Thumb strip beneath hero
  thumbStrip: {
    paddingHorizontal: spacing.xl, paddingTop: spacing.md, gap: spacing.sm,
  },
  thumbStripImg: {
    width: 56, height: 56, borderRadius: radii.sm,
    backgroundColor: colors.surfaceMuted,
  },
  thumbStripMore: { alignItems: 'center', justifyContent: 'center' },
  thumbStripMoreText: { ...type.bodySm, fontWeight: '600', color: colors.textMuted },

  // Section header
  sectionLabelRow: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.sm,
    marginTop: spacing.xxl, marginBottom: spacing.md,
  },
  accentBar: { width: 24, height: 2, backgroundColor: colors.emerald },
  sectionLabel: {
    fontSize: 11, letterSpacing: 1.6, fontWeight: '700', color: colors.text,
    textTransform: 'uppercase',
  },
  sectionSub: { ...type.bodySm, color: colors.textMuted, marginTop: -spacing.xs, marginBottom: spacing.md },

  // Why-now card (big editorial quote)
  whyCard: {
    backgroundColor: colors.text,
    borderRadius: radii.lg,
    padding: spacing.xl,
    marginBottom: spacing.md,
  },
  whyKicker: {
    fontSize: 10, letterSpacing: 1.8, fontWeight: '700',
    color: colors.bg, opacity: 0.6, marginBottom: spacing.sm,
  },
  whyText: { color: colors.bg, fontSize: 18, lineHeight: 26, fontWeight: '500' },

  // Consumer card
  consumerCard: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.xl,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
  },
  consumerKicker: {
    fontSize: 10, letterSpacing: 1.6, fontWeight: '700',
    color: colors.textSubtle, marginBottom: spacing.sm,
  },
  consumerText: { ...type.body, color: colors.text, lineHeight: 24 },

  // Commentary
  commentaryText: { ...type.body, color: colors.text, lineHeight: 24 },

  // Brand carousel
  brandStrip: { paddingRight: spacing.xl, gap: spacing.md, paddingVertical: spacing.sm },
  brandCard: {
    width: 232,
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
    minHeight: 168,
  },
  brandCardTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  brandCardNum: {
    ...type.caption, color: colors.textSubtle, fontSize: 10, letterSpacing: 1,
  },
  brandCardName: {
    fontSize: 22, fontWeight: '700', color: colors.text,
    letterSpacing: -0.4, marginTop: spacing.md,
  },
  brandCardRationale: {
    ...type.bodySm, color: colors.textMuted,
    marginTop: spacing.sm, lineHeight: 18,
  },

  // Price ladder
  ladderRow: {
    flexDirection: 'row', alignItems: 'stretch', gap: spacing.xs,
    marginTop: spacing.sm,
  },
  ladderCol: {
    flex: 1, padding: spacing.md, borderRadius: radii.md, minHeight: 110,
  },
  ladderColAnchor: { backgroundColor: colors.surface, borderWidth: StyleSheet.hairlineWidth, borderColor: colors.divider },
  ladderColFloor:  { backgroundColor: colors.surfaceMuted },
  ladderColTarget: { backgroundColor: colors.emerald },
  ladderArrow: { alignItems: 'center', justifyContent: 'center', width: 14 },
  ladderArrowText: { color: colors.textSubtle, fontSize: 18 },
  ladderTag: {
    fontSize: 9, letterSpacing: 1.2, fontWeight: '700',
    color: colors.textSubtle, marginBottom: spacing.sm,
  },
  ladderValue: { fontSize: 16, fontWeight: '700', color: colors.text, letterSpacing: -0.2 },
  ladderSub: { ...type.bodySm, fontSize: 11, color: colors.textMuted, marginTop: spacing.xs },
  ladderProse: {
    ...type.bodySm, color: colors.text, lineHeight: 20,
    marginTop: spacing.lg, paddingLeft: spacing.md,
    borderLeftWidth: 2, borderLeftColor: colors.emerald,
  },

  // India play
  indiaPlayCard: {
    marginTop: spacing.xl,
    backgroundColor: colors.emeraldSoft,
    borderRadius: radii.lg,
    padding: spacing.xl,
    borderLeftWidth: 4, borderLeftColor: colors.emerald,
  },
  indiaPlayKicker: {
    fontSize: 10, letterSpacing: 1.8, fontWeight: '700',
    color: colors.emeraldDeep, marginBottom: spacing.sm,
  },
  indiaPlayText: { ...type.body, color: colors.text, lineHeight: 24 },

  // Palette
  paletteStrip: { paddingRight: spacing.xl, gap: spacing.md, paddingVertical: spacing.sm },
  swatchWrap: { width: 76, alignItems: 'flex-start' },
  swatch: {
    width: 76, height: 92, borderRadius: radii.md,
    borderWidth: StyleSheet.hairlineWidth, borderColor: colors.divider,
  },
  swatchLabel: { ...type.bodySm, fontSize: 12, fontWeight: '600', color: colors.text, marginTop: 8 },
  swatchHex: { ...type.bodySm, fontSize: 10, color: colors.textSubtle, marginTop: 2, letterSpacing: 0.4 },

  // Ops (production + merchandising)
  opsRow: {
    flexDirection: Platform.OS === 'web' ? 'row' : 'column',
    gap: spacing.md, marginTop: spacing.sm,
  },
  opsCol: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.lg,
    borderTopWidth: 3, borderTopColor: colors.text,
  },
  opsKicker: {
    fontSize: 10, letterSpacing: 1.6, fontWeight: '700',
    color: colors.textMuted, marginBottom: spacing.sm,
  },
  opsText: { ...type.body, color: colors.text, lineHeight: 22 },

  // Direction cards
  dirCard: { borderRadius: radii.lg, marginBottom: spacing.md, overflow: 'hidden' },
  dirImageWrap: {
    width: '100%', height: 240,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  dirImage: { width: '100%', height: 240 },
  dirBody: { padding: spacing.xl },
  dirCardHead: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  dirCardGlyph: { fontSize: 18 },
  dirCardLabel: { ...type.caption, letterSpacing: 1.4, fontSize: 10, fontWeight: '700' },
  dirCardTitle: { ...type.h2, color: colors.text, marginTop: spacing.sm, fontSize: 22 },
  dirCardDesc: { ...type.body, color: colors.text, marginTop: spacing.sm, opacity: 0.85, lineHeight: 22 },
  dirMetaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.lg },
  dirMetaPill: {
    paddingHorizontal: 10, paddingVertical: 5, borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.7)',
  },
  dirMetaText: { ...type.bodySm, fontSize: 11, color: colors.text, fontWeight: '500' },
  refineBtn: {
    marginTop: spacing.lg,
    alignSelf: 'flex-start',
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderRadius: 999,
    backgroundColor: 'rgba(255,255,255,0.85)',
    borderWidth: StyleSheet.hairlineWidth, borderColor: 'rgba(0,0,0,0.1)',
  },
  refineBtnText: {
    ...type.bodySm, fontSize: 12, fontWeight: '600', color: colors.text,
  },

  // Refine modal
  modalBackdrop: {
    flex: 1, backgroundColor: 'rgba(15,15,14,0.55)',
    justifyContent: 'flex-end',
  },
  modalKeyboardWrap: { width: '100%' },
  modalSheet: {
    backgroundColor: colors.bg,
    borderTopLeftRadius: radii.lg, borderTopRightRadius: radii.lg,
    padding: spacing.xl, paddingBottom: spacing.xxl,
    maxHeight: '85%',
  },
  modalHandle: {
    width: 36, height: 4, borderRadius: 2,
    backgroundColor: colors.divider,
    alignSelf: 'center', marginBottom: spacing.lg,
  },
  modalKicker: {
    fontSize: 10, letterSpacing: 1.8, fontWeight: '700',
    color: colors.emerald, marginBottom: spacing.xs,
  },
  modalTitle: { ...type.h2, color: colors.text, marginBottom: spacing.sm },
  modalSubtle: { ...type.bodySm, color: colors.textMuted, marginBottom: spacing.lg, lineHeight: 18 },
  modalInput: {
    ...type.body, minHeight: 80,
    backgroundColor: colors.surface,
    borderRadius: radii.md, padding: spacing.md,
    borderWidth: StyleSheet.hairlineWidth, borderColor: colors.divider,
    color: colors.text, textAlignVertical: 'top',
    ...(Platform.OS === 'web' ? { outlineColor: colors.emerald } as any : {}),
  },
  modalError: { ...type.bodySm, color: colors.burgundy, marginTop: spacing.sm },
  modalChipRow: {
    flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.md,
  },
  modalChip: {
    paddingHorizontal: spacing.md, paddingVertical: spacing.sm,
    borderRadius: 999, backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth, borderColor: colors.divider,
  },
  modalChipText: { ...type.bodySm, fontSize: 12, color: colors.text },
  modalActions: {
    flexDirection: 'row', alignItems: 'center', gap: spacing.md,
    marginTop: spacing.xl,
  },
  modalCancel: { paddingHorizontal: spacing.md, paddingVertical: spacing.md },
  modalCancelText: { ...type.body, color: colors.textMuted, fontWeight: '600' },
  modalBusy: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'center',
    gap: spacing.sm, marginTop: spacing.md,
  },
  modalBusyText: { ...type.bodySm, color: colors.textMuted },

  // Detail drawer
  detailToggle: { alignSelf: 'center', paddingVertical: spacing.xl },
  detailToggleText: { ...type.bodySm, color: colors.emerald, fontWeight: '600' },
  detailCard: { backgroundColor: colors.surfaceMuted, borderRadius: radii.md, padding: spacing.lg },
  metaLine: { ...type.bodySm, color: colors.text, marginTop: spacing.xs },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: spacing.sm },
  chip: {
    paddingHorizontal: 10, paddingVertical: 4, borderRadius: 999,
    backgroundColor: colors.bg,
    borderWidth: StyleSheet.hairlineWidth, borderColor: colors.divider,
  },
  chipText: { ...type.bodySm, fontSize: 11, color: colors.text },
  citeBlock: { marginTop: spacing.sm },
  citeBrand: { ...type.bodySm, fontWeight: '600', color: colors.text },
  citeLink: { ...type.bodySm, fontSize: 11, color: colors.emerald, textDecorationLine: 'underline', marginTop: 2 },
  readBlock: { paddingVertical: spacing.md, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.divider, marginTop: spacing.sm },
  readHead: { ...type.h3, color: colors.text, marginBottom: spacing.xs },
  readRow: { flexDirection: 'row', marginTop: 4 },
  readRowLabel: { ...type.bodySm, fontSize: 11, color: colors.textSubtle, width: 80, textTransform: 'uppercase', letterSpacing: 0.5 },
  readRowValue: { ...type.bodySm, color: colors.text, flex: 1 },

  ctaRow: { marginTop: spacing.xl },

  // Data-source banner
  dataBanner: {
    borderRadius: radii.md,
    padding: spacing.lg,
    borderLeftWidth: 3,
  },
  dataBannerWarn: { backgroundColor: colors.burgundySoft, borderLeftColor: colors.burgundy },
  dataBannerInfo: { backgroundColor: colors.surfaceMuted, borderLeftColor: colors.textMuted },
  dataBannerKicker: {
    fontSize: 10, letterSpacing: 1.6, fontWeight: '700',
    color: colors.text, marginBottom: spacing.xs,
  },
  dataBannerText: { ...type.bodySm, color: colors.text, lineHeight: 18 },

  // Per-category
  byCatLead: { ...type.bodySm, color: colors.textMuted, marginBottom: spacing.sm },
  groupHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  groupLabel: { ...type.h2, color: colors.text },
  groupCount: { ...type.bodySm, fontSize: 11, color: colors.textSubtle, textTransform: 'uppercase', letterSpacing: 0.6 },
  groupObs: { ...type.h3, color: colors.text, marginTop: spacing.sm },
  groupSummary: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.xs },
  groupBrands: { marginTop: spacing.md, gap: 6 },
  groupBrandRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  groupBrandName: { ...type.body, color: colors.text },
  groupCommentary: { ...type.bodySm, color: colors.text, marginTop: spacing.md, lineHeight: 22 },
});
