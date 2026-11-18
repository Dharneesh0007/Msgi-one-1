/**
 * MSGI One — Role-Aware Home Dashboard Screen
 * Connected to live Phase 2 APIs: Events, MentorMatch, Global Connect, and Identity.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  TextInput,
  Alert,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../lib/api';
import {
  MentorProfile,
  EventItem,
  RegionalLocation,
  LearningResourceItem,
  CourseEnrollmentItem,
  CommunityItem,
  NotificationRecord,
  VerificationRequestItem,
} from '../../types/business';
import { Colors, Typography, Spacing, BorderRadius } from '../../constants/theme';

export default function DashboardScreen() {
  const router = useRouter();
  const { user, primaryRole, refreshProfile } = useAuth();

  const [refreshing, setRefreshing] = useState(false);
  const [mentors, setMentors] = useState<MentorProfile[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [locations, setLocations] = useState<RegionalLocation[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  // Mentorship request modal state
  const [selectedMentor, setSelectedMentor] = useState<MentorProfile | null>(null);
  const [mentorTopic, setMentorTopic] = useState('AI Career Pathways');
  const [mentorGoal, setMentorGoal] = useState('Prepare for Machine Learning Engineer roles');
  const [isSubmittingMentorReq, setIsSubmittingMentorReq] = useState(false);
  const [mentorActionFeedback, setMentorActionFeedback] = useState<string | null>(null);

  // Event registration feedback
  const [registeringEventId, setRegisteringEventId] = useState<string | null>(null);
  const [eventFeedback, setEventFeedback] = useState<string | null>(null);

  // Phase 4 Services Hub state
  const [activeServicesTab, setActiveServicesTab] = useState<'learning' | 'communities' | 'notifications' | 'admin'>('learning');
  const [learningCourses, setLearningCourses] = useState<LearningResourceItem[]>([]);
  const [userEnrollments, setUserEnrollments] = useState<CourseEnrollmentItem[]>([]);
  const [communities, setCommunities] = useState<CommunityItem[]>([]);
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [unreadNotifCount, setUnreadNotifCount] = useState<number>(0);
  const [pendingVerifications, setPendingVerifications] = useState<VerificationRequestItem[]>([]);
  const [serviceActionFeedback, setServiceActionFeedback] = useState<string | null>(null);
  const [updatingEnrollmentId, setUpdatingEnrollmentId] = useState<string | null>(null);

  const loadDashboardData = useCallback(async () => {
    try {
      setLoadingData(true);
      const [mentorRes, eventRes, locRes, learnRes, myLearnRes, commRes, notifRes, unreadRes] = await Promise.allSettled([
        api.listMentors({ student_goal: 'AI Engineer' }),
        api.listEvents(),
        api.getGlobalLocations(),
        api.listLearningResources(),
        api.getMyLearning(),
        api.listCommunities(),
        api.getMyNotifications(),
        api.getUnreadNotificationCount(),
      ]);

      if (mentorRes.status === 'fulfilled') setMentors(mentorRes.value || []);
      if (eventRes.status === 'fulfilled') setEvents(eventRes.value || []);
      if (locRes.status === 'fulfilled') setLocations(locRes.value || []);
      if (learnRes.status === 'fulfilled') setLearningCourses(learnRes.value || []);
      if (myLearnRes.status === 'fulfilled') setUserEnrollments(myLearnRes.value || []);
      if (commRes.status === 'fulfilled') setCommunities(commRes.value || []);
      if (notifRes.status === 'fulfilled') setNotifications(notifRes.value || []);
      if (unreadRes.status === 'fulfilled') setUnreadNotifCount(unreadRes.value || 0);

      if (primaryRole === 'admin' || user?.roles?.includes('admin') || user?.roles?.includes('institutional_admin')) {
        try {
          const vReqs = await api.listPendingVerifications();
          setPendingVerifications(vReqs || []);
        } catch {
          // ignore non-admin role errors
        }
      }
    } catch (err: any) {
      console.warn('[Dashboard] Data load error:', err.message);
    } finally {
      setLoadingData(false);
      setRefreshing(false);
    }
  }, [primaryRole, user?.roles]);

  useEffect(() => {
    loadDashboardData();
  }, [loadDashboardData]);

  const onRefresh = async () => {
    setRefreshing(true);
    await refreshProfile();
    await loadDashboardData();
  };

  const handleRegisterEvent = async (eventId: string) => {
    setRegisteringEventId(eventId);
    setEventFeedback(null);
    try {
      await api.registerForEvent(eventId);
      setEventFeedback('Registration confirmed! Ticket code generated.');
      loadDashboardData();
    } catch (err: any) {
      setEventFeedback(err.message || 'Registration failed.');
    } finally {
      setRegisteringEventId(null);
    }
  };

  const handleRequestMentorship = async () => {
    if (!selectedMentor) return;
    setIsSubmittingMentorReq(true);
    setMentorActionFeedback(null);
    try {
      await api.submitMentorRequest({
        mentor_id: selectedMentor.id,
        topic: mentorTopic,
        career_goal: mentorGoal,
      });
      setMentorActionFeedback('Mentorship request successfully submitted to mentor.');
      loadDashboardData();
    } catch (err: any) {
      setMentorActionFeedback(err.message || 'Failed to submit request.');
    } finally {
      setIsSubmittingMentorReq(false);
    }
  };

  const handleEnrollCourse = async (resourceId: string) => {
    setServiceActionFeedback(null);
    try {
      await api.enrollInCourse(resourceId);
      setServiceActionFeedback('Successfully enrolled in course!');
      loadDashboardData();
    } catch (err: any) {
      setServiceActionFeedback(err.message || 'Enrollment failed.');
    }
  };

  const handleUpdateProgress = async (enrollmentId: string, currentProgress: number) => {
    setUpdatingEnrollmentId(enrollmentId);
    setServiceActionFeedback(null);
    try {
      const nextProgress = Math.min(100, currentProgress + 25);
      await api.updateLearningProgress(enrollmentId, nextProgress);
      setServiceActionFeedback(nextProgress === 100 ? 'Milestone achieved! Course completed.' : `Progress updated to ${nextProgress}%`);
      loadDashboardData();
    } catch (err: any) {
      setServiceActionFeedback(err.message || 'Progress update failed.');
    } finally {
      setUpdatingEnrollmentId(null);
    }
  };

  const handleJoinCommunity = async (communityId: string) => {
    setServiceActionFeedback(null);
    try {
      const res = await api.joinCommunity(communityId);
      setServiceActionFeedback(res.status === 'active' ? 'Successfully joined community!' : 'Membership request submitted for moderator review.');
      loadDashboardData();
    } catch (err: any) {
      setServiceActionFeedback(err.message || 'Failed to join community.');
    }
  };

  const handleMarkNotificationRead = async (notifId: string) => {
    try {
      await api.markNotificationAsRead(notifId);
      loadDashboardData();
    } catch (err: any) {
      console.warn('Failed to mark read', err);
    }
  };

  const handleDecideVerification = async (requestId: string, decision: 'approved' | 'rejected') => {
    setServiceActionFeedback(null);
    try {
      await api.decideVerification(requestId, decision);
      setServiceActionFeedback(`Verification request ${decision}.`);
      loadDashboardData();
    } catch (err: any) {
      setServiceActionFeedback(err.message || 'Failed to update verification request.');
    }
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

      {/* Quick Hub Navigation */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Ecosystem Navigation Hubs</Text>
        <View style={styles.quickNavRow}>
          <TouchableOpacity
            style={styles.quickNavCard}
            onPress={() => router.push('/(tabs)/network')}
          >
            <Text style={styles.quickNavIcon}>🌐</Text>
            <Text style={styles.quickNavTitle}>Alumni Network</Text>
            <Text style={styles.quickNavDesc}>Live search verified alumni</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.quickNavCard}
            onPress={() => router.push('/(tabs)/opportunities')}
          >
            <Text style={styles.quickNavIcon}>💼</Text>
            <Text style={styles.quickNavTitle}>CareerBridge</Text>
            <Text style={styles.quickNavDesc}>Jobs & skill matches</Text>
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

      {/* Module 3: MentorMatch Section */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>MentorMatch — Available Mentors</Text>
          <TouchableOpacity onPress={() => router.push('/(tabs)/network')}>
            <Text style={styles.sectionLink}>View All</Text>
          </TouchableOpacity>
        </View>

        {loadingData ? (
          <ActivityIndicator color={Colors.primary} />
        ) : mentors.length === 0 ? (
          <Text style={styles.emptyText}>No mentors currently accepting requests.</Text>
        ) : (
          mentors.slice(0, 2).map((mentor) => (
            <View key={mentor.id} style={styles.mentorCard}>
              <View style={styles.mentorHeader}>
                <View style={styles.avatarSmall}>
                  <Text style={styles.avatarSmallText}>{mentor.full_name[0]}</Text>
                </View>
                <View style={styles.mentorMeta}>
                  <Text style={styles.mentorName}>{mentor.full_name}</Text>
                  <Text style={styles.mentorHeadline}>{mentor.headline}</Text>
                  <Text style={styles.mentorLocation}>📍 {mentor.country}</Text>
                </View>
                {mentor.match_score && (
                  <View style={styles.scoreBadge}>
                    <Text style={styles.scoreText}>{mentor.match_score}% Match</Text>
                  </View>
                )}
              </View>

              <View style={styles.topicsRow}>
                {mentor.advisory_topics.map((t) => (
                  <View key={t} style={styles.topicBadge}>
                    <Text style={styles.topicText}>{t}</Text>
                  </View>
                ))}
              </View>

              <View style={styles.mentorFooter}>
                <Text style={styles.slotsText}>
                  {mentor.available_slots} of {mentor.max_active_mentees} slots open
                </Text>
                <TouchableOpacity
                  style={styles.requestButton}
                  onPress={() => {
                    setSelectedMentor(mentor);
                    setMentorActionFeedback(null);
                  }}
                >
                  <Text style={styles.requestButtonText}>Request Mentorship</Text>
                </TouchableOpacity>
              </View>
            </View>
          ))
        )}
      </View>

      {/* Module 4: Upcoming Events & Webinars */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Upcoming Events & Reunions</Text>
        {eventFeedback && (
          <View style={styles.feedbackBanner}>
            <Text style={styles.feedbackText}>{eventFeedback}</Text>
          </View>
        )}

        {events.map((ev) => (
          <View key={ev.id} style={styles.eventCard}>
            <View style={styles.eventHeader}>
              <View style={styles.eventTypeBadge}>
                <Text style={styles.eventTypeText}>{ev.event_type.toUpperCase()}</Text>
              </View>
              <Text style={styles.eventDate}>
                {new Date(ev.start_time).toLocaleDateString()}
              </Text>
            </View>

            <Text style={styles.eventTitle}>{ev.title}</Text>
            <Text style={styles.eventDesc}>{ev.description}</Text>
            <Text style={styles.eventLocation}>📍 {ev.location}</Text>

            <View style={styles.eventFooter}>
              <Text style={styles.seatsText}>
                {ev.available_seats} of {ev.max_capacity} seats available
              </Text>
              {ev.is_registered ? (
                <View style={styles.registeredBadge}>
                  <Text style={styles.registeredBadgeText}>✓ Registered</Text>
                </View>
              ) : (
                <TouchableOpacity
                  style={[styles.registerEventBtn, registeringEventId === ev.id && styles.buttonDisabled]}
                  onPress={() => handleRegisterEvent(ev.id)}
                  disabled={registeringEventId === ev.id || ev.available_seats <= 0}
                >
                  {registeringEventId === ev.id ? (
                    <ActivityIndicator size="small" color="#FFFFFF" />
                  ) : (
                    <Text style={styles.registerEventBtnText}>
                      {ev.available_seats > 0 ? 'Register Now' : 'Fully Booked'}
                    </Text>
                  )}
                </TouchableOpacity>
              )}
            </View>
          </View>
        ))}
      </View>

      {/* Module 5: Global Connect Regional Chapters (P1) */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Global Alumni Chapters</Text>
        <View style={styles.chaptersGrid}>
          {locations.map((loc) => (
            <View key={`${loc.country}-${loc.city}`} style={styles.chapterCard}>
              <Text style={styles.chapterCity}>{loc.city}</Text>
              <Text style={styles.chapterCountry}>{loc.country}</Text>
              <Text style={styles.chapterCount}>
                👥 {loc.alumni_count}+ verified alumni
              </Text>
              {loc.is_active_chapter && (
                <View style={styles.activeChapterBadge}>
                  <Text style={styles.activeChapterText}>Active Chapter</Text>
                </View>
              )}
            </View>
          ))}
        </View>
      </View>

      {/* Phase 4: Extended Services Hub */}
      <View style={styles.section}>
        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionTitle}>Extended Services Hub</Text>
          {unreadNotifCount > 0 && (
            <View style={styles.unreadBadge}>
              <Text style={styles.unreadBadgeText}>{unreadNotifCount} New</Text>
            </View>
          )}
        </View>

        {serviceActionFeedback && (
          <View style={styles.feedbackBanner}>
            <Text style={styles.feedbackText}>{serviceActionFeedback}</Text>
          </View>
        )}

        {/* Tab Controls */}
        <View style={styles.hubTabRow}>
          <TouchableOpacity
            style={[styles.hubTabButton, activeServicesTab === 'learning' && styles.hubTabButtonActive]}
            onPress={() => setActiveServicesTab('learning')}
          >
            <Text style={[styles.hubTabText, activeServicesTab === 'learning' && styles.hubTabTextActive]}>
              🎓 Learning
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.hubTabButton, activeServicesTab === 'communities' && styles.hubTabButtonActive]}
            onPress={() => setActiveServicesTab('communities')}
          >
            <Text style={[styles.hubTabText, activeServicesTab === 'communities' && styles.hubTabTextActive]}>
              👥 Groups
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.hubTabButton, activeServicesTab === 'notifications' && styles.hubTabButtonActive]}
            onPress={() => setActiveServicesTab('notifications')}
          >
            <Text style={[styles.hubTabText, activeServicesTab === 'notifications' && styles.hubTabTextActive]}>
              🔔 Alert ({unreadNotifCount})
            </Text>
          </TouchableOpacity>

          {(primaryRole === 'admin' || user?.roles?.includes('admin') || user?.roles?.includes('institutional_admin')) && (
            <TouchableOpacity
              style={[styles.hubTabButton, activeServicesTab === 'admin' && styles.hubTabButtonActive]}
              onPress={() => setActiveServicesTab('admin')}
            >
              <Text style={[styles.hubTabText, activeServicesTab === 'admin' && styles.hubTabTextActive]}>
                🛡️ Admin ({pendingVerifications.length})
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Tab Content: Learning */}
        {activeServicesTab === 'learning' && (
          <View style={styles.hubContentBox}>
            <Text style={styles.hubSubheader}>Course Catalog & Progress</Text>
            {userEnrollments.length > 0 && (
              <View style={styles.enrollmentSection}>
                <Text style={styles.enrollmentSectionTitle}>My Active Enrollments:</Text>
                {userEnrollments.map((enr) => (
                  <View key={enr.id} style={styles.enrollmentCard}>
                    <View style={styles.enrollmentMeta}>
                      <Text style={styles.enrollmentTitle}>{enr.course_title}</Text>
                      <Text style={styles.enrollmentStatusBadge}>
                        {enr.status.toUpperCase()} ({enr.progress_percentage}%)
                      </Text>
                    </View>
                    <View style={styles.progressBarTrack}>
                      <View style={[styles.progressBarFill, { width: `${enr.progress_percentage}%` }]} />
                    </View>
                    {enr.status !== 'completed' && (
                      <TouchableOpacity
                        style={styles.progressBtn}
                        onPress={() => handleUpdateProgress(enr.id, enr.progress_percentage)}
                        disabled={updatingEnrollmentId === enr.id}
                      >
                        <Text style={styles.progressBtnText}>
                          {updatingEnrollmentId === enr.id ? 'Saving...' : 'Mark +25% Progress'}
                        </Text>
                      </TouchableOpacity>
                    )}
                  </View>
                ))}
              </View>
            )}

            {learningCourses.slice(0, 3).map((course) => {
              const isEnrolled = userEnrollments.some((e) => e.resource_id === course.resource_id);
              return (
                <View key={course.resource_id} style={styles.courseItemCard}>
                  <View style={styles.courseItemHeader}>
                    <Text style={styles.courseItemTitle}>{course.title}</Text>
                    <Text style={styles.courseDifficultyBadge}>{course.difficulty}</Text>
                  </View>
                  <Text style={styles.courseProvider}>
                    {course.provider} • {course.target_skill} • {course.duration_hours}h
                  </Text>
                  {!isEnrolled ? (
                    <TouchableOpacity
                      style={styles.enrollBtn}
                      onPress={() => handleEnrollCourse(course.resource_id)}
                    >
                      <Text style={styles.enrollBtnText}>Enroll Free</Text>
                    </TouchableOpacity>
                  ) : (
                    <Text style={styles.alreadyEnrolledText}>✓ Enrolled</Text>
                  )}
                </View>
              );
            })}
          </View>
        )}

        {/* Tab Content: Communities */}
        {activeServicesTab === 'communities' && (
          <View style={styles.hubContentBox}>
            <Text style={styles.hubSubheader}>MSGI Guilds & Interest Groups</Text>
            {communities.map((comm) => (
              <View key={comm.id} style={styles.communityCard}>
                <View style={styles.communityHeaderRow}>
                  <Text style={styles.communityName}>{comm.name}</Text>
                  {comm.is_private && (
                    <View style={styles.privateBadge}>
                      <Text style={styles.privateBadgeText}>PRIVATE</Text>
                    </View>
                  )}
                </View>
                <Text style={styles.communityDesc}>{comm.description}</Text>
                <View style={styles.communityFooterRow}>
                  <Text style={styles.communityMembersText}>👥 {comm.member_count} Members</Text>
                  {comm.is_member ? (
                    <Text style={styles.joinedBadgeText}>✓ Member</Text>
                  ) : (
                    <TouchableOpacity
                      style={styles.joinCommBtn}
                      onPress={() => handleJoinCommunity(comm.id)}
                    >
                      <Text style={styles.joinCommBtnText}>{comm.is_private ? 'Request Access' : 'Join Group'}</Text>
                    </TouchableOpacity>
                  )}
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Tab Content: Notifications */}
        {activeServicesTab === 'notifications' && (
          <View style={styles.hubContentBox}>
            <Text style={styles.hubSubheader}>Realtime Alerts</Text>
            {notifications.length === 0 ? (
              <Text style={styles.emptyText}>No notifications at this time.</Text>
            ) : (
              notifications.slice(0, 4).map((notif) => (
                <View key={notif.id} style={[styles.notifCard, !notif.is_read && styles.notifCardUnread]}>
                  <View style={styles.notifHeader}>
                    <Text style={styles.notifTitle}>{notif.title}</Text>
                    {!notif.is_read && (
                      <TouchableOpacity
                        style={styles.markReadBtn}
                        onPress={() => handleMarkNotificationRead(notif.id)}
                      >
                        <Text style={styles.markReadBtnText}>Mark Read</Text>
                      </TouchableOpacity>
                    )}
                  </View>
                  <Text style={styles.notifMessage}>{notif.message}</Text>
                  <Text style={styles.notifTime}>{new Date(notif.created_at).toLocaleTimeString()}</Text>
                </View>
              ))
            )}
          </View>
        )}

        {/* Tab Content: Admin */}
        {activeServicesTab === 'admin' && (
          <View style={styles.hubContentBox}>
            <Text style={styles.hubSubheader}>Institutional Credential Verification</Text>
            {pendingVerifications.length === 0 ? (
              <Text style={styles.emptyText}>All verification requests have been processed.</Text>
            ) : (
              pendingVerifications.map((vReq) => (
                <View key={vReq.id} style={styles.adminReqCard}>
                  <Text style={styles.adminReqUser}>{vReq.user_name} ({vReq.user_email})</Text>
                  <Text style={styles.adminReqRole}>Requested Role: {vReq.requested_role.toUpperCase()}</Text>
                  <View style={styles.adminActionRow}>
                    <TouchableOpacity
                      style={[styles.adminBtn, styles.approveBtn]}
                      onPress={() => handleDecideVerification(vReq.id, 'approved')}
                    >
                      <Text style={styles.adminBtnText}>Approve</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.adminBtn, styles.rejectBtn]}
                      onPress={() => handleDecideVerification(vReq.id, 'rejected')}
                    >
                      <Text style={styles.adminBtnText}>Reject</Text>
                    </TouchableOpacity>
                  </View>
                </View>
              ))
            )}
          </View>
        )}
      </View>

      {/* Mentorship Request Modal Sheet */}
      {selectedMentor && (
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Request Mentorship</Text>
              <TouchableOpacity onPress={() => setSelectedMentor(null)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <Text style={styles.modalMentorName}>With {selectedMentor.full_name}</Text>
            <Text style={styles.modalMentorCompany}>{selectedMentor.headline}</Text>

            {mentorActionFeedback && (
              <View style={styles.feedbackBanner}>
                <Text style={styles.feedbackText}>{mentorActionFeedback}</Text>
              </View>
            )}

            {!mentorActionFeedback?.includes('successfully') && (
              <>
                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Mentorship Topic *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={mentorTopic}
                    onChangeText={setMentorTopic}
                    placeholder="e.g. AI Career Pathways"
                  />
                </View>

                <View style={styles.inputGroup}>
                  <Text style={styles.inputLabel}>Your Career Goal *</Text>
                  <TextInput
                    style={styles.textInput}
                    value={mentorGoal}
                    onChangeText={setMentorGoal}
                    placeholder="e.g. Prepare for ML Engineer roles in Tokyo"
                  />
                </View>

                <TouchableOpacity
                  style={[styles.submitRequestBtn, isSubmittingMentorReq && styles.buttonDisabled]}
                  onPress={handleRequestMentorship}
                  disabled={isSubmittingMentorReq}
                >
                  {isSubmittingMentorReq ? (
                    <ActivityIndicator color="#FFFFFF" />
                  ) : (
                    <Text style={styles.submitRequestBtnText}>Confirm Mentorship Request</Text>
                  )}
                </TouchableOpacity>
              </>
            )}

            <TouchableOpacity style={styles.closeBtn} onPress={() => setSelectedMentor(null)}>
              <Text style={styles.closeBtnText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      )}
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
  section: {
    marginBottom: Spacing.lg,
  },
  sectionHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.sm,
  },
  sectionTitle: {
    fontSize: Typography.fontSize.md,
    fontWeight: 'bold',
    color: Colors.text,
  },
  sectionLink: {
    fontSize: Typography.fontSize.xs,
    color: Colors.primary,
    fontWeight: 'bold',
  },
  emptyText: {
    fontSize: Typography.fontSize.xs,
    color: Colors.textSecondary,
    fontStyle: 'italic',
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
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  aiBannerCard: {
    backgroundColor: '#0F172A',
    borderRadius: BorderRadius.lg,
    padding: Spacing.md,
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
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primaryDark,
  },
  aiBannerTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  aiBannerSubtitle: {
    fontSize: 11,
    color: '#94A3B8',
    marginTop: 2,
  },
  mentorCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  mentorHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  avatarSmall: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: Colors.primaryLight,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: Spacing.sm,
  },
  avatarSmallText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.md,
  },
  mentorMeta: {
    flex: 1,
  },
  mentorName: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
  },
  mentorHeadline: {
    fontSize: 11,
    color: Colors.textSecondary,
  },
  mentorLocation: {
    fontSize: 10,
    color: Colors.textMuted,
    marginTop: 2,
  },
  scoreBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  scoreText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#15803D',
  },
  topicsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 4,
    marginTop: Spacing.sm,
  },
  topicBadge: {
    backgroundColor: '#F1F5F9',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  topicText: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  mentorFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: Spacing.xs,
  },
  slotsText: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  requestButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
  },
  requestButtonText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  eventCard: {
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    marginBottom: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.xs,
  },
  eventTypeBadge: {
    backgroundColor: '#EFF6FF',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: BorderRadius.sm,
  },
  eventTypeText: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primaryLight,
  },
  eventDate: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  eventTitle: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
  },
  eventDesc: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  eventLocation: {
    fontSize: 10,
    color: Colors.textMuted,
    marginTop: 4,
  },
  eventFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderLight,
    paddingTop: Spacing.xs,
  },
  seatsText: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  registerEventBtn: {
    backgroundColor: Colors.primary,
    paddingHorizontal: Spacing.md,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
  },
  registerEventBtnText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '600',
  },
  registeredBadge: {
    backgroundColor: '#DCFCE7',
    paddingHorizontal: Spacing.sm,
    paddingVertical: 4,
    borderRadius: BorderRadius.sm,
  },
  registeredBadgeText: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#15803D',
  },
  chaptersGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  chapterCard: {
    width: '48%',
    backgroundColor: Colors.card,
    borderRadius: BorderRadius.md,
    padding: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  chapterCity: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
  },
  chapterCountry: {
    fontSize: 10,
    color: Colors.textMuted,
  },
  chapterCount: {
    fontSize: 11,
    color: Colors.primary,
    fontWeight: '600',
    marginTop: 4,
  },
  activeChapterBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 4,
    paddingVertical: 1,
    borderRadius: BorderRadius.sm,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  activeChapterText: {
    fontSize: 9,
    color: '#92400E',
    fontWeight: 'bold',
  },
  feedbackBanner: {
    backgroundColor: '#DCFCE7',
    padding: Spacing.sm,
    borderRadius: BorderRadius.sm,
    marginBottom: Spacing.sm,
  },
  feedbackText: {
    fontSize: 11,
    color: '#15803D',
    fontWeight: '600',
  },
  modalOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: Colors.card,
    borderTopLeftRadius: BorderRadius.lg,
    borderTopRightRadius: BorderRadius.lg,
    padding: Spacing.lg,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  modalTitle: {
    fontSize: Typography.fontSize.lg,
    fontWeight: 'bold',
    color: Colors.text,
  },
  modalCloseText: {
    fontSize: Typography.fontSize.lg,
    color: Colors.textSecondary,
  },
  modalMentorName: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.primary,
    marginTop: 4,
  },
  modalMentorCompany: {
    fontSize: 11,
    color: Colors.textSecondary,
    marginBottom: Spacing.md,
  },
  inputGroup: {
    marginBottom: Spacing.sm,
  },
  inputLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: Colors.text,
    marginBottom: 2,
  },
  textInput: {
    backgroundColor: Colors.background,
    borderWidth: 1,
    borderColor: Colors.border,
    borderRadius: BorderRadius.sm,
    padding: Spacing.xs,
    fontSize: Typography.fontSize.xs,
    color: Colors.text,
  },
  submitRequestBtn: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.md,
    paddingVertical: Spacing.sm,
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  submitRequestBtnText: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: Typography.fontSize.sm,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  closeBtn: {
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    marginTop: Spacing.xs,
  },
  closeBtnText: {
    color: Colors.textSecondary,
    fontSize: Typography.fontSize.xs,
  },
  unreadBadge: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: BorderRadius.full,
  },
  unreadBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  hubTabRow: {
    flexDirection: 'row',
    backgroundColor: '#E2E8F0',
    borderRadius: BorderRadius.md,
    padding: 3,
    marginBottom: Spacing.md,
  },
  hubTabButton: {
    flex: 1,
    paddingVertical: Spacing.xs,
    alignItems: 'center',
    borderRadius: BorderRadius.sm,
  },
  hubTabButtonActive: {
    backgroundColor: '#FFFFFF',
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  hubTabText: {
    fontSize: 11,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  hubTabTextActive: {
    color: Colors.primary,
    fontWeight: 'bold',
  },
  hubContentBox: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.md,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  hubSubheader: {
    fontSize: Typography.fontSize.sm,
    fontWeight: 'bold',
    color: Colors.text,
    marginBottom: Spacing.sm,
  },
  enrollmentSection: {
    marginBottom: Spacing.md,
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.sm,
    padding: Spacing.sm,
  },
  enrollmentSectionTitle: {
    fontSize: 11,
    fontWeight: 'bold',
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  enrollmentCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: BorderRadius.sm,
    padding: Spacing.sm,
    marginBottom: Spacing.xs,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  enrollmentMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  enrollmentTitle: {
    fontSize: Typography.fontSize.xs,
    fontWeight: '600',
    color: Colors.text,
    flex: 1,
  },
  enrollmentStatusBadge: {
    fontSize: 10,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  progressBarTrack: {
    height: 6,
    backgroundColor: '#E2E8F0',
    borderRadius: 3,
    overflow: 'hidden',
    marginVertical: 4,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: '#10B981',
  },
  progressBtn: {
    backgroundColor: '#E0F2FE',
    borderRadius: BorderRadius.xs,
    paddingVertical: 3,
    paddingHorizontal: 8,
    alignSelf: 'flex-start',
    marginTop: 4,
  },
  progressBtnText: {
    fontSize: 10,
    color: '#0369A1',
    fontWeight: '600',
  },
  courseItemCard: {
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    paddingVertical: Spacing.xs,
  },
  courseItemHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  courseItemTitle: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.text,
    flex: 1,
  },
  courseDifficultyBadge: {
    fontSize: 9,
    color: '#0F766E',
    backgroundColor: '#CCFBF1',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  courseProvider: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginVertical: 2,
  },
  enrollBtn: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.xs,
    paddingVertical: 3,
    paddingHorizontal: 8,
    alignSelf: 'flex-start',
    marginTop: 2,
  },
  enrollBtnText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  alreadyEnrolledText: {
    fontSize: 10,
    color: '#10B981',
    fontWeight: 'bold',
    marginTop: 2,
  },
  communityCard: {
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
    paddingVertical: Spacing.xs,
  },
  communityHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  communityName: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.text,
    flex: 1,
  },
  privateBadge: {
    backgroundColor: '#FEF3C7',
    paddingHorizontal: 6,
    paddingVertical: 1,
    borderRadius: 4,
  },
  privateBadgeText: {
    fontSize: 9,
    color: '#92400E',
    fontWeight: 'bold',
  },
  communityDesc: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginVertical: 2,
  },
  communityFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 2,
  },
  communityMembersText: {
    fontSize: 10,
    color: Colors.textSecondary,
  },
  joinedBadgeText: {
    fontSize: 10,
    color: '#10B981',
    fontWeight: 'bold',
  },
  joinCommBtn: {
    backgroundColor: Colors.primary,
    borderRadius: BorderRadius.xs,
    paddingVertical: 2,
    paddingHorizontal: 8,
  },
  joinCommBtnText: {
    fontSize: 10,
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  notifCard: {
    paddingVertical: Spacing.xs,
    borderBottomWidth: 1,
    borderBottomColor: '#F1F5F9',
  },
  notifCardUnread: {
    backgroundColor: '#FEF9C3',
    padding: Spacing.xs,
    borderRadius: BorderRadius.xs,
    marginBottom: 4,
  },
  notifHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  notifTitle: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.text,
    flex: 1,
  },
  markReadBtn: {
    backgroundColor: '#E2E8F0',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  markReadBtnText: {
    fontSize: 9,
    color: Colors.textSecondary,
    fontWeight: '600',
  },
  notifMessage: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginVertical: 2,
  },
  notifTime: {
    fontSize: 9,
    color: '#94A3B8',
  },
  adminReqCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: BorderRadius.xs,
    padding: Spacing.xs,
    marginBottom: Spacing.xs,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  adminReqUser: {
    fontSize: Typography.fontSize.xs,
    fontWeight: 'bold',
    color: Colors.text,
  },
  adminReqRole: {
    fontSize: 10,
    color: Colors.textSecondary,
    marginVertical: 2,
  },
  adminActionRow: {
    flexDirection: 'row',
    gap: Spacing.xs,
    marginTop: 4,
  },
  adminBtn: {
    flex: 1,
    paddingVertical: 4,
    borderRadius: BorderRadius.xs,
    alignItems: 'center',
  },
  approveBtn: {
    backgroundColor: '#10B981',
  },
  rejectBtn: {
    backgroundColor: '#EF4444',
  },
  adminBtnText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
});
