import React, { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';

import { Kicker } from '@/components/Kicker';
import { Card } from '@/components/Card';
import { colors, radii, spacing, type } from '@/theme';
import { loadHistory, type HistoryEntry } from '@/storage/history';

export function ProfileScreen() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);

  useEffect(() => {
    loadHistory().then(setEntries).catch(() => {});
  }, []);

  const analysisCount = entries.length;
  const imageCount = entries.reduce((n, e) => n + (e.report.image_count || 0), 0);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <StatusBar style="dark" />
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scroll}>
        <Kicker>Profile</Kicker>
        <Text style={styles.name}>Designer</Text>
        <Text style={styles.tagline}>Your SIGNAL workspace.</Text>

        <View style={styles.statsRow}>
          <Card flat style={styles.statCard}>
            <Text style={styles.statValue}>{analysisCount}</Text>
            <Text style={styles.statLabel}>ANALYSES</Text>
          </Card>
          <Card flat style={styles.statCard}>
            <Text style={styles.statValue}>{imageCount}</Text>
            <Text style={styles.statLabel}>IMAGES</Text>
          </Card>
        </View>

        <Card style={{ marginTop: spacing.lg }}>
          <Kicker>Settings</Kicker>
          <Row label="Backend" value="Connected" />
          <Row label="Privacy" value="Identity-blind, in-memory only" />
          <Row label="Region focus" value="India · Value + Mid-Premium" />
        </Card>

        <Card style={{ marginTop: spacing.lg }}>
          <Kicker>Coming soon</Kicker>
          <Row label="Cross-trip patterns" value="—" />
          <Row label="Voice notes per image" value="—" />
          <Row label="Team folders" value="—" />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={styles.rowValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: spacing.xl, paddingBottom: spacing.xxxl },
  name: { ...type.display, fontSize: 36, color: colors.text, marginTop: spacing.sm },
  tagline: { ...type.body, color: colors.textMuted, marginTop: spacing.xs },
  statsRow: {
    flexDirection: 'row',
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  statCard: {
    flex: 1,
    backgroundColor: colors.emeraldSoft,
    borderRadius: radii.md,
    padding: spacing.lg,
    alignItems: 'flex-start',
  },
  statValue: { ...type.display, fontSize: 36, color: colors.emerald },
  statLabel: { ...type.caption, color: colors.emerald, marginTop: 2 },
  row: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: spacing.sm },
  rowLabel: { ...type.body, color: colors.textMuted },
  rowValue: { ...type.body, color: colors.text, fontWeight: '500', textAlign: 'right', maxWidth: '60%' },
});
