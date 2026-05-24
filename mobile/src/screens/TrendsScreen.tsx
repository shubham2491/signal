import React, { useState } from 'react';
import {
  ActivityIndicator,
  Keyboard,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as Haptics from 'expo-haptics';
import { useNavigation, CommonActions } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Kicker } from '@/components/Kicker';
import { colors, radii, spacing, type as typo } from '@/theme';
import { analyzeBrief } from '@/api/client';
import { appendEntry } from '@/storage/history';
import type { RootStackParamList } from '@/navigation';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Results'>;

const SUGGESTIONS = [
  'Oversized utility, earth tones, SS26',
  'Y2K going-out, satin slip dresses, festive',
  'Quiet-luxury workwear, linen blazers, ecru palette',
  'Indo-fusion co-ord sets, hand-block prints',
  'Wide-leg denim, cropped tees, drop-shoulder',
];

export function TrendsScreen() {
  const nav = useNavigation<Nav>();
  const [brief, setBrief] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    const text = brief.trim();
    if (text.length < 4) {
      setError('Add a bit more detail — at least a few words.');
      return;
    }
    setError(null);
    setBusy(true);
    Keyboard.dismiss();
    try {
      const report = await analyzeBrief(text);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      await appendEntry({
        id: report.id,
        createdAt: Date.now(),
        thumbnails: [],
        imageCount: 0,
        mode: report.mode,
        observation: report.observation,
        report,
      });
      nav.dispatch(
        CommonActions.reset({
          index: 1,
          routes: [
            { name: 'Tabs' },
            { name: 'Results', params: { report, thumbnails: [] } },
          ],
        }),
      );
    } catch (e: any) {
      setError(e?.message ?? 'Could not analyse the brief.');
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
    } finally {
      setBusy(false);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <StatusBar style="dark" />
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={styles.scroll}
        keyboardShouldPersistTaps="handled"
      >
        <Kicker>Trends</Kicker>
        <Text style={styles.title}>Type the trend</Text>
        <Text style={styles.tagline}>
          Describe what you're chasing. SIGNAL will translate it into a brief
          you can hand to sampling.
        </Text>

        <Card style={{ marginTop: spacing.xl }}>
          <Kicker>Designer Brief</Kicker>
          <TextInput
            value={brief}
            onChangeText={(t) => { setBrief(t); if (error) setError(null); }}
            placeholder="Oversized utility, earth tones, SS26..."
            placeholderTextColor={colors.textSubtle}
            multiline
            numberOfLines={4}
            style={styles.input}
            editable={!busy}
          />
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <View style={{ height: spacing.md }} />
          <Button
            label={busy ? 'Analysing…' : 'Get the brief'}
            onPress={submit}
            loading={busy}
            disabled={busy}
          />
        </Card>

        <View style={{ marginTop: spacing.xl }}>
          <Kicker>Try one of these</Kicker>
          <View style={styles.suggestionGrid}>
            {SUGGESTIONS.map((s) => (
              <Pressable
                key={s}
                onPress={() => !busy && setBrief(s)}
                style={({ pressed }) => [styles.suggestionChip, pressed && { opacity: 0.7 }]}
              >
                <Text style={styles.suggestionText}>{s}</Text>
              </Pressable>
            ))}
          </View>
        </View>

        <Card flat style={[styles.comingSoonCard, { marginTop: spacing.xl }]}>
          <Kicker>Coming next</Kicker>
          <Text style={styles.subText}>
            ◯  Paste a Zara / COS / Uniqlo product URL → get the Indian translation
          </Text>
          <Text style={styles.subText}>
            ◯  Pinterest / Are.na mood board URL → full grouped analysis
          </Text>
          <Text style={styles.subText}>
            ◯  Color palette picker → match against current brand floors
          </Text>
        </Card>

        {busy ? (
          <View style={styles.busyOverlay}>
            <ActivityIndicator color={colors.emerald} />
            <Text style={styles.busyText}>Reading the floor…</Text>
          </View>
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  scroll: { padding: spacing.xl, paddingBottom: spacing.xxxl },
  title: { ...typo.display, fontSize: 36, color: colors.text, marginTop: spacing.sm },
  tagline: { ...typo.body, color: colors.textMuted, marginTop: spacing.sm, maxWidth: 320 },
  input: {
    ...typo.body,
    minHeight: 96,
    marginTop: spacing.sm,
    padding: spacing.md,
    borderRadius: radii.md,
    backgroundColor: colors.bg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
    color: colors.text,
    textAlignVertical: 'top',
    ...(Platform.OS === 'web' ? { outlineColor: colors.emerald } : {}),
  },
  error: { ...typo.bodySm, color: colors.burgundy, marginTop: spacing.sm },
  suggestionGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginTop: spacing.sm },
  suggestionChip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: radii.pill,
    backgroundColor: colors.surface,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: colors.divider,
  },
  suggestionText: { ...typo.bodySm, color: colors.text },
  comingSoonCard: { backgroundColor: colors.surfaceMuted },
  subText: { ...typo.bodySm, color: colors.textMuted, marginTop: spacing.sm },
  busyOverlay: {
    marginTop: spacing.xl,
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  busyText: { ...typo.bodySm, color: colors.textMuted },
});
