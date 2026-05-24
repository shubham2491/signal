import React, { useMemo } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { colors, radii, spacing, type } from '@/theme';
import type { RootStackParamList } from '@/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'UploadPreview'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'UploadPreview'>;

const HERO_HEIGHT = 380;

export function UploadPreviewScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { images } = route.params;

  const detected = useMemo(() => guessMode(images.length), [images.length]);
  const lead = images[0];
  const rest = images.slice(1);

  return (
    <SafeAreaView style={styles.container} edges={['left', 'right']}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        {/* Hero lead image with floating chrome */}
        <View style={styles.hero}>
          <Image source={{ uri: lead.uri }} style={styles.heroImg} resizeMode="cover" />
          <View style={styles.heroOverlay} />
          <SafeAreaView edges={['top']} style={styles.heroChromeWrap} pointerEvents="box-none">
            <View style={styles.heroChrome}>
              <Pressable onPress={() => nav.goBack()} style={styles.chip} hitSlop={12}>
                <Text style={styles.chipText}>← Back</Text>
              </Pressable>
              <View style={styles.chip}>
                <Text style={styles.chipText}>{images.length} image{images.length === 1 ? '' : 's'}</Text>
              </View>
            </View>
          </SafeAreaView>

          <View style={styles.heroBottom}>
            <Text style={styles.heroKicker}>WE DETECTED</Text>
            <Text style={styles.heroTitle}>{detected.label}</Text>
            <Text style={styles.heroDesc}>{detected.desc}</Text>
          </View>
        </View>

        {/* Additional images strip */}
        {rest.length > 0 ? (
          <View style={styles.gridWrap}>
            <Text style={styles.gridLabel}>Also included</Text>
            <View style={styles.grid}>
              {rest.map((img, idx) => (
                <Image key={img.uri + idx} source={{ uri: img.uri }} style={styles.gridTile} />
              ))}
            </View>
          </View>
        ) : null}

        {/* What you'll get teaser */}
        <View style={styles.tease}>
          <Text style={styles.teaseLabel}>WHAT YOU'LL GET</Text>
          <View style={styles.teaseList}>
            <Text style={styles.teaseItem}>◆  International aspirational anchors</Text>
            <Text style={styles.teaseItem}>◆  Consumer profile + occasion read</Text>
            <Text style={styles.teaseItem}>◆  INR price ladder · anchor → floor → MRP</Text>
            <Text style={styles.teaseItem}>◆  How-to-launch in India (distribution + timing)</Text>
            <Text style={styles.teaseItem}>◆  Three design routes, sized for production</Text>
          </View>
        </View>

        <View style={styles.actions}>
          <Pressable onPress={() => nav.goBack()} style={({ pressed }) => [styles.changeLink, pressed && { opacity: 0.5 }]}>
            <Text style={styles.changeText}>Change selection</Text>
          </Pressable>
          <Button
            label={`Analyze ${images.length === 1 ? 'Image' : `${images.length} Images`}`}
            onPress={() => nav.navigate('Analysis', { images })}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

function guessMode(count: number): { label: string; desc: string } {
  if (count === 1) return { label: 'Single Image', desc: "We'll read one piece for the full translation brief." };
  if (count <= 4) return { label: 'Product Study', desc: 'A small set — we read each, then synthesise.' };
  if (count <= 7) return { label: 'Assortment Review', desc: "We'll group by category and brief each one." };
  return { label: 'Store Walk', desc: "Big set — we'll read it like a competitive shelf scan." };
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { paddingBottom: spacing.xxxl },

  hero: { width: '100%', height: HERO_HEIGHT, backgroundColor: colors.text, position: 'relative' },
  heroImg: { ...StyleSheet.absoluteFillObject, width: '100%', height: HERO_HEIGHT },
  heroOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(15,15,14,0.45)' },
  heroChromeWrap: { position: 'absolute', top: 0, left: 0, right: 0 },
  heroChrome: {
    flexDirection: 'row', justifyContent: 'space-between',
    paddingHorizontal: spacing.lg, paddingTop: spacing.md,
  },
  chip: {
    paddingHorizontal: spacing.md, height: 36, borderRadius: 18,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center', justifyContent: 'center',
  },
  chipText: { color: '#fff', fontSize: 13, fontWeight: '600' },

  heroBottom: {
    position: 'absolute', left: 0, right: 0, bottom: 0,
    paddingHorizontal: spacing.xl, paddingBottom: spacing.xl,
  },
  heroKicker: {
    color: 'rgba(255,255,255,0.7)', fontSize: 11, letterSpacing: 1.8,
    fontWeight: '600', marginBottom: spacing.sm,
  },
  heroTitle: {
    color: '#fff', fontSize: 36, lineHeight: 40, fontWeight: '700', letterSpacing: -1,
  },
  heroDesc: {
    color: 'rgba(255,255,255,0.85)', fontSize: 14, lineHeight: 20, marginTop: spacing.sm,
  },

  gridWrap: { paddingHorizontal: spacing.xl, marginTop: spacing.xl },
  gridLabel: {
    fontSize: 11, letterSpacing: 1.6, fontWeight: '700',
    color: colors.textMuted, marginBottom: spacing.md, textTransform: 'uppercase',
  },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  gridTile: { width: 76, height: 76, borderRadius: radii.sm, backgroundColor: colors.surfaceMuted },

  tease: {
    marginTop: spacing.xl, paddingHorizontal: spacing.xl,
  },
  teaseLabel: {
    fontSize: 11, letterSpacing: 1.6, fontWeight: '700',
    color: colors.textMuted, marginBottom: spacing.md, textTransform: 'uppercase',
  },
  teaseList: {
    backgroundColor: colors.surface, borderRadius: radii.lg,
    padding: spacing.lg, gap: spacing.sm,
    borderLeftWidth: 3, borderLeftColor: colors.emerald,
  },
  teaseItem: { ...type.body, color: colors.text, fontSize: 14 },

  actions: { paddingHorizontal: spacing.xl, paddingTop: spacing.xl },
  changeLink: { alignSelf: 'center', paddingVertical: spacing.md, marginBottom: spacing.sm },
  changeText: { ...type.bodySm, color: colors.textMuted, textDecorationLine: 'underline' },
});
