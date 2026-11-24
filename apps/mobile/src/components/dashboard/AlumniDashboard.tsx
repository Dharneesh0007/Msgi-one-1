import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { UserProfileResponse } from '../../types/auth';
import { WelcomeBanner } from './WelcomeBanner';
import { AIActionCard } from './AIActionCard';
import { PendingRequestsSection } from './PendingRequestsSection';
import { UpcomingMeetingsSection } from './UpcomingMeetingsSection';
import { UnreadMessagesSection } from './UnreadMessagesSection';
import { CareerOpportunitiesSection } from './CareerOpportunitiesSection';
import { NotificationsSection } from './NotificationsSection';
import { FeedbackBanner, ErrorRecoveryBanner } from '../common/StateViews';
import { useDashboardData } from '../../hooks/useDashboardData';

export function AlumniDashboard({
  user,
  dashboard,
}: {
  user: UserProfileResponse | null;
  dashboard: ReturnType<typeof useDashboardData>;
}) {
  const router = useRouter();

  const acceptedCount = dashboard.mentorRequests.filter((r) => r.status === 'accepted').length;
  const pendingCount = dashboard.mentorRequests.filter((r) => r.status === 'pending').length;

  return (
    <View>
      <WelcomeBanner
        user={user}
        primaryRole="alumni"
        subtitle={
          user?.alumni_profile?.current_company
            ? `${user.alumni_profile.current_title || 'Alumnus'} @ ${user.alumni_profile.current_company}`
            : 'Alumni Portal'
        }
      />

      {dashboard.loadError ? (
        <ErrorRecoveryBanner message={dashboard.loadError} onRetry={dashboard.loadDashboardData} />
      ) : null}
      {dashboard.actionFeedback ? <FeedbackBanner message={dashboard.actionFeedback} /> : null}

      {/* Mentorship Activity KPI Row */}
      <View style={styles.kpiRow}>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiValue}>{pendingCount}</Text>
          <Text style={styles.kpiLabel}>New Requests</Text>
        </View>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiValue}>{acceptedCount}</Text>
          <Text style={styles.kpiLabel}>Active Mentees</Text>
        </View>
        <View style={styles.kpiCard}>
          <Text style={styles.kpiValue}>{dashboard.unreadNotifCount}</Text>
          <Text style={styles.kpiLabel}>Unread Alerts</Text>
        </View>
      </View>

      {/* Availability & Profile Management Quick Access */}
      <View style={styles.quickNavRow}>
        <TouchableOpacity style={styles.quickNavCard} onPress={() => router.push('/(tabs)/profile')}>
          <Text style={styles.quickNavIcon}>🗓️</Text>
          <Text style={styles.quickNavTitle}>Availability & Bio</Text>
          <Text style={styles.quickNavDesc}>Update mentorship & career profile</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickNavCard} onPress={() => router.push('/(tabs)/opportunities')}>
          <Text style={styles.quickNavIcon}>📢</Text>
          <Text style={styles.quickNavTitle}>Job Postings</Text>
          <Text style={styles.quickNavDesc}>Refer students to open roles</Text>
        </TouchableOpacity>
      </View>

      <AIActionCard
        title="Alumni AI Assistant"
        subtitle="Draft thoughtful student replies, review mentorship fit, and prepare meeting agendas."
      />

      {/* Student Request Centre */}
      <PendingRequestsSection
        requests={dashboard.mentorRequests}
        mode="alumni"
        onRespond={dashboard.handleRespondMentorRequest}
      />

      <UpcomingMeetingsSection title="Upcoming Student Consultations" meetings={dashboard.meetings} />
      <UnreadMessagesSection threads={dashboard.conversations} />
      <CareerOpportunitiesSection jobs={dashboard.jobs} />
      <NotificationsSection
        notifications={dashboard.notifications}
        unreadCount={dashboard.unreadNotifCount}
        onMarkRead={dashboard.handleMarkNotificationRead}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  kpiRow: { flexDirection: 'row', gap: Spacing.sm, marginBottom: Spacing.md },
  kpiCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: Colors.border,
  },
  kpiValue: { fontSize: Typography.fontSize.xl, fontWeight: 'bold', color: Colors.primary },
  kpiLabel: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  quickNavRow: { flexDirection: 'row', gap: Spacing.md, marginBottom: Spacing.md },
  quickNavCard: {
    flex: 1,
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  quickNavIcon: { fontSize: 22, marginBottom: Spacing.xs },
  quickNavTitle: { fontSize: Typography.fontSize.sm, fontWeight: 'bold', color: Colors.text },
  quickNavDesc: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
});
