import React from 'react';
import { StyleSheet, Text } from 'react-native';
import { colors, type } from '@/theme';

export function Kicker({ children, color }: { children: React.ReactNode; color?: string }) {
  return <Text style={[styles.kicker, color ? { color } : null]}>{children}</Text>;
}

const styles = StyleSheet.create({
  kicker: {
    ...type.caption,
    color: colors.textMuted,
    textTransform: 'uppercase',
  },
});
