// SIGNAL design system.
// Editorial palette per the brief: warm white, charcoal, stone, deep emerald,
// muted burgundy. No SaaS blue, ever.

export const colors = {
  bg: '#FBF8F2',          // warm white
  surface: '#FFFFFF',
  surfaceMuted: '#F4EFE5',
  text: '#1F1F1D',        // charcoal
  textMuted: '#6B6760',   // stone
  textSubtle: '#9A938A',
  divider: '#E6E2D8',
  emerald: '#1F5F4A',     // accent 1
  emeraldSoft: '#E3EDE7',
  burgundy: '#7A2A2A',    // accent 2
  burgundySoft: '#F3E3E3',
  shadow: 'rgba(31, 31, 29, 0.06)',
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
  display: { fontSize: 32, lineHeight: 38, fontWeight: '700' as const, letterSpacing: -0.5 },
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
