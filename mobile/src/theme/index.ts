// SIGNAL design system.
// Editorial palette per the brief: warm white, charcoal, stone, deep emerald,
// muted burgundy. No SaaS blue, ever.

export const colors = {
  bg: '#F7F2E8',          // warmer cream
  surface: '#FFFFFF',
  surfaceMuted: '#EEE7D6',
  text: '#1A1A18',        // deeper charcoal
  textMuted: '#5F5B53',
  textSubtle: '#9A938A',
  divider: '#E0DAC9',
  emerald: '#0F4D3A',     // deep forest green primary
  emeraldDeep: '#0A3A2C',
  emeraldSoft: '#D9E5DE',
  burgundy: '#7A2A2A',
  burgundySoft: '#F3E3E3',
  // Direction-card tints (per references)
  safeTint: '#DDE9E0',    // pale sage
  trendTint: '#F4D9D5',   // dusty rose
  diffTint:  '#F1E3CD',   // warm sand
  shadow: 'rgba(26, 26, 24, 0.08)',
} as const;

export const radii = {
  sm: 8,
  md: 14,
  lg: 22,
  pill: 999,
} as const;

export const spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
  xxxl: 48,
} as const;

export const type = {
  display: { fontSize: 42, lineHeight: 48, fontWeight: '700' as const, letterSpacing: -1.2 },
  h1:      { fontSize: 26, lineHeight: 32, fontWeight: '700' as const, letterSpacing: -0.3 },
  h2:      { fontSize: 20, lineHeight: 26, fontWeight: '600' as const, letterSpacing: -0.2 },
  h3:      { fontSize: 16, lineHeight: 22, fontWeight: '600' as const },
  body:    { fontSize: 15, lineHeight: 22, fontWeight: '400' as const },
  bodySm:  { fontSize: 13, lineHeight: 19, fontWeight: '400' as const },
  caption: { fontSize: 11, lineHeight: 14, fontWeight: '500' as const, letterSpacing: 0.6 },
  mono:    { fontSize: 12, lineHeight: 16, fontWeight: '500' as const },
} as const;

export const shadow = {
  card: {
    shadowColor: colors.text,
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.06,
    shadowRadius: 16,
    elevation: 2,
  },
} as const;
