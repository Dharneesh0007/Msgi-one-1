/**
 * MSGI One — Mobile Institutional Authentication Screen (Login)
 * Visual Direction: MSEC (Meenakshi Sundararajan Engineering College) Campus Background
 * Typography Hierarchy:
 * - Primary Display: Bold Italic Serif (Brand Title & Welcome)
 * - Secondary Display: Italic Serif (Institutional Tagline)
 * - Standard Body: Clean Normal Formal Font (Form Inputs, Labels, Buttons)
 * WCAG AA Contrast Compliance (> 4.5:1) with Protective Gradient Scrim
 */

import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ImageBackground,
  StatusBar,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

// Local bundled MSEC campus reference asset (AAPT-compliant valid JPEG)
const CAMPUS_BACKGROUND = require('../../../assets/msec_campus_reference.jpg');

export default function LoginScreen() {
  const router = useRouter();
  const { signIn, isLoading, error: authError } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password) {
      setLocalError('Please enter both institutional email and password.');
      return;
    }

    setLocalError(null);
    setIsSubmitting(true);
    try {
      await signIn(email.trim(), password);
      // Navigation is triggered reactively by RootNavigationLayout
    } catch (err: any) {
      setLocalError(err.message || 'Login failed. Please verify your institutional credentials.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleQuickDemo = (roleEmail: string) => {
    setEmail(roleEmail);
    setPassword('');
    setLocalError(null);
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <StatusBar barStyle="light-content" backgroundColor={Colors.primaryDark} />
      <ImageBackground
        source={CAMPUS_BACKGROUND}
        style={styles.backgroundImage}
        resizeMode="cover"
      >
        {/* Dark Scrim Overlay for WCAG AA Contrast */}
        <View style={styles.scrimOverlay}>
          <ScrollView
            contentContainerStyle={styles.scrollContent}
            keyboardShouldPersistTaps="handled"
            showsVerticalScrollIndicator={false}
          >
            {/* Institutional Header & MSEC Identity */}
            <View style={styles.header}>
              <View style={styles.crestContainer}>
                <Text style={styles.crestText}>M</Text>
              </View>
              {/* PRIMARY TYPOGRAPHY: Bold Italic Serif */}
              <Text style={styles.brandTitle}>MSGI ONE</Text>
              {/* SECONDARY TYPOGRAPHY: Italic Serif */}
              <Text style={styles.brandTagline}>Meenakshi Sundararajan Engineering College Ecosystem</Text>
              <Text style={styles.campusSubtext}>Alumni & Institutional Knowledge Platform</Text>
            </View>

            {/* High-Contrast Card Container */}
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Institutional Sign In</Text>
              <Text style={styles.cardSubtitle}>
                Access verified academic, career, and mentorship records
              </Text>

              {(localError || authError) && (
                <View style={styles.errorBanner} accessibilityRole="alert">
                  <Text style={styles.errorText}>{localError || authError}</Text>
                </View>
              )}

              {/* Email Field: Clean Normal Formal Font */}
              <View style={styles.inputGroup}>
                <Text style={styles.inputLabel}>Institutional Email</Text>
                <TextInput
                  style={styles.input}
                  placeholder="name@example.msgi.edu"
                  placeholderTextColor={Colors.textMuted}
                  value={email}
                  onChangeText={setEmail}
                  autoCapitalize="none"
                  keyboardType="email-address"
                  autoComplete="email"
                  accessibilityLabel="Institutional Email Input"
                />
              </View>

              {/* Password Field: Clean Normal Formal Font */}
              <View style={styles.inputGroup}>
                <View style={styles.labelRow}>
                  <Text style={styles.inputLabel}>Password</Text>
                  <TouchableOpacity
                    onPress={() => router.push('/(auth)/forgot-password')}
                    accessibilityRole="link"
                  >
                    <Text style={styles.forgotPasswordLink}>Forgot Password?</Text>
                  </TouchableOpacity>
                </View>
                <TextInput
                  style={styles.input}
                  placeholder="••••••••••••"
                  placeholderTextColor={Colors.textMuted}
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                  autoCapitalize="none"
                  accessibilityLabel="Password Input"
                />
              </View>

              {/* Submit Button: Clean Bold Formal Font */}
              <TouchableOpacity
                style={[styles.primaryButton, (isSubmitting || isLoading) && styles.buttonDisabled]}
                onPress={handleLogin}
                disabled={isSubmitting || isLoading}
                accessibilityRole="button"
                accessibilityLabel="Sign In"
              >
                {isSubmitting || isLoading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.primaryButtonText}>Sign In to Ecosystem</Text>
                )}
              </TouchableOpacity>

              <View style={styles.footerRow}>
                <Text style={styles.footerText}>New to MSGI One?</Text>
                <TouchableOpacity
                  onPress={() => router.push('/(auth)/register')}
                  accessibilityRole="link"
                >
                  <Text style={styles.registerLink}>Create Account</Text>
                </TouchableOpacity>
              </View>
            </View>

            {/* Synthetic Demo Shortcuts (Safely gated for Development and Staging Review) */}
            {(__DEV__ || process.env.EXPO_PUBLIC_ENABLE_DEMO_SHORTCUTS === 'true') && (
              <View style={styles.demoSection}>
                <Text style={styles.demoTitle}>Quick Synthetic Demo Accounts (Staging / Dev)</Text>
                <View style={styles.demoButtonRow}>
                  <TouchableOpacity
                    style={styles.demoButton}
                    onPress={() => handleQuickDemo('alex.rivera@example.msgi.edu')}
                    accessibilityRole="button"
                    accessibilityLabel="Quick Demo Login as Student Alex"
                  >
                    <Text style={styles.demoButtonText}>Student (Alex)</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.demoButton}
                    onPress={() => handleQuickDemo('kenji.sato@example.msgi.edu')}
                    accessibilityRole="button"
                    accessibilityLabel="Quick Demo Login as Alumni Kenji"
                  >
                    <Text style={styles.demoButtonText}>Alumni (Kenji)</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.demoButton}
                    onPress={() => handleQuickDemo('sarah.jenkins@example.msgi.edu')}
                    accessibilityRole="button"
                    accessibilityLabel="Quick Demo Login as Admin Sarah"
                  >
                    <Text style={styles.demoButtonText}>Admin (Sarah)</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </ScrollView>
        </View>
      </ImageBackground>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primaryDark,
  },
  backgroundImage: {
    flex: 1,
    width: '100%',
    height: '100%',
  },
  scrimOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.76)', // Soft dark scrim ensuring > 4.5:1 contrast
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: Spacing.lg,
    paddingVertical: Spacing.xxl,
  },
  header: {
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  crestContainer: {
    width: 64,
    height: 64,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.accent,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: Spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 5,
    elevation: 4,
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  crestText: {
    fontFamily: Typography.displayPrimary.fontFamily,
    fontSize: Typography.fontSize.hero,
    fontWeight: 'bold',
    fontStyle: 'italic',
    color: Colors.primaryDark,
  },
  brandTitle: {
    ...Typography.displayPrimary,
    color: '#FFFFFF',
    textShadowColor: 'rgba(0, 0, 0, 0.65)',
    textShadowOffset: { width: 0, height: 2 },
    textShadowRadius: 4,
  },
  brandTagline: {
    ...Typography.displaySecondary,
    color: Colors.accentLight,
    marginTop: Spacing.xs,
    textAlign: 'center',
    paddingHorizontal: Spacing.md,
    textShadowColor: 'rgba(0, 0, 0, 0.6)',
    textShadowOffset: { width: 0, height: 1 },
    textShadowRadius: 3,
  },
  campusSubtext: {
    fontFamily: Typography.caption.fontFamily,
    fontSize: Typography.fontSize.xs,
    color: '#E2E8F0',
    marginTop: Spacing.xs,
    letterSpacing: 0.8,
    textTransform: 'uppercase',
  },
  card: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 6,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.35)',
  },
  cardTitle: {
    ...Typography.sectionHeading,
    color: Colors.text,
  },
  cardSubtitle: {
    ...Typography.body,
    fontSize: Typography.fontSize.sm,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  errorBanner: {
    backgroundColor: '#FEE2E2',
    borderColor: Colors.error,
    borderWidth: 1,
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    marginBottom: Spacing.md,
  },
  errorText: {
    ...Typography.body,
    color: Colors.error,
    fontSize: Typography.fontSize.sm,
  },
  inputGroup: {
    marginBottom: Spacing.md,
  },
  labelRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  inputLabel: {
    ...Typography.formLabel,
    color: Colors.text,
  },
  forgotPasswordLink: {
    ...Typography.caption,
    color: Colors.primaryLight,
    fontWeight: '600',
  },
  input: {
    ...Typography.formInput,
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.md,
    paddingHorizontal: Spacing.md,
    paddingVertical: Platform.OS === 'ios' ? Spacing.sm : Spacing.xs,
    color: Colors.text,
  },
  primaryButton: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.md,
    alignItems: 'center',
    marginTop: Spacing.sm,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3,
  },
  buttonDisabled: {
    opacity: 0.65,
  },
  primaryButtonText: {
    ...Typography.button,
    color: '#FFFFFF',
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: Spacing.lg,
  },
  footerText: {
    ...Typography.body,
    fontSize: Typography.fontSize.sm,
    color: Colors.textSecondary,
    marginRight: Spacing.xs,
  },
  registerLink: {
    ...Typography.body,
    fontSize: Typography.fontSize.sm,
    color: Colors.accentDark,
    fontWeight: '700',
  },
  demoSection: {
    marginTop: Spacing.lg,
    alignItems: 'center',
  },
  demoTitle: {
    ...Typography.caption,
    color: '#E2E8F0',
    textTransform: 'uppercase',
    letterSpacing: 1,
    marginBottom: Spacing.sm,
  },
  demoButtonRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  demoButton: {
    backgroundColor: 'rgba(15, 23, 42, 0.65)',
    borderRadius: BorderRadius.sm,
    paddingVertical: Spacing.xs,
    paddingHorizontal: Spacing.md,
    borderWidth: 1,
    borderColor: 'rgba(212, 175, 55, 0.45)', // Accent Gold border
  },
  demoButtonText: {
    ...Typography.caption,
    color: '#FFFFFF',
    fontWeight: '600',
  },
});
