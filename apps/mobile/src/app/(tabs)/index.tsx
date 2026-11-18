/**
 * MSGI One — Role-Aware Home Dashboard Screen
 * Adapts dynamically to the user's verified role (Student, Alumni, Faculty, Recruiter, Admin).
 */

import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export default function DashboardScreen() {
  const router = useRouter();
  const { user, primaryRole, refreshProfile, isLoading } = useAuth();
  const [refreshing, setRefreshing] = React.useState(false);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshProfile();
    setRefreshing(false);
  };

  const displayName = user?.first_name ? `${user.first_name} ${user.last_name || ''}` : 'Institutional Member';

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.scrollContent}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[Colors.primary]} />}
    >
      {/* Welcome Banner */}
      <View style={styles.welcomeCard}>
        <View style={styles.avatarCrest}>
          <Text style={styles.avatarText}>
            {user?.first_name ? user.first_name[0].toUpperCase() : 'M'}
          </Text>
        </View>
        <View style={styles.welcomeInfo}>
          <Text style={styles.greetingText}>Welcome back,</Text>
          <Text style={styles.userNameText}>{displayName}</Text>
          <View style={styles.roleBadgeRow}>
            <View style={styles.roleBadge}>
              <Text style={styles.roleBadgeText}>{primaryRole.toUpperCase()}</Text>
            </View>
            {user?.is_verified && (
              <View style={styles.verifiedBadge}>
                <Text style={styles.verifiedBadgeText}>✓ VERIFIED</Text>
              </View>
            )}
          </View>
        </View>
      </View>

      {/* Role-Specific Metric Cards */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Institutional Ecosystem Overview</Text>
        <View style={styles.statsGrid}>
          {primaryRole === 'student' && (
            <>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>1,420+</Text>
                <Text style={styles.statLabel}>Active Alumni Mentors</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>84</Text>
                <Text style={styles.statLabel}>Internship Openings</Text>
              </View>
            </>
          )}

          {primaryRole === 'alumni' && (
            <>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>3</Text>
                <Text style={styles.statLabel}>Mentorship Inquiries</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>12,500+</Text>
                <Text style={styles.statLabel}>Global Alumni</Text>
              </View>
            </>
          )}

          {primaryRole === 'recruiter' && (
            <>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>3,800+</Text>
                <Text style={styles.statLabel}>Graduating Candidates</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>12</Text>
                <Text style={styles.statLabel}>Active Listings</Text>
              </View>
            </>
          )}

          {(primaryRole === 'admin' || primaryRole === 'faculty') && (
            <>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>14</Text>
                <Text style={styles.statLabel}>Pending Verifications</Text>
              </View>
              <View style={styles.statCard}>
                <Text style={styles.statValue}>98.4%</Text>
                <Text style={styles.statLabel}>Ecosystem Health</Text>
              </View>
            </>
          )}
        </View>
      </View>

      {/* Quick Action Hubs */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Quick Hub Navigation</Text>
        <View style={styles.quickNavRow}>
          <TouchableOpacity
            style={styles.quickNavCard}
            onPress={() => router.push('/(tabs)/network')}
          >
            <Text style={styles.quickNavIcon}>🌐</Text>
            <Text style={styles.quickNavTitle}>Alumni Directory</Text>
            <Text style={styles.quickNavDesc}>Explore global alumni by city & skills</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickNavCard}
            onPress={() => router.push('/(tabs)/opportunities')}
          >
            <Text style={styles.quickNavIcon}>💼</Text>
            <Text style={styles.quickNavTitle}>CareerBridge</Text>
            <Text style={styles.quickNavDesc}>Exclusive jobs & alumni referrals</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.aiBannerCard}
          onPress={() => router.push('/(tabs)/ai')}
        >
          <View style={styles.aiBadge}>
            <Text style={styles.aiBadgeText}>AGENTIC AI</Text>
          </View>
          <Text style={styles.aiBannerTitle}>MSGI AI Command Centre</Text>
          <Text style={styles.aiBannerSubtitle}>
            Autonomous alumni matchmaker, career strategist, and institutional advisor.
          </Text>
        </TouchableOpacity>
      </View>

      {/* Institutional Announcements */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Institutional Announcements</Text>
        <View style={styles.announcementCard}>
          <View style={styles.announcementHeader}>
            <Text style={styles.announcementTag}>UPCOMING EVENT</Text>
            <Text style={styles.announcementDate}>Dec 12, 2026</Text>
          </View>
          <Text style={styles.announcementTitle}>MSGI Annual Global Alumni Summit & Tech Gala</Text>
          <Text style={styles.announcementDesc}>
            Connect with distinguished alumni founders, faculty leaders, and global industry heads.
          </Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollContent: {
    padding: Spacing.md,
    paddingBottom: Spacing.xxl,
  },
  welcomeCard: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: Spacing.lg,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
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
  welcomeInfo: {
    flex: 1,
  },
  greetingText: {
    fontSize: Typography.fontSize.xs,
    color: '#CBD5E1',
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  userNameText: {
    fontSize: Typography.fontSize.xl,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 2,
  },
  roleBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: Spacing.xs,
    gap: Spacing.xs,
  },
  roleBadge: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  roleBadgeText: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: '#FFFFFF',
    letterSpacing: 0.5,
  },
  verifiedBadge: {
    backgroundColor: Colors.success,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  verifiedBadgeText: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  section: {
    marginBottom: Spacing.lg,
  },
  sectionTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  statCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  statValue: {
    fontSize: Typography.fontSize.xxl,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  statLabel: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: 4,
    textAlign: 'center',
  },
  quickNavRow: {
    flexDirection: 'row',
    gap: Spacing.md,
    marginBottom: Spacing.md,
  },
  quickNavCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  quickNavIcon: {
    fontSize: 24,
    marginBottom: Spacing.xs,
  },
  quickNavTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
  },
  quickNavDesc: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  aiBannerCard: {
    backgroundColor: '#0F172A',
    borderRadius: BorderRadius.lg,
    padding: Spacing.lg,
    borderWidth: 1,
    borderColor: '#334155',
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
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.primaryDark,
  },
  aiBannerTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  aiBannerSubtitle: {
    fontSize: Typography.fontSize.xs,
    color: '#94A3B8',
    marginTop: 4,
    lineHeight: 18,
  },
  announcementCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  announcementHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  announcementTag: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.accentDark,
  },
  announcementDate: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textMuted,
  },
  announcementTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
  },
  announcementDesc: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    marginTop: 4,
    lineHeight: 18,
  },
});
