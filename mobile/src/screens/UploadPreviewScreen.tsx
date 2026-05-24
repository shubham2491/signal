import React, { useMemo } from 'react';
import { FlatList, Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { Kicker } from '@/components/Kicker';
import { ScreenHeader } from '@/components/ScreenHeader';
import { colors, radii, spacing, type } from '@/theme';
import type { RootStackParamList } from '@/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'UploadPreview'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'UploadPreview'>;

export function UploadPreviewScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { images } = route.params;

  const detected = useMemo(() => guessMode(images.length), [images.length]);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      <ScreenHeader onBack={() => nav.goBack()} title="Preview" />

      <View style={styles.detect}>
        <Kicker>We detected</Kicker>
        <Text style={styles.detectTitle}>{detected.label}</Text>
        <Text style={styles.detectMeta}>
          {images.length} image{images.length === 1 ? '' : 's'} · we'll confirm after analysis
        </Text>
      </View>

      <FlatList
        data={images}
        keyExtractor={(item, idx) => `${item.uri}-${idx}`}
        numColumns={3}
        contentContainerStyle={styles.grid}
        columnWrapperStyle={{ gap: spacing.sm }}
        ItemSeparatorComponent={() => <View style={{ height: spacing.sm }} />}
        renderItem={({ item }) => (
          <Image source={{ uri: item.uri }} style={styles.tile} />
        )}
      />

      <View style={styles.actions}>
        <Pressable onPress={() => nav.goBack()} style={({ pressed }) => [styles.changeLink, pressed && { opacity: 0.5 }]}>
          <Text style={styles.changeText}>Change selection</Text>
        </Pressable>
        <Button
          label={`Analyze ${images.length === 1 ? 'Image' : `${images.length} Images`}`}
          onPress={() => nav.navigate('Analysis', { images })}
        />
      </View>
    </SafeAreaView>
  );
}

function guessMode(count: number): { label: string } {
  if (count === 1) return { label: 'Single Image' };
  if (count <= 4) return { label: 'Product Study' };
  if (count <= 7) return { label: 'Assortment Review' };
  return { label: 'Competitor Store Walk' };
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  detect: {
    paddingHorizontal: spacing.xl,
    paddingBottom: spacing.lg,
  },
  detectTitle: { ...type.h1, color: colors.text, marginTop: spacing.xs },
  detectMeta: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.xs },
  grid: { paddingHorizontal: spacing.xl, paddingBottom: spacing.lg, gap: spacing.sm },
  tile: {
    flex: 1 / 3,
    aspectRatio: 1,
    borderRadius: radii.md,
    backgroundColor: colors.surfaceMuted,
  },
  actions: { paddingHorizontal: spacing.xl, paddingBottom: spacing.lg, paddingTop: spacing.sm },
  changeLink: { alignSelf: 'center', paddingVertical: spacing.md },
  changeText: { ...type.bodySm, color: colors.textMuted, textDecorationLine: 'underline' },
});
