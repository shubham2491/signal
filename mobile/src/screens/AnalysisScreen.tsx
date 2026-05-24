import React, { useEffect, useRef, useState } from 'react';
import { Animated, Easing, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, CommonActions } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { Kicker } from '@/components/Kicker';
import { colors, radii, spacing, type } from '@/theme';
import { analyze } from '@/api/client';
import { appendEntry } from '@/storage/history';
import type { RootStackParamList } from '@/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Analysis'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'Analysis'>;

const STEPS = [
  'Reading images',
  'Detecting context',
  'Selecting brand cohort',
  'Pulling live retailer signals',
  'Writing the brief',
];

export function AnalysisScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { images } = route.params;

  const [stepIdx, setStepIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const pulse = useRef(new Animated.Value(0)).current;

  // Drive the visual step ticker independently of the network call.
  useEffect(() => {
    let cancelled = false;
    let i = 0;
    const tick = () => {
      if (cancelled) return;
      i = Math.min(i + 1, STEPS.length - 1);
      setStepIdx(i);
      if (i < STEPS.length - 1) setTimeout(tick, 1400);
    };
    const t = setTimeout(tick, 900);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, []);

  // Pulse animation on the active dot
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 900, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
      ]),
    ).start();
  }, [pulse]);

  // The actual API call
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const report = await analyze(images);
        if (cancelled) return;
        const thumbnails = images.slice(0, 6).map(i => i.uri);
        await appendEntry({
          id: report.id,
          createdAt: Date.now(),
          thumbnails,
          imageCount: images.length,
          mode: report.mode,
          observation: report.observation,
          report,
        });
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
        nav.dispatch(
          CommonActions.reset({
            index: 1,
            routes: [
              { name: 'Home' },
              { name: 'Results', params: { report, thumbnails } },
            ],
          }),
        );
      } catch (e: any) {
        if (cancelled) return;
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error).catch(() => {});
        setError(e?.message ?? 'Analysis failed.');
      }
    })();
    return () => { cancelled = true; };
  }, [images, nav]);

  const dotScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.6] });
  const dotOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 0.3] });

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      <View style={styles.body}>
        <Kicker>Analyzing</Kicker>
        <Text style={styles.title}>Reading the floor</Text>

        <View style={styles.steps}>
          {STEPS.map((step, i) => {
            const state =
              i < stepIdx ? 'done' : i === stepIdx ? 'active' : 'pending';
            return (
              <View key={step} style={styles.stepRow}>
                <View style={styles.dotWrap}>
                  {state === 'active' ? (
                    <Animated.View
                      style={[styles.dot, styles.dotActive, { transform: [{ scale: dotScale }], opacity: dotOpacity }]}
                    />
                  ) : null}
                  <View
                    style={[
                      styles.dot,
                      state === 'done' && styles.dotDone,
                      state === 'active' && styles.dotActive,
                      state === 'pending' && styles.dotPending,
                    ]}
                  />
                </View>
                <Text
                  style={[
                    styles.stepLabel,
                    state === 'done' && styles.stepDone,
                    state === 'active' && styles.stepActive,
                    state === 'pending' && styles.stepPending,
                  ]}
                >
                  {step}
                </Text>
              </View>
            );
          })}
        </View>

        {error ? (
          <View style={styles.errorBox}>
            <Text style={styles.errorTitle}>Something went wrong</Text>
            <Text style={styles.errorText}>{error}</Text>
            <Text style={styles.errorHint} onPress={() => nav.goBack()}>
              Go back
            </Text>
          </View>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  body: { flex: 1, paddingHorizontal: spacing.xl, justifyContent: 'center' },
  title: { ...type.h1, color: colors.text, marginTop: spacing.xs, marginBottom: spacing.xxl },
  steps: { gap: spacing.lg },
  stepRow: { flexDirection: 'row', alignItems: 'center' },
  dotWrap: { width: 24, alignItems: 'center', justifyContent: 'center', marginRight: spacing.md },
  dot: { width: 8, height: 8, borderRadius: 4, position: 'absolute' },
  dotPending: { backgroundColor: colors.divider },
  dotActive: { backgroundColor: colors.emerald },
  dotDone: { backgroundColor: colors.text },
  stepLabel: { ...type.body },
  stepPending: { color: colors.textSubtle },
  stepActive: { color: colors.text, fontWeight: '600' },
  stepDone: { color: colors.textMuted },
  errorBox: {
    marginTop: spacing.xxl,
    padding: spacing.lg,
    borderRadius: radii.md,
    backgroundColor: colors.burgundySoft,
  },
  errorTitle: { ...type.h3, color: colors.burgundy, marginBottom: spacing.xs },
  errorText: { ...type.bodySm, color: colors.text },
  errorHint: { ...type.bodySm, color: colors.burgundy, marginTop: spacing.md, textDecorationLine: 'underline' },
});
