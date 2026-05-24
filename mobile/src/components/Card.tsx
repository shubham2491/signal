import React from 'react';
import { StyleSheet, View, ViewStyle } from 'react-native';
import { colors, radii, shadow, spacing } from '@/theme';

export function Card({
  children,
  style,
  flat = false,
}: {
  children: React.ReactNode;
  style?: ViewStyle | ViewStyle[];
  flat?: boolean;
}) {
  return (
    <View style={[styles.base, !flat && shadow.card, style]}>{children}</View>
  );
}

const styles = StyleSheet.create({
  base: {
    backgroundColor: colors.surface,
    borderRadius: radii.lg,
    padding: spacing.xl,
  },
});
