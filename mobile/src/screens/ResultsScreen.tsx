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
          nav.dispatch(CommonActions.reset({ index: 0, routes: [{ name: 'Home' }] }))
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

        {/* SECTION 2: Brand Signals */}
        <Card style={{ marginTop: spacing.lg }}>
          <Kicker>Brand Signals</Kicker>
          <View style={{ height: spacing.md }} />
          {report.brand_signals.map((sig, i) => (
            <View
              key={sig.brand}
              style={[
                styles.brandRow,
                i < report.brand_signals.length - 1 && styles.brandRowDivider,
              ]}
            >
              <View style={styles.brandHead}>
                <Text style={styles.brandName}>{sig.brand}</Text>
                <SimilarityPill value={sig.similarity} />
              </View>
              <Text style={styles.brandRationale}>{sig.rationale}</Text>
            </View>
          ))}
        </Card>

        {/* SECTION 3: Market Commentary */}
        {report.commentary ? (
          <Card style={{ marginTop: spacing.lg }}>
            <Kicker>Market Commentary</Kicker>
            <Text style={styles.commentary}>{report.commentary}</Text>
          </Card>
        ) : null}

        {/* SECTION 4: Recommended Directions */}
        <Card style={{ marginTop: spacing.lg }}>
          <Kicker>Recommended Directions</Kicker>
          <View style={{ height: spacing.sm }} />
          {report.directions.map((d, i) => (
            <View
              key={d.label}
              style={[
                styles.direction,
                i < report.directions.length - 1 && styles.directionDivider,
              ]}
            >
              <Text style={styles.dirLabel}>{d.label.toUpperCase()}</Text>
              <Text style={styles.dirTitle}>{d.title}</Text>
              <Text style={styles.dirDesc}>{d.description}</Text>
            </View>
          ))}
        </Card>

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

  brandRow: { paddingVertical: spacing.md },
  brandRowDivider: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.divider },
  brandHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  brandName: { ...type.h3, color: colors.text },
  brandRationale: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.xs },

  commentary: { ...type.body, color: colors.text, marginTop: spacing.sm, lineHeight: 24 },

  direction: { paddingVertical: spacing.md },
  directionDivider: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: colors.divider },
  dirLabel: { ...type.caption, color: colors.burgundy, letterSpacing: 1 },
  dirTitle: { ...type.h2, color: colors.text, marginTop: spacing.xs },
  dirDesc: { ...type.body, color: colors.textMuted, marginTop: spacing.xs },

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
});
