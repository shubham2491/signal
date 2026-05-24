import React from 'react';
import { Image, StyleSheet, Text, View } from 'react-native';
import { colors, radii, type } from '@/theme';

/**
 * Compact 1..N image collage used in upload previews and history rows.
 * Lays out up to 4 thumbs with a "+N" overflow tile when there's more.
 */
export function ImageCollage({
  uris,
  size = 96,
  radius = radii.md,
}: {
  uris: string[];
  size?: number;
  radius?: number;
}) {
  const visible = uris.slice(0, 4);
  const overflow = uris.length - visible.length;

  if (uris.length === 0) {
    return <View style={[styles.placeholder, { width: size, height: size, borderRadius: radius }]} />;
  }
  if (uris.length === 1) {
    return (
      <Image
        source={{ uri: uris[0] }}
        style={{ width: size, height: size, borderRadius: radius, backgroundColor: colors.surfaceMuted }}
      />
    );
  }

  return (
    <View style={[styles.grid, { width: size, height: size, borderRadius: radius }]}>
      {visible.map((u, i) => (
        <View
          key={`${u}-${i}`}
          style={[
            styles.tile,
            visible.length === 2 && { width: '100%', height: '50%' },
            visible.length === 3 && (i === 0 ? { width: '100%', height: '50%' } : { width: '50%', height: '50%' }),
            visible.length >= 4 && { width: '50%', height: '50%' },
          ]}
        >
          <Image source={{ uri: u }} style={styles.tileImg} />
          {i === visible.length - 1 && overflow > 0 ? (
            <View style={styles.overflow}>
              <Text style={styles.overflowText}>+{overflow}</Text>
            </View>
          ) : null}
        </View>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    overflow: 'hidden',
    backgroundColor: colors.surfaceMuted,
    flexDirection: 'row',
    flexWrap: 'wrap',
  },
  tile: {
    padding: 1,
    position: 'relative',
  },
  tileImg: { width: '100%', height: '100%', backgroundColor: colors.surfaceMuted },
  overflow: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(31,31,29,0.55)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  overflowText: { ...type.h2, color: '#fff' },
  placeholder: { backgroundColor: colors.surfaceMuted },
});
