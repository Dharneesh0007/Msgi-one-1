import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { UserProfileResponse, UserRole } from '../../types/auth';

export function WelcomeBanner({
  user,
  primaryRole,
  subtitle,
}: {
  user: UserProfileResponse | null;
  primaryRole: UserRole | 'guest';
  subtitle?: string;
}) {
  const displayName = user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : 'Institutional Member';

  return (
    <View style={styles.welcomeCard}>
      <View style={styles.avatarCrest}>
        <Text style={styles.avatarText}>
          {user?.first_name ? user.first_name[0].toUpperCase() : 'M'}
        </Text>
      </View>
      <View style={styles.welcomeInfo}>
        <Text style={styles.greetingText}>Welcome back,</Text>
        <Text style={styles.userNameText}>{displayName}</Text>
        {subtitle ? <Text style={styles.subtitleText}>{subtitle}</Text> : null}
        <View style={styles.roleBadgeRow}>
          <View style={styles.roleBadge}>
            <Text style={styles.roleBadgeText}>{primaryRole.toUpperCase()}</Text>
          </View>
          {user?.is_verified ? (
            <View style={styles.verifiedBadge}>
              <Text style={styles.verifiedBadgeText}>✓ VERIFIED</Text>
            </View>
          ) : (
            <View style={styles.pendingBadge}>
              <Text style={styles.pendingBadgeText}>PENDING VERIFICATION</Text>
            </View>
          )}
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  welcomeCard: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.lg,
  },
  avatarCrest: {
    width: 60,
    height: 60,
    borderRadius: BorderRadius.full,
    backgroundColor: Colors.accent,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.md,
  },
  avatarText: {
    fontSize: Typography.fontSize.xl,
    fontWeight: 'bold',
    color: Colors.primaryDark,
  },
  welcomeInfo: { flex: 1 },
  greetingText: {
    fontSize: 10,
    color: '#CBD5E1',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  userNameText: {
    fontSize: Typography.fontSize.lg,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 2,
  },
  subtitleText: {
    fontSize: 12,
    color: '#E2E8F0',
    marginTop: 2,
  },
  roleBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.xs,
    gap: Spacing.xs,
    flexWrap: 'wrap',
  },
  roleBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  verifiedBadge: {
    backgroundColor: Colors.success,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  verifiedBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  pendingBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.3)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  pendingBadgeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#FEF3C7',
  },
});
