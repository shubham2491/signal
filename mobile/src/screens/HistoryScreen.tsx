import React, { useCallback, useEffect, useState } from 'react';
import { Alert, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect, useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Card } from '@/components/Card';
import { ImageCollage } from '@/components/ImageCollage';
import { Kicker } from '@/components/Kicker';
import { ScreenHeader } from '@/components/ScreenHeader';
import { colors, radii, spacing, type } from '@/theme';
import { clearHistory, groupByDay, loadHistory, removeEntry, type HistoryEntry } from '@/storage/history';
import type { RootStackParamList } from '@/navigation';

// History sits in the Tab navigator but pushes Results, which lives in the
// root stack — so we just type against the root stack for navigation calls.
type Nav = NativeStackNavigationProp<RootStackParamList, 'Results'>;

type Section = { label: string; items: HistoryEntry[] };

export function HistoryScreen() {
  const nav = useNavigation<Nav>();
  const [sections, setSections] = useState<Section[]>([]);

  const reload = useCallback(async () => {
    const all = await loadHistory();
    setSections(groupByDay(all));
  }, []);

  useFocusEffect(useCallback(() => { reload(); }, [reload]));

  useEffect(() => { reload(); }, [reload]);

  const isEmpty = sections.length === 0;

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <ScreenHeader
        title="History"
        right={
          isEmpty ? null : (
            <Pressable
              hitSlop={12}
              onPress={() => {
                Alert.alert('Clear history?', 'Removes all saved analyses on this device.', [
                  { text: 'Cancel', style: 'cancel' },
                  {
                    text: 'Clear',
                    style: 'destructive',
                    onPress: async () => { await clearHistory(); reload(); },
                  },
                ]);
              }}
            >
              <Text style={styles.clearLink}>Clear</Text>
            </Pressable>
          )
        }
      />

      {isEmpty ? (
        <View style={styles.empty}>
          <Text style={styles.emptyTitle}>Nothing scanned yet</Text>
          <Text style={styles.emptyBody}>Your past briefs will live here, organised by day.</Text>
        </View>
      ) : (
        <FlatList
          data={sections}
          keyExtractor={(s) => s.label}
          contentContainerStyle={{ paddingHorizontal: spacing.xl, paddingBottom: spacing.xxxl }}
          ItemSeparatorComponent={() => <View style={{ height: spacing.lg }} />}
          renderItem={({ item: section }) => (
            <View>
              <Kicker>{section.label}</Kicker>
              <View style={{ height: spacing.sm }} />
              {section.items.map((entry) => (
                <Pressable
                  key={entry.id}
                  onPress={() => nav.navigate('Results', { report: entry.report, thumbnails: entry.thumbnails })}
                  onLongPress={() => {
                    Alert.alert('Remove?', entry.observation, [
                      { text: 'Cancel', style: 'cancel' },
                      {
                        text: 'Remove',
                        style: 'destructive',
                        onPress: async () => { await removeEntry(entry.id); reload(); },
                      },
                    ]);
                  }}
                  style={({ pressed }) => [pressed && { opacity: 0.7 }, { marginBottom: spacing.md }]}
                >
                  <Card flat style={styles.entryCard}>
                    <ImageCollage uris={entry.thumbnails} size={72} radius={radii.md} />
                    <View style={styles.entryText}>
                      <Text style={styles.entryTitle} numberOfLines={2}>{entry.observation}</Text>
                      <Text style={styles.entryMeta}>
                        {formatMode(entry.mode)} · {entry.imageCount} image{entry.imageCount === 1 ? '' : 's'}
                      </Text>
                    </View>
                  </Card>
                </Pressable>
              ))}
            </View>
          )}
        />
      )}
    </SafeAreaView>
  );
}

function formatMode(m: string): string {
  return m.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  clearLink: { ...type.bodySm, color: colors.burgundy },

  empty: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingHorizontal: spacing.xl },
  emptyTitle: { ...type.h2, color: colors.text, marginBottom: spacing.xs },
  emptyBody: { ...type.body, color: colors.textMuted, textAlign: 'center' },

  entryCard: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radii.md,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
  },
  entryText: { flex: 1, marginLeft: spacing.md },
  entryTitle: { ...type.h3, color: colors.text },
  entryMeta: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.xs },
});
