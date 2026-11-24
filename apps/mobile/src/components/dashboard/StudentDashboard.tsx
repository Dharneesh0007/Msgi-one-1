import React, { useState } from 'react';
import { View, Text, TouchableOpacity, TextInput, ActivityIndicator, StyleSheet } from 'react-native';
import { useRouter } from 'expo-router';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';
import { UserProfileResponse } from '../../types/auth';
import { MentorProfile } from '../../types/business';
import { WelcomeBanner } from './WelcomeBanner';
import { AIActionCard } from './AIActionCard';
import { MentorRecommendationCard } from './MentorRecommendationCard';
import { PendingRequestsSection } from './PendingRequestsSection';
import { UpcomingMeetingsSection } from './UpcomingMeetingsSection';
import { UnreadMessagesSection } from './UnreadMessagesSection';
import { CareerOpportunitiesSection } from './CareerOpportunitiesSection';
import { NotificationsSection } from './NotificationsSection';
import { LearningCommunitiesSection } from './LearningCommunitiesSection';
import { FeedbackBanner, LoadingStateView, ErrorRecoveryBanner } from '../common/StateViews';
import { useDashboardData } from '../../hooks/useDashboardData';

export function StudentDashboard({
  user,
  dashboard,
}: {
  user: UserProfileResponse | null;
  dashboard: ReturnType<typeof useDashboardData>;
}) {
  const router = useRouter();
  const [selectedMentor, setSelectedMentor] = useState<MentorProfile | null>(null);
  const [mentorTopic, setMentorTopic] = useState('AI Career Pathways');
  const [mentorGoal, setMentorGoal] = useState('Prepare for Software & AI Engineer roles');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [mentorModalMsg, setMentorModalMsg] = useState<string | null>(null);

  const handleSubmitMentor = async () => {
    if (!selectedMentor) return;
    setIsSubmitting(true);
    setMentorModalMsg(null);
    try {
      await dashboard.handleSubmitMentorRequest(selectedMentor.id, mentorTopic, mentorGoal);
      setMentorModalMsg('Mentorship request successfully submitted to mentor.');
    } catch (err: any) {
      setMentorModalMsg(err.message || 'Failed to submit mentorship request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View>
      <WelcomeBanner
        user={user}
        primaryRole="student"
        subtitle={user?.student_profile?.department ? `${user.student_profile.department} • Student Portal` : 'Student Portal'}
      />

      {dashboard.loadError ? (
        <ErrorRecoveryBanner message={dashboard.loadError} onRetry={dashboard.loadDashboardData} />
      ) : null}
      {dashboard.actionFeedback ? <FeedbackBanner message={dashboard.actionFeedback} /> : null}

      {/* Quick Navigation */}
      <View style={styles.quickNavRow}>
        <TouchableOpacity style={styles.quickNavCard} onPress={() => router.push('/(tabs)/network')}>
          <Text style={styles.quickNavIcon}>🌐</Text>
          <Text style={styles.quickNavTitle}>Discover Alumni</Text>
          <Text style={styles.quickNavDesc}>Search verified graduates</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.quickNavCard} onPress={() => router.push('/(tabs)/opportunities')}>
          <Text style={styles.quickNavIcon}>💼</Text>
          <Text style={styles.quickNavTitle}>CareerBridge</Text>
          <Text style={styles.quickNavDesc}>Jobs & skill matches</Text>
        </TouchableOpacity>
      </View>

      <AIActionCard subtitle="Ask your AI copilot to recommend alumni mentors, analyze skill gaps, and plan your career." />

      {/* Announcements */}
      {dashboard.announcements.length > 0 ? (
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Institutional Announcements</Text>
          {dashboard.announcements.slice(0, 2).map((ann) => (
            <View key={ann.id} style={styles.annCard}>
              <Text style={styles.annTitle}>{ann.title}</Text>
              <Text style={styles.annBody}>{ann.body}</Text>
            </View>
          ))}
        </View>
      ) : null}

      {/* Recommended Alumni */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Recommended Alumni</Text>
          <TouchableOpacity onPress={() => router.push('/(tabs)/network')}>
            <Text style={styles.sectionLink}>Directory</Text>
          </TouchableOpacity>
        </View>
        {dashboard.alumniMatches.slice(0, 2).map((alum) => (
          <TouchableOpacity
            key={alum.id}
            style={styles.alumniMiniCard}
            onPress={() => router.push('/(tabs)/network')}
          >
            <Text style={styles.alumniMiniName}>{alum.full_name} {alum.is_verified ? '✓' : ''}</Text>
            <Text style={styles.alumniMiniMeta}>{alum.headline} • Class of {alum.graduation_year}</Text>
          </TouchableOpacity>
        ))}
      </View>

      {/* Recommended Mentors */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Recommended Mentors</Text>
          <TouchableOpacity onPress={() => router.push('/(tabs)/network')}>
            <Text style={styles.sectionLink}>View All</Text>
          </TouchableOpacity>
        </View>
        {dashboard.loadingData ? (
          <LoadingStateView message="Loading mentors..." />
        ) : (
          dashboard.mentors.slice(0, 2).map((m) => (
            <MentorRecommendationCard
              key={m.id}
              mentor={m}
              onRequestMentorship={(mentor) => {
                setSelectedMentor(mentor);
                setMentorModalMsg(null);
              }}
            />
          ))
        )}
      </View>

      <UpcomingMeetingsSection meetings={dashboard.meetings} />
      <PendingRequestsSection
        requests={dashboard.mentorRequests}
        mode="student"
        onRespond={dashboard.handleRespondMentorRequest}
      />
      <UnreadMessagesSection threads={dashboard.conversations} />
      <CareerOpportunitiesSection jobs={dashboard.jobs} />

      {/* Events */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Upcoming Institutional Events</Text>
        {dashboard.events.slice(0, 3).map((ev) => (
          <View key={ev.id} style={styles.eventCard}>
            <Text style={styles.eventTitle}>{ev.title}</Text>
            <Text style={styles.eventMeta}>
              📍 {ev.location} • {new Date(ev.start_time).toLocaleDateString()} • {ev.available_seats} seats left
            </Text>
            {ev.is_registered ? (
              <Text style={styles.registeredText}>✓ Registered</Text>
            ) : (
              <TouchableOpacity
                style={styles.registerBtn}
                onPress={() => dashboard.handleRegisterEvent(ev.id)}
                disabled={dashboard.registeringEventId === ev.id || ev.available_seats <= 0}
              >
                <Text style={styles.registerBtnText}>
                  {dashboard.registeringEventId === ev.id ? 'Registering...' : ev.available_seats > 0 ? 'Register Now' : 'Full'}
                </Text>
              </TouchableOpacity>
            )}
          </View>
        ))}
      </View>

      <LearningCommunitiesSection
        courses={dashboard.learningCourses}
        enrollments={dashboard.userEnrollments}
        communities={dashboard.communities}
        updatingEnrollmentId={dashboard.updatingEnrollmentId}
        onEnrollCourse={dashboard.handleEnrollCourse}
        onUpdateProgress={dashboard.handleUpdateProgress}
        onJoinCommunity={dashboard.handleJoinCommunity}
      />

      <NotificationsSection
        notifications={dashboard.notifications}
        unreadCount={dashboard.unreadNotifCount}
        onMarkRead={dashboard.handleMarkNotificationRead}
      />

      {/* Mentorship Request Modal */}
      {selectedMentor ? (
        <View style={styles.modalCard}>
          <Text style={styles.modalTitle}>Request Mentorship: {selectedMentor.full_name}</Text>
          {mentorModalMsg ? <FeedbackBanner message={mentorModalMsg} /> : null}
          <TextInput style={styles.input} value={mentorTopic} onChangeText={setMentorTopic} placeholder="Topic" />
          <TextInput style={styles.input} value={mentorGoal} onChangeText={setMentorGoal} placeholder="Career Goal" />
          <View style={styles.modalActions}>
            <TouchableOpacity style={styles.submitBtn} onPress={handleSubmitMentor} disabled={isSubmitting}>
              {isSubmitting ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.submitBtnText}>Submit</Text>}
            </TouchableOpacity>
            <TouchableOpacity style={styles.closeBtn} onPress={() => setSelectedMentor(null)}>
              <Text style={styles.closeBtnText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
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
  section: { marginBottom: Spacing.lg },
  sectionHeaderRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: Spacing.sm },
  sectionTitle: { fontSize: Typography.fontSize.md, fontWeight: 'bold', color: Colors.text, marginBottom: Spacing.xs },
  sectionLink: { fontSize: Typography.fontSize.xs, color: Colors.primary, fontWeight: 'bold' },
  annCard: { backgroundColor: '#FEFCE8', borderWidth: 1, borderColor: '#FDE047', borderRadius: BorderRadius.md, padding: Spacing.sm, marginBottom: Spacing.xs },
  annTitle: { fontSize: 13, fontWeight: 'bold', color: '#854D0E' },
  annBody: { fontSize: 12, color: '#713F12', marginTop: 2 },
  alumniMiniCard: { backgroundColor: Colors.card, borderRadius: BorderRadius.md, padding: Spacing.sm, marginBottom: Spacing.xs, borderWidth: 1, borderColor: Colors.border },
  alumniMiniName: { fontSize: 13, fontWeight: 'bold', color: Colors.text },
  alumniMiniMeta: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  eventCard: { backgroundColor: Colors.card, borderRadius: BorderRadius.md, padding: Spacing.md, marginBottom: Spacing.xs, borderWidth: 1, borderColor: Colors.border },
  eventTitle: { fontSize: 13, fontWeight: 'bold', color: Colors.text },
  eventMeta: { fontSize: 11, color: Colors.textSecondary, marginTop: 2 },
  registeredText: { fontSize: 11, fontWeight: 'bold', color: Colors.success, marginTop: 6 },
  registerBtn: { alignSelf: 'flex-start', backgroundColor: Colors.primary, paddingHorizontal: Spacing.sm, paddingVertical: 5, borderRadius: BorderRadius.sm, marginTop: 6 },
  registerBtnText: { color: '#FFFFFF', fontSize: 11, fontWeight: 'bold' },
  modalCard: { backgroundColor: Colors.card, borderRadius: BorderRadius.lg, padding: Spacing.md, borderWidth: 1, borderColor: Colors.primary, marginBottom: Spacing.lg },
  modalTitle: { fontSize: Typography.fontSize.md, fontWeight: 'bold', color: Colors.text, marginBottom: Spacing.sm },
  input: { backgroundColor: Colors.background, borderWidth: 1, borderColor: Colors.border, borderRadius: BorderRadius.sm, padding: Spacing.sm, marginBottom: Spacing.sm, color: Colors.text },
  modalActions: { flexDirection: 'row', gap: Spacing.sm },
  submitBtn: { flex: 1, backgroundColor: Colors.primary, paddingVertical: Spacing.sm, borderRadius: BorderRadius.sm, alignItems: 'center' },
  submitBtnText: { color: '#FFFFFF', fontWeight: 'bold' },
  closeBtn: { paddingVertical: Spacing.sm, paddingHorizontal: Spacing.md, borderRadius: BorderRadius.sm, borderWidth: 1, borderColor: Colors.border },
  closeBtnText: { color: Colors.textSecondary, fontWeight: '600' },
});
