import React, { useCallback, useState } from 'react';
import { Alert, Platform, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar } from 'expo-status-bar';
import * as ImagePicker from 'expo-image-picker';
import * as Haptics from 'expo-haptics';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Button } from '@/components/Button';
import { Kicker } from '@/components/Kicker';
import { colors, radii, spacing, type } from '@/theme';
import type { RootStackParamList, SelectedImage } from '@/navigation';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Home'>;

export function HomeScreen() {
  const nav = useNavigation<Nav>();
  const [busy, setBusy] = useState<'camera' | 'library' | null>(null);

  const pickFromLibrary = useCallback(async () => {
    setBusy('library');
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert('Permission needed', 'Allow photo access to upload images.');
        return;
      }
      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        allowsMultipleSelection: true,
        selectionLimit: 24,
        quality: 0.9,
      });
      if (res.canceled || res.assets.length === 0) return;
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
      nav.navigate('UploadPreview', { images: res.assets.map(toSelected) });
    } finally {
      setBusy(null);
    }
  }, [nav]);

  const takePhoto = useCallback(async () => {
    setBusy('camera');
    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) {
        Alert.alert('Permission needed', 'Allow camera access to capture images.');
        return;
      }
      const res = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        quality: 0.9,
      });
      if (res.canceled || res.assets.length === 0) return;
      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium).catch(() => {});
      nav.navigate('UploadPreview', { images: res.assets.map(toSelected) });
    } finally {
      setBusy(null);
    }
  }, [nav]);

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <StatusBar style="dark" />

      <View style={styles.header}>
        <Pressable onPress={() => nav.navigate('History')} hitSlop={12}>
          <Text style={styles.headerLink}>History</Text>
        </Pressable>
      </View>

      <View style={styles.hero}>
        <Kicker>Fashion Signal Agent</Kicker>
        <Text style={styles.brand}>SIGNAL</Text>
        <Text style={styles.tagline}>
          Snap products. Understand what brands are doing. Decide what to design next.
        </Text>
      </View>

      <View style={styles.actions}>
        <Button
          label="Take Photo"
          onPress={takePhoto}
          loading={busy === 'camera'}
          disabled={busy !== null && busy !== 'camera'}
        />
        <View style={{ height: spacing.md }} />
        <Button
          label="Upload Images"
          variant="secondary"
          onPress={pickFromLibrary}
          loading={busy === 'library'}
          disabled={busy !== null && busy !== 'library'}
        />
        {Platform.OS === 'web' ? (
          <Text style={styles.pickerHint}>
            Tip: hold ⌘ (Mac) or Ctrl (Win) in the file dialog to select multiple images.
          </Text>
        ) : null}
      </View>

      <View style={styles.footer}>
        <Text style={styles.footerText}>
          Analysis focuses on apparel & design attributes, not personal identity. Images are processed
          in memory and never stored.
        </Text>
      </View>
    </SafeAreaView>
  );
}

function toSelected(a: ImagePicker.ImagePickerAsset): SelectedImage {
  return {
    uri: a.uri,
    mime: a.mimeType || 'image/jpeg',
    name: a.fileName || a.uri.split('/').pop() || 'image.jpg',
  };
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.bg, paddingHorizontal: spacing.xl },
  header: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    paddingTop: spacing.sm,
  },
  headerLink: { ...type.bodySm, color: colors.textMuted },
  hero: { flex: 1, justifyContent: 'center' },
  brand: {
    ...type.display,
    fontSize: 56,
    lineHeight: 60,
    color: colors.text,
    marginTop: spacing.md,
    letterSpacing: -1.2,
  },
  tagline: {
    ...type.body,
    color: colors.textMuted,
    marginTop: spacing.lg,
    maxWidth: 340,
  },
  actions: { paddingBottom: spacing.lg },
  pickerHint: {
    ...type.bodySm,
    fontSize: 11,
    color: colors.textSubtle,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  footer: { paddingBottom: spacing.xl },
  footerText: {
    ...type.bodySm,
    fontSize: 11,
    color: colors.textSubtle,
    textAlign: 'center',
  },
});
