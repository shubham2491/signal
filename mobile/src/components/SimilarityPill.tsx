import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import type { Similarity } from '@/api/client';
import { colors, radii, type } from '@/theme';

const palette: Record<Similarity, { bg: string; fg: string }> = {
  Strong:   { bg: colors.emeraldSoft, fg: colors.emerald },
  Adjacent: { bg: '#EFEAE0',          fg: colors.text },
  Moderate: { bg: '#EFEAE0',          fg: colors.textMuted },
  Weak:     { bg: '#F4EFE5',          fg: colors.textSubtle },
};

export function SimilarityPill({ value }: { value: Similarity }) {
  const c = palette[value];
  return (
    <View style={[styles.pill, { backgroundColor: c.bg }]}>
      <Text style={[styles.label, { color: c.fg }]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  pill: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: radii.pill,
    alignSelf: 'flex-start',
  },
  label: { ...type.caption, fontWeight: '600' },
});
