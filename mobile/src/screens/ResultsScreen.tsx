import React, { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
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
            <Kicker>Keywords</Kicker>
            <Text style={styles.kwLine}>{report.keywords.join('  ·  ')}</Text>
            <View style={{ height: spacing.lg }} />
            <Kicker>Per-Image Reads</Kicker>
            {report.reads.map((r) => (
              <View key={r.index} style={styles.readBlock}>
                <Text style={styles.readHead}>
                  Image {r.index + 1} — {r.attributes.category || 'apparel'}
                </Text>
                <Text style={styles.readMeta}>
                  {[r.attributes.silhouette, r.attributes.aesthetic, r.attributes.market_segment]
                    .filter(Boolean).join(' · ')}
                </Text>
                {r.attributes.colors.length ? (
                  <Text style={styles.readMeta}>Colors: {r.attributes.colors.join(', ')}</Text>
                ) : null}
                {r.attributes.fabric_guess ? (
                  <Text style={styles.readMeta}>Fabric: {r.attributes.fabric_guess}</Text>
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

  readBlock: { paddingVertical: spacing.sm },
  readHead: { ...type.h3, color: colors.text },
  readMeta: { ...type.bodySm, color: colors.textMuted, marginTop: 2 },

  ctaRow: { flexDirection: 'row', marginTop: spacing.lg, gap: spacing.md },
});
