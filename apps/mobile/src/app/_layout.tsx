/**
 * MSGI One — Mobile Root Layout & Protected Route Guard
 * Enforces authentication state machine and redirects according to role & onboarding status.
 */

import React, { useEffect, useState } from 'react';
import { Stack, useRouter, useSegments, Href } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet, Text, TouchableOpacity } from 'react-native';
import { QueryClientProvider } from '@tanstack/react-query';
import * as Notifications from 'expo-notifications';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { queryClient } from '../lib/queryClient';
import { isBiometricLockEnabled, promptBiometricUnlock } from '../lib/biometrics';
import { registerDeviceForPushNotifications, resolveNotificationTargetRoute } from '../lib/notifications';
import { Colors, Typography, Spacing } from '../constants/theme';

function RootNavigationLayout() {
  const { session, user, isLoading, isProfileComplete } = useAuth();
  const segments = useSegments();
  const router = useRouter();
  const [biometricLocked, setBiometricLocked] = useState(false);

  useEffect(() => {
    let active = true;
    if (!session) {
      setBiometricLocked(false);
      return;
    }
    isBiometricLockEnabled().then(async (enabled) => {
      if (!active || !enabled) return;
      setBiometricLocked(true);
      const ok = await promptBiometricUnlock('Unlock MSGI One');
      if (active && ok) setBiometricLocked(false);
    });
    registerDeviceForPushNotifications().catch(() => null);
    return () => {
      active = false;
    };
  }, [session?.access_token]);

  useEffect(() => {
    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      const target = resolveNotificationTargetRoute(response.notification.request.content.data as Record<string, any>);
      if (target) {
        router.push(target as Href);
      }
    });
    return () => sub.remove();
  }, [router]);

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

  if (biometricLocked && session) {
    return (
      <View style={styles.loadingContainer}>
        <View style={styles.brandBadge}>
          <Text style={styles.brandTitle}>MSGI ONE LOCKED</Text>
          <Text style={styles.brandSubtitle}>Biometric Verification Required</Text>
        </View>
        <TouchableOpacity
          style={{ backgroundColor: Colors.accent, paddingHorizontal: 20, paddingVertical: 12, borderRadius: 10 }}
          onPress={async () => {
            const ok = await promptBiometricUnlock('Unlock MSGI One');
            if (ok) setBiometricLocked(false);
          }}
        >
          <Text style={{ color: Colors.primaryDark, fontWeight: '700' }}>Unlock with Biometrics</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <>
      <StatusBar style="auto" />
      <Stack screenOptions={{ headerShown: false }}>
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="meetings" options={{ headerShown: false }} />
        <Stack.Screen name="messages" options={{ headerShown: false }} />
        <Stack.Screen name="admin-ai" options={{ headerShown: false }} />
        <Stack.Screen name="room/[meetingId]" options={{ headerShown: false }} />
      </Stack>
    </>
  );
}

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RootNavigationLayout />
      </AuthProvider>
    </QueryClientProvider>
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
