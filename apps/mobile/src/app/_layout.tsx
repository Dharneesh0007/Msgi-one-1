/**
 * MSGI One — Mobile Root Layout & Protected Route Guard
 * Enforces authentication state machine and redirects according to role & onboarding status.
 */

import React, { useEffect } from 'react';
import { Stack, useRouter, useSegments } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet, Text } from 'react-native';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { Colors, Typography, Spacing } from '../constants/theme';

function RootNavigationLayout() {
  const { session, user, isLoading, isProfileComplete } = useAuth();
  const segments = useSegments();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;

    const inAuthGroup = segments[0] === '(auth)';
    const currentScreen = segments[1];

    if (!session) {
      // User is unauthenticated — redirect to login if not already in auth stack
      if (!inAuthGroup) {
        router.replace('/(auth)/login');
      }
    } else {
      // User is authenticated
      if (!isProfileComplete) {
        // Must complete first/last name onboarding
        if (currentScreen !== 'complete-profile') {
          router.replace('/(auth)/complete-profile');
        }
      } else if (inAuthGroup && currentScreen !== 'verification-pending') {
        // Authenticated and complete profile — route to main dashboard tabs
        router.replace('/(tabs)');
      }
    }
  }, [session, user, isLoading, isProfileComplete, segments]);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <View style={styles.brandBadge}>
          <Text style={styles.brandTitle}>MSGI ONE</Text>
          <Text style={styles.brandSubtitle}>Institutional Alumni Ecosystem</Text>
        </View>
        <ActivityIndicator size="large" color={Colors.accent} style={styles.spinner} />
        <StatusBar style="light" />
      </View>
    );
  }

  return (
    <>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigationLayout />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: Colors.primary,
    justifyContent: 'center',
    alignItems: 'center',
    padding: Spacing.xl,
  },
  brandBadge: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
  },
  brandTitle: {
    fontSize: Typography.fontSize.title,
    fontWeight: 'bold',
    color: '#FFFFFF',
    letterSpacing: 2,
  },
  brandSubtitle: {
    fontSize: Typography.fontSize.sm,
    color: Colors.accent,
    marginTop: Spacing.xs,
    letterSpacing: 1,
  },
  spinner: {
    marginTop: Spacing.md,
  },
});
