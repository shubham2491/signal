import React, { useEffect, useRef, useState } from 'react';
import { Animated, Easing, Image, Platform, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute, CommonActions } from '@react-navigation/native';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { colors, radii, spacing, type } from '@/theme';
import { analyze } from '@/api/client';
import { appendEntry } from '@/storage/history';
import type { RootStackParamList } from '@/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Analysis'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'Analysis'>;

const STEPS = [
  { label: 'Reading the shoot',         glyph: '◐' },
  { label: 'Pulling brand signals',     glyph: '◑' },
  { label: 'Mapping the consumer',      glyph: '◒' },
  { label: 'Sizing the price ladder',   glyph: '◓' },
  { label: 'Drafting the brief',        glyph: '◉' },
];

export function AnalysisScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { images } = route.params;

  const [stepIdx, setStepIdx] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const pulse = useRef(new Animated.Value(0)).current;
  const heroFade = useRef(new Animated.Value(0)).current;

  // Fade hero in on mount
  useEffect(() => {
    Animated.timing(heroFade, {
      toValue: 1, duration: 600, easing: Easing.out(Easing.ease), useNativeDriver: true,
    }).start();
  }, [heroFade]);

  // Step ticker
  useEffect(() => {
    let cancelled = false;
    let i = 0;
    const tick = () => {
      if (cancelled) return;
      i = Math.min(i + 1, STEPS.length - 1);
      setStepIdx(i);
      if (i < STEPS.length - 1) setTimeout(tick, 1600);
    };
    const t = setTimeout(tick, 1000);
    return () => { cancelled = true; clearTimeout(t); };
  }, []);

  // Pulse loop
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1100, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulse, { toValue: 0, duration: 1100, easing: Easing.inOut(Easing.ease), useNativeDriver: true }),
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
        const thumbnails = images.slice(0, 6).map((i) => i.uri);
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
              { name: 'Tabs' },
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

  const pulseOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.4, 1] });
  const pulseScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.05] });
  const ringScale = pulse.interpolate({ inputRange: [0, 1], outputRange: [1, 1.5] });
  const ringOpacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.6, 0] });

  const lead = images[0]?.uri;

  return (
    <View style={styles.container}>
      {/* Cinematic background: blurred uploaded image */}
      {lead ? (
        <Animated.View style={[StyleSheet.absoluteFill, { opacity: heroFade }]}>
          <Image
            source={{ uri: lead }}
            style={[styles.bgImg, Platform.OS === 'web' ? ({ filter: 'blur(28px)' } as any) : null]}
            resizeMode="cover"
          />
          <View style={styles.bgOverlay} />
        </Animated.View>
      ) : (
        <View style={[StyleSheet.absoluteFill, { backgroundColor: colors.text }]} />
      )}

      <SafeAreaView style={styles.safe} edges={['top', 'left', 'right', 'bottom']}>
        <View style={styles.body}>
          {/* Center: pulsing emblem + active step label */}
          <View style={styles.center}>
            <View style={styles.emblemWrap}>
              <Animated.View
                style={[styles.ring, { opacity: ringOpacity, transform: [{ scale: ringScale }] }]}
              />
              <Animated.View style={[styles.emblem, { opacity: pulseOpacity, transform: [{ scale: pulseScale }] }]}>
                <Text style={styles.emblemText}>{STEPS[stepIdx].glyph}</Text>
              </Animated.View>
            </View>

            <Text style={styles.kicker}>SIGNAL · ANALYSING</Text>
            <Text style={styles.activeStep}>{STEPS[stepIdx].label}</Text>
            <Text style={styles.subtle}>
              Translating an international read into an India brief.
            </Text>
          </View>

          {/* Bottom: step list */}
          <View style={styles.stepsList}>
            {STEPS.map((s, i) => {
              const done = i < stepIdx;
              const active = i === stepIdx;
              return (
                <View key={s.label} style={styles.stepRow}>
                  <View style={[styles.dot, done && styles.dotDone, active && styles.dotActive]} />
                  <Text style={[styles.stepText, active && styles.stepTextActive, done && styles.stepTextDone]}>
                    {s.label}
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
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.text },
  bgImg: { ...StyleSheet.absoluteFillObject, width: '100%', height: '100%' },
  bgOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(10,10,9,0.72)' },
  safe: { flex: 1 },
  body: { flex: 1, paddingHorizontal: spacing.xl, paddingVertical: spacing.xxl, justifyContent: 'space-between' },

  center: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  emblemWrap: { width: 120, height: 120, alignItems: 'center', justifyContent: 'center', marginBottom: spacing.xl },
  ring: {
    position: 'absolute', width: 120, height: 120, borderRadius: 60,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.45)',
  },
  emblem: {
    width: 92, height: 92, borderRadius: 46,
    backgroundColor: 'rgba(255,255,255,0.12)',
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.25)',
  },
  emblemText: { color: '#fff', fontSize: 36 },

  kicker: { color: 'rgba(255,255,255,0.55)', fontSize: 11, letterSpacing: 2, fontWeight: '700' },
  activeStep: {
    color: '#fff', fontSize: 30, lineHeight: 36, fontWeight: '700',
    letterSpacing: -0.6, marginTop: spacing.md, textAlign: 'center',
  },
  subtle: { color: 'rgba(255,255,255,0.7)', fontSize: 13, marginTop: spacing.sm, textAlign: 'center', maxWidth: 280 },

  stepsList: { gap: spacing.md, paddingHorizontal: spacing.sm },
  stepRow: { flexDirection: 'row', alignItems: 'center', gap: spacing.md },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.2)' },
  dotDone: { backgroundColor: 'rgba(255,255,255,0.55)' },
  dotActive: { backgroundColor: '#fff', width: 8, height: 8, borderRadius: 4 },
  stepText: { color: 'rgba(255,255,255,0.45)', fontSize: 14 },
  stepTextDone: { color: 'rgba(255,255,255,0.7)' },
  stepTextActive: { color: '#fff', fontWeight: '600' },

  errorBox: {
    padding: spacing.lg, borderRadius: radii.md,
    backgroundColor: colors.burgundySoft, marginTop: spacing.lg,
  },
  errorTitle: { ...type.h3, color: colors.burgundy, marginBottom: spacing.xs },
  errorText: { ...type.bodySm, color: colors.text },
  errorHint: { ...type.bodySm, color: colors.burgundy, marginTop: spacing.md, textDecorationLine: 'underline' },
});
