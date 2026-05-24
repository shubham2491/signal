import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Image, Platform, StyleSheet, Text, View } from 'react-native';
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
import { loadHistory } from '@/storage/history';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Tabs'>;

export function HomeScreen() {
  const nav = useNavigation<Nav>();
  const [busy, setBusy] = useState<'camera' | 'library' | null>(null);
  const [heroUri, setHeroUri] = useState<string | null>(null);

  // Rotate hero from a recent thumbnail in history. No history = no hero
  // (UI degrades to a tidy colored block, see styles.heroPlaceholder).
  useEffect(() => {
    loadHistory().then((entries) => {
      const flat = entries.flatMap((e) => e.thumbnails).filter(Boolean);
      if (flat.length) {
        setHeroUri(flat[Math.floor(Math.random() * Math.min(flat.length, 8))]);
      }
    }).catch(() => {});
  }, []);

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

      <View style={styles.hero}>
        {heroUri ? (
          <Image source={{ uri: heroUri }} style={styles.heroImage} resizeMode="cover" />
        ) : (
          <View style={styles.heroPlaceholder}>
            <Text style={styles.heroPlaceholderText}>SIGNAL</Text>
          </View>
        )}
        <View style={styles.heroOverlay} />
      </View>

      <View style={styles.copy}>
        <Kicker>Fashion Intelligence</Kicker>
        <Text style={styles.brand}>SIGNAL</Text>
        <Text style={styles.tagline}>
          From a single photo to a designer brief — anchored to Indian retail.
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
        <Text style={styles.subline}>
          Single image · multi-image · auto-grouped by category
          {Platform.OS === 'web' ? '  ·  hold ⌘/Ctrl in the dialog to pick many' : ''}
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
  container: { flex: 1, backgroundColor: colors.bg },

  hero: {
    height: 320,
    backgroundColor: colors.surfaceMuted,
    borderBottomLeftRadius: radii.lg,
    borderBottomRightRadius: radii.lg,
    overflow: 'hidden',
  },
  heroImage: { width: '100%', height: '100%' },
  heroOverlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(15, 77, 58, 0.05)',
  },
  heroPlaceholder: {
    flex: 1, alignItems: 'center', justifyContent: 'center',
    backgroundColor: colors.surfaceMuted,
  },
  heroPlaceholderText: {
    ...type.display,
    fontSize: 64,
    color: colors.divider,
    letterSpacing: -2,
  },

  copy: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xl,
  },
  brand: {
    ...type.display,
    color: colors.text,
    marginTop: spacing.xs,
  },
  tagline: {
    ...type.body,
    color: colors.textMuted,
    marginTop: spacing.sm,
    maxWidth: 320,
  },

  actions: {
    paddingHorizontal: spacing.xl,
    paddingTop: spacing.xl,
    paddingBottom: spacing.xl,
    marginTop: 'auto',
  },
  subline: {
    ...type.bodySm,
    fontSize: 11,
    color: colors.textSubtle,
    textAlign: 'center',
    marginTop: spacing.md,
  },
});
