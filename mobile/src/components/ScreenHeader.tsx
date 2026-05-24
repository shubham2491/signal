import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors, spacing, type } from '@/theme';

export function ScreenHeader({
  title,
  onBack,
  right,
}: {
  title?: string;
  onBack?: () => void;
  right?: React.ReactNode;
}) {
  return (
    <View style={styles.row}>
      <View style={styles.side}>
        {onBack ? (
          <Pressable onPress={onBack} hitSlop={12} style={({ pressed }) => [pressed && { opacity: 0.5 }]}>
            <Text style={styles.chev}>{'←'}</Text>
          </Pressable>
        ) : null}
      </View>
      <View style={styles.center}>
        {title ? <Text style={styles.title}>{title}</Text> : null}
      </View>
      <View style={[styles.side, { alignItems: 'flex-end' }]}>{right}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
  },
  side: { width: 48 },
  center: { flex: 1, alignItems: 'center' },
  title: { ...type.h3, color: colors.text },
  chev: { fontSize: 22, color: colors.text },
});
