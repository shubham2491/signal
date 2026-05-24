import React, { useState } from 'react';
import { Alert, Linking, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation, useRoute } from '@react-navigation/native';
import * as Sharing from 'expo-sharing';
import * as Haptics from 'expo-haptics';
import type { NativeStackNavigationProp, NativeStackScreenProps } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { Kicker } from '@/components/Kicker';
import { ScreenHeader } from '@/components/ScreenHeader';
import { colors, radii, spacing, type } from '@/theme';
import { emailReport, exportReport } from '@/api/client';
import type { RootStackParamList } from '@/navigation';

type Props = NativeStackScreenProps<RootStackParamList, 'Export'>;
type Nav = NativeStackNavigationProp<RootStackParamList, 'Export'>;

export function ExportScreen() {
  const route = useRoute<Props['route']>();
  const nav = useNavigation<Nav>();
  const { report } = route.params;

  const [email, setEmail] = useState('');
  const [link, setLink] = useState<string | null>(null);
  const [busy, setBusy] = useState<'pdf' | 'email' | null>(null);

  const generatePdf = async () => {
    setBusy('pdf');
    try {
      const res = await exportReport(report);
      setLink(res.download_url);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    } catch (e: any) {
      Alert.alert('Export failed', e?.message ?? 'Try again.');
    } finally {
      setBusy(null);
    }
  };

  const sendEmail = async () => {
    if (!isEmail(email)) {
      Alert.alert('Invalid email', 'Enter a valid email address.');
      return;
    }
    setBusy('email');
    try {
      const res = await emailReport(report, email.trim());
      setLink(res.download_url);
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
      Alert.alert('PDF ready', res.message);
    } catch (e: any) {
      Alert.alert('Send failed', e?.message ?? 'Try again.');
    } finally {
      setBusy(null);
    }
  };

  const share = async () => {
    if (!link) return;
    if (Platform.OS === 'web') {
      Linking.openURL(link);
      return;
    }
    const available = await Sharing.isAvailableAsync();
    if (available) {
      // Sharing.shareAsync wants a file path; we share the URL via OS share for simplicity
      Linking.openURL(link);
    } else {
      Linking.openURL(link);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right', 'bottom']}>
      <ScreenHeader title="Export" onBack={() => nav.goBack()} />

      <View style={styles.body}>
        <Kicker>This brief</Kicker>
        <Text style={styles.title}>{report.observation}</Text>

        <Card style={styles.section}>
          <Kicker>PDF</Kicker>
          <Text style={styles.help}>Generate an editorial PDF you can save or share.</Text>
          <View style={{ height: spacing.md }} />
          <Button
            label={link ? 'Regenerate PDF' : 'Generate PDF'}
            onPress={generatePdf}
            loading={busy === 'pdf'}
            disabled={busy !== null && busy !== 'pdf'}
          />
        </Card>

        <Card style={styles.section}>
          <Kicker>Email</Kicker>
          <Text style={styles.help}>
            We'll prepare the PDF and surface a download link you can share with the recipient.
          </Text>
          <View style={{ height: spacing.md }} />
          <TextInput
            value={email}
            onChangeText={setEmail}
            placeholder="designer@brand.com"
            placeholderTextColor={colors.textSubtle}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="email-address"
            style={styles.input}
          />
          <View style={{ height: spacing.md }} />
          <Button
            label="Prepare for Email"
            variant="secondary"
            onPress={sendEmail}
            loading={busy === 'email'}
            disabled={busy !== null && busy !== 'email'}
          />
        </Card>

        {link ? (
          <Card flat style={[styles.section, { backgroundColor: colors.emeraldSoft }]}>
            <Kicker color={colors.emerald}>Download link</Kicker>
            <Text style={styles.link} numberOfLines={2}>{link}</Text>
            <View style={{ height: spacing.md }} />
            <Pressable onPress={share} style={({ pressed }) => [styles.shareBtn, pressed && { opacity: 0.7 }]}>
              <Text style={styles.shareText}>Open / Share</Text>
            </Pressable>
          </Card>
        ) : null}
      </View>
    </SafeAreaView>
  );
}

function isEmail(s: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(s.trim());
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg },
  body: { flex: 1, paddingHorizontal: spacing.xl },
  title: { ...type.h1, color: colors.text, marginTop: spacing.xs, marginBottom: spacing.lg },
  section: { marginBottom: spacing.lg },
  help: { ...type.bodySm, color: colors.textMuted, marginTop: spacing.xs },
  input: {
    ...type.body,
    color: colors.text,
    backgroundColor: colors.surfaceMuted,
    borderRadius: radii.md,
    paddingHorizontal: spacing.lg,
    height: 50,
  },
  link: { ...type.bodySm, color: colors.emerald, marginTop: spacing.xs },
  shareBtn: {
    alignSelf: 'flex-start',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.lg,
    borderRadius: radii.pill,
    backgroundColor: colors.emerald,
  },
  shareText: { ...type.bodySm, color: '#fff', fontWeight: '600' },
});
