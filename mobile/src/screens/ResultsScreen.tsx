import React, { useState } from 'react';
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, CommonActions } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ImageCollage } from '@/components/ImageCollage';
import { Kicker } from '@/components/Kicker';
import { ScreenHeader } from '@/components/ScreenHeader';
import { SimilarityPill } from '@/components/SimilarityPill';
import { colors, radii, spacing, type } from '@/theme';
import type { RootStackParamList } from '@/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Results'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'Results'>;

export function ResultsScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { report, thumbnails } = route.params;
  const [showDetail, setShowDetail] = useState(false);

  const modeLabel = report.mode.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScreenHeader
        onBack={() =>
          nav.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'Tabs' }] }))
        }
        right={
          <Pressable onPress={() => nav.navigate('Export', { report })} hitSlop={12}>
            <Text style={styles.exportLink}>Export</Text>
          </Pressable>
        }
      />

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
      >
        <View style={styles.heroRow}>
          <ImageCollage uris={thumbnails} size={88} />
          <View style={styles.heroText}>
            <Kicker>{modeLabel} · {report.image_count} image{report.image_count === 1 ? '' : 's'}</Kicker>
            <Text style={styles.observation}>{report.observation}</Text>
          </View>
        </View>

        {report.summary ? (
          <Text style={styles.summary}>{report.summary}</Text>
        ) : null}

        {/* SECTION 2: Brand Signals as a 2-col card grid */}
        <View style={{ marginTop: spacing.xl }}>
          <Kicker>Brand Signals</Kicker>
          <View style={styles.brandGrid}>
            {report.brand_signals.map((sig) => (
              <View key={sig.brand} style={styles.brandCard}>
                <Text style={styles.brandWordmark} numberOfLines={1}>{sig.brand}</Text>
                <View style={{ marginTop: spacing.xs }}>
                  <SimilarityPill value={sig.similarity} />
                </View>
                <Text style={styles.brandCardRationale} numberOfLines={3}>{sig.rationale}</Text>
              </View>
            ))}
          </View>
        </View>

        {/* SECTION 3: Market Commentary */}
        {report.commentary ? (
          <Card style={{ marginTop: spacing.lg }}>
            <Kicker>Market Commentary</Kicker>
            <Text style={styles.commentary}>{report.commentary}</Text>
          </Card>
        ) : null}

        {/* SECTION 4: Recommended Directions as tinted cards */}
        <View style={{ marginTop: spacing.xl }}>
          <Kicker>Recommended Directions</Kicker>
          <View style={{ height: spacing.md }} />
          {report.directions.map((d) => {
            const meta = DIRECTION_META[d.label] || DIRECTION_META.fallback;
            return (
              <View key={d.label} style={[styles.dirCard, { backgroundColor: meta.tint }]}>
                <View style={styles.dirCardHead}>
                  <Text style={[styles.dirCardLabel, { color: meta.color }]}>{meta.glyph}  {d.label.toUpperCase()}</Text>
                </View>
                <Text style={styles.dirCardTitle}>{d.title}</Text>
                <Text style={styles.dirCardDesc}>{d.description}</Text>
              </View>
            );
          })}
        </View>

        {/* SECTION 5: Per-category breakdown (only when multi-category upload) */}
        {report.groups && report.groups.length > 1 ? (
          <View style={{ marginTop: spacing.xl }}>
            <Kicker>By Category</Kicker>
            <Text style={styles.byCatLead}>
              We detected {report.groups.length} categories in your upload. Each gets its own
              brand signals and direction below.
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

                {g.commentary ? (
                  <Text style={styles.groupCommentary}>{g.commentary}</Text>
                ) : null}

                {g.directions.length ? (
                  <View style={styles.groupDirections}>
                    {g.directions.map((d) => (
                      <View key={d.label} style={styles.groupDirRow}>
                        <Text style={styles.groupDirLabel}>{d.label.toUpperCase()}</Text>
                        <Text style={styles.groupDirTitle}>{d.title}</Text>
                      </View>
                    ))}
                  </View>
                ) : null}
              </Card>
            ))}
          </View>
        ) : null}

        {/* Progressive disclosure: power-user detail layer */}
        <Pressable onPress={() => setShowDetail(v => !v)} style={styles.detailToggle}>
          <Text style={styles.detailToggleText}>
            {showDetail ? 'Hide full intelligence' : 'See full intelligence'}
          </Text>
        </Pressable>

        {showDetail ? (
          <Card flat style={[styles.detailCard, { marginBottom: spacing.xl }]}>
            {/* Detection meta */}
            <Kicker>Detection</Kicker>
            <Text style={styles.metaLine}>
              {modeLabel} · confidence {(report.mode_confidence * 100).toFixed(0)}%
              {'  ·  '}
              {report.image_count} image{report.image_count === 1 ? '' : 's'}
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

            {/* Per-brand citations */}
            {report.brand_signals.some(s => s.citations.length) ? (
              <>
                <View style={{ height: spacing.lg }} />
                <Kicker>Brand Citations</Kicker>
                {report.brand_signals.filter(s => s.citations.length).map((s) => (
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

            {/* Per-image full reads */}
            <View style={{ height: spacing.lg }} />
            <Kicker>Per-Image Reads ({report.reads.length})</Kicker>
            {report.reads.map((r) => (
              <View key={r.index} style={styles.readBlock}>
                <Text style={styles.readHead}>
                  Image {r.index + 1} — {r.attributes.category || 'apparel'}
                </Text>

                {r.attributes.silhouette ? (
                  <ReadRow label="Silhouette" value={r.attributes.silhouette} />
                ) : null}
                {r.attributes.fabric_guess ? (
                  <ReadRow label="Fabric" value={r.attributes.fabric_guess} />
                ) : null}
                {r.attributes.colors.length ? (
                  <ReadRow label="Colors" value={r.attributes.colors.join(', ')} />
                ) : null}
                {r.attributes.styling.length ? (
                  <ReadRow label="Styling" value={r.attributes.styling.join(', ')} />
                ) : null}
                {r.attributes.trims.length ? (
                  <ReadRow label="Trims" value={r.attributes.trims.join(', ')} />
                ) : null}
                {r.attributes.aesthetic ? (
                  <ReadRow label="Aesthetic" value={r.attributes.aesthetic} />
                ) : null}
                {r.attributes.market_segment ? (
                  <ReadRow label="Tier" value={r.attributes.market_segment} />
                ) : null}
                {r.attributes.notes ? (
                  <ReadRow label="Notes" value={r.attributes.notes} />
                ) : null}

                {r.keywords.length ? (
                  <View style={styles.miniChipRow}>
                    {r.keywords.map((k) => (
                      <View key={k} style={styles.miniChip}>
                        <Text style={styles.miniChipText}>{k}</Text>
                      </View>
                    ))}
                  </View>
                ) : null}
              </View>
            ))}
          </Card>
        ) : null}

        <View style={styles.ctaRow}>
          <Button
            label="Export Report"
            onPress={() => nav.navigate('Export', { report })}
            style={{ flex: 1 }}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const DIRECTION_META: Record<string, { tint: string; color: string; glyph: string }> = {
  'Safe Commercial':     { tint: colors.safeTint,  color: colors.emerald, glyph: '◆' },
  'Trend Forward':       { tint: colors.trendTint, color: colors.burgundy, glyph: '↗' },
  'Differentiated Route':{ tint: colors.diffTint,  color: colors.text,    glyph: '★' },
  fallback:              { tint: colors.surfaceMuted, color: colors.text, glyph: '◆' },
};

function ReadRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.readRow}>
      <Text style={styles.readRowLabel}>{label}</Text>
      <Text style={styles.readRowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { paddingHorizontal: spacing.xl, paddingBottom: spacing.xxxl },
  exportLink: { ...type.bodySm, color: colors.emerald, fontWeight: '600' },

  heroRow: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.lg },
  heroText: { flex: 1, marginLeft: spacing.lg },
  observation: { ...type.h1, color: colors.text, marginTop: spacing.xs },
  summary: { ...type.body, color: colors.textMuted, marginBottom: spacing.sm },

  // Brand grid
  brandGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.md,
    marginTop: spacing.md,
  },
  brandCard: {
    width: '47%',
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    padding: spacing.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
    minHeight: 132,
  },
  brandWordmark: {
    fontSize: 18,
    fontWeight: '700',
    color: colors.text,
    letterSpacing: -0.4,
  },
  brandCardRationale: {
    ...type.bodySm,
    fontSize: 12,
    color: colors.textMuted,
    marginTop: spacing.sm,
    lineHeight: 17,
  },

  commentary: { ...type.body, color: colors.text, marginTop: spacing.sm, lineHeight: 24 },

  // Tinted direction cards
  dirCard: {
    borderRadius: radii.md,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  dirCardHead: { flexDirection: 'row', alignItems: 'center' },
  dirCardLabel: { ...type.caption, letterSpacing: 1.2 },
  dirCardTitle: { ...type.h2, color: colors.text, marginTop: spacing.xs },
  dirCardDesc: { ...type.body, color: colors.text, marginTop: spacing.xs, opacity: 0.85 },

  detailToggle: { alignSelf: 'center', paddingVertical: spacing.lg },
  detailToggleText: { ...type.bodySm, color: colors.emerald, textDecorationLine: 'underline' },

  detailCard: {
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    padding: spacing.lg,
  },
  kwLine: { ...type.bodySm, color: colors.text, marginTop: spacing.xs },
  metaLine: { ...type.bodySm, color: colors.text, marginTop: spacing.xs },

  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginTop: spacing.sm,
  },
  chip: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 999,
    backgroundColor: colors.bg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
  },
  chipText: { ...type.bodySm, fontSize: 11, color: colors.text },

  miniChipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: spacing.sm,
  },
  miniChip: {
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 999,
    backgroundColor: colors.bg,
  },
  miniChipText: { ...type.bodySm, fontSize: 10, color: colors.textMuted },

  citeBlock: { marginTop: spacing.sm },
  citeBrand: { ...type.bodySm, fontWeight: '600', color: colors.text },
  citeLink: { ...type.bodySm, fontSize: 11, color: colors.emerald, textDecorationLine: 'underline', marginTop: 2 },

  readBlock: {
    paddingVertical: spacing.md,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.divider,
    marginTop: spacing.sm,
  },
  readHead: { ...type.h3, color: colors.text, marginBottom: spacing.xs },
  readRow: { flexDirection: 'row', marginTop: 4 },
  readRowLabel: { ...type.bodySm, fontSize: 11, color: colors.textSubtle, width: 80, textTransform: 'uppercase', letterSpacing: 0.5 },
  readRowValue: { ...type.bodySm, color: colors.text, flex: 1 },

  ctaRow: { flexDirection: 'row', marginTop: spacing.lg, gap: spacing.md },

  // Per-category breakdown
  byCatLead: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.sm, marginBottom: spacing.sm },
  groupHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline' },
  groupLabel: { ...type.h2, color: colors.text },
  groupCount: { ...type.bodySm, fontSize: 11, color: colors.textSubtle, textTransform: 'uppercase', letterSpacing: 0.6 },
  groupObs: { ...type.h3, color: colors.text, marginTop: spacing.sm },
  groupSummary: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.xs },
  groupBrands: { marginTop: spacing.md, gap: 6 },
  groupBrandRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  groupBrandName: { ...type.body, color: colors.text },
  groupCommentary: { ...type.bodySm, color: colors.text, marginTop: spacing.md, lineHeight: 22 },
  groupDirections: { marginTop: spacing.md, gap: spacing.sm },
  groupDirRow: { paddingTop: spacing.xs },
  groupDirLabel: { ...type.caption, color: colors.burgundy, letterSpacing: 0.8, fontSize: 10 },
  groupDirTitle: { ...type.bodySm, fontWeight: '600', color: colors.text, marginTop: 2 },
});
