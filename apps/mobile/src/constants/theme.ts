/**
 * MSGI One — Institutional Mobile Design Tokens
 * Institutional Palette: MSGI Navy (#1A365D), MSGI Gold (#D4AF37), Slate neutrals.
 * Mandatory 3-Tier Typography System:
 * 1. Primary Display: Bold Italic Serif (Headings, Platform Identity, Significant Welcome)
 * 2. Secondary Display: Italic Serif (Institutional Taglines, Subtitles, Highlights)
 * 3. Standard Body: Clean Normal Formal Font (Body Text, Forms, Inputs, Buttons, Data)
 */

import { Platform, TextStyle } from 'react-native';

export const Colors = {
  primary: '#1A365D',        // MSGI Deep Navy
  primaryLight: '#2A4365',
  primaryDark: '#0F2942',
  accent: '#D4AF37',         // MSGI Gold
  accentLight: '#E6C65C',
  accentDark: '#B8972E',
  background: '#F8FAFC',
  card: '#FFFFFF',
  text: '#0F172A',
  textSecondary: '#64748B',
  textMuted: '#94A3B8',
  border: '#E2E8F0',
  borderLight: '#F1F5F9',
  success: '#10B981',
  warning: '#F59E0B',
  error: '#EF4444',
  info: '#3B82F6',
  scrimDark: 'rgba(15, 23, 42, 0.78)',
  scrimLight: 'rgba(26, 54, 93, 0.88)',
};

const serifFamily = Platform.select({
  ios: 'Georgia',
  android: 'serif',
  web: 'Playfair Display, Georgia, "Times New Roman", serif',
  default: 'serif',
});

const formalSansFamily = Platform.select({
  ios: 'System',
  android: 'sans-serif',
  web: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  default: 'sans-serif',
});

export const Typography = {
  fontFamily: {
    serif: serifFamily,
    formal: formalSansFamily,
    regular: formalSansFamily,
    medium: formalSansFamily,
    bold: formalSansFamily,
  },
  fontSize: {
    xs: 12,
    sm: 14,
    md: 16,
    lg: 18,
    xl: 20,
    xxl: 24,
    title: 28,
    hero: 32,
  },
  // Mandatory 3-Tier Semantic Typography Tokens
  displayPrimary: {
    fontFamily: serifFamily,
    fontSize: 28,
    fontWeight: '700' as TextStyle['fontWeight'],
    fontStyle: 'italic' as TextStyle['fontStyle'],
    letterSpacing: 1.5,
  },
  displaySecondary: {
    fontFamily: serifFamily,
    fontSize: 14,
    fontWeight: '400' as TextStyle['fontWeight'],
    fontStyle: 'italic' as TextStyle['fontStyle'],
    letterSpacing: 0.8,
  },
  sectionHeading: {
    fontFamily: serifFamily,
    fontSize: 22,
    fontWeight: '700' as TextStyle['fontWeight'],
    fontStyle: 'normal' as TextStyle['fontStyle'],
    letterSpacing: 0.5,
  },
  body: {
    fontFamily: formalSansFamily,
    fontSize: 15,
    fontWeight: '400' as TextStyle['fontWeight'],
    fontStyle: 'normal' as TextStyle['fontStyle'],
    lineHeight: 22,
  },
  formLabel: {
    fontFamily: formalSansFamily,
    fontSize: 14,
    fontWeight: '600' as TextStyle['fontWeight'],
    fontStyle: 'normal' as TextStyle['fontStyle'],
  },
  formInput: {
    fontFamily: formalSansFamily,
    fontSize: 16,
    fontWeight: '400' as TextStyle['fontWeight'],
    fontStyle: 'normal' as TextStyle['fontStyle'],
  },
  button: {
    fontFamily: formalSansFamily,
    fontSize: 16,
    fontWeight: '700' as TextStyle['fontWeight'],
    fontStyle: 'normal' as TextStyle['fontStyle'],
    letterSpacing: 0.5,
  },
  caption: {
    fontFamily: formalSansFamily,
    fontSize: 12,
    fontWeight: '400' as TextStyle['fontWeight'],
    fontStyle: 'normal' as TextStyle['fontStyle'],
  },
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48,
};

export const BorderRadius = {
  xs: 4,
  sm: 6,
  md: 10,
  lg: 16,
  full: 9999,
};
