import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export function AIActionCard({
  title = 'MSGI AI Command Centre',
  subtitle = 'Autonomous alumni matchmaker, career strategist, and institutional advisor.',
}: {
  title?: string;
  subtitle?: string;
}) {
  const router = useRouter();

  return (
    <TouchableOpacity
      style={styles.aiBannerCard}
      onPress={() => router.push('/(tabs)/ai')}
      accessibilityRole="button"
      accessibilityLabel={title}
    >
      <View style={styles.aiBadge}>
        <Text style={styles.aiBadgeText}>AGENTIC AI COPILOT</Text>
      </View>
      <Text style={styles.aiBannerTitle}>{title}</Text>
      <Text style={styles.aiBannerSubtitle}>{subtitle}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  aiBannerCard: {
    backgroundColor: '#0F172A',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: '#334155',
    marginBottom: Spacing.lg,
  },
  aiBadge: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.accent,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
    marginBottom: Spacing.xs,
  },
  aiBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primaryDark,
  },
  aiBannerTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  aiBannerSubtitle: {
    fontSize: 12,
    color: '#94A3B8',
    marginTop: 4,
  },
});
