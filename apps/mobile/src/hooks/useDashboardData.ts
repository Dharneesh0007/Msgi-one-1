/**
 * MSGI One — Dashboard Data & Action Hook (Phase 4 Decomposition)
 * Isolates domain API calls, loading/error states, and mutations from presentation components.
 */

import { useState, useEffect, useCallback } from 'react';
import { api } from '../lib/api';
import { UserProfileResponse, UserRole } from '../types/auth';
import {
  AlumniDirectoryItem,
  MentorProfile,
  MentorRequest,
  EventItem,
  JobOpportunity,
  RegionalLocation,
  LearningResourceItem,
  CourseEnrollmentItem,
  CommunityItem,
  NotificationRecord,
  VerificationRequestItem,
  AnnouncementItem,
  AdminSummary,
  AdminUserRoleRecord,
  ModerationReportItem,
  OperationalStatus,
  MeetingItem,
  ConversationItem,
} from '../types/business';

export function useDashboardData(
  user: UserProfileResponse | null,
  primaryRole: UserRole | 'guest',
  refreshProfile: () => Promise<void>
) {
  const [refreshing, setRefreshing] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [alumniMatches, setAlumniMatches] = useState<AlumniDirectoryItem[]>([]);
  const [mentors, setMentors] = useState<MentorProfile[]>([]);
  const [mentorRequests, setMentorRequests] = useState<MentorRequest[]>([]);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [jobs, setJobs] = useState<JobOpportunity[]>([]);
  const [locations, setLocations] = useState<RegionalLocation[]>([]);
  const [learningCourses, setLearningCourses] = useState<LearningResourceItem[]>([]);
  const [userEnrollments, setUserEnrollments] = useState<CourseEnrollmentItem[]>([]);
  const [communities, setCommunities] = useState<CommunityItem[]>([]);
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [unreadNotifCount, setUnreadNotifCount] = useState<number>(0);
  const [announcements, setAnnouncements] = useState<AnnouncementItem[]>([]);
  const [meetings, setMeetings] = useState<MeetingItem[]>([]);
  const [conversations, setConversations] = useState<ConversationItem[]>([]);

  // Admin state
  const [pendingVerifications, setPendingVerifications] = useState<VerificationRequestItem[]>([]);
  const [adminSummary, setAdminSummary] = useState<AdminSummary | null>(null);
  const [adminUsers, setAdminUsers] = useState<AdminUserRoleRecord[]>([]);
  const [adminReports, setAdminReports] = useState<ModerationReportItem[]>([]);
  const [adminStatus, setAdminStatus] = useState<OperationalStatus | null>(null);

  // Action feedback states
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [registeringEventId, setRegisteringEventId] = useState<string | null>(null);
  const [updatingEnrollmentId, setUpdatingEnrollmentId] = useState<string | null>(null);

  const isAdmin = primaryRole === 'admin' || Boolean(user?.roles?.includes('admin'));

  const loadDashboardData = useCallback(async () => {
    try {
      setLoadingData(true);
      setLoadError(null);
      const [
        alumniRes,
        mentorRes,
        mentorReqRes,
        eventRes,
        jobsRes,
        locRes,
        learnRes,
        myLearnRes,
        commRes,
        notifRes,
        unreadRes,
        annRes,
        mtgsRes,
        convsRes,
      ] = await Promise.allSettled([
        api.searchAlumni({ verified_only: true, limit: 4 }),
        api.listMentors({ student_goal: 'AI Engineer' }),
        api.getMyMentorRequests(),
        api.listEvents(),
        api.listJobs(),
        api.getGlobalLocations(),
        api.listLearningResources(),
        api.getMyLearning(),
        api.listCommunities(),
        api.getNotifications(),
        api.getUnreadNotificationCount(),
        api.getAnnouncements(),
        api.listMeetings(),
        api.listConversations(),
      ]);

      if (alumniRes.status === 'fulfilled') setAlumniMatches(alumniRes.value?.items || []);
      if (mentorRes.status === 'fulfilled') setMentors(mentorRes.value || []);
      if (mentorReqRes.status === 'fulfilled') setMentorRequests(mentorReqRes.value || []);
      if (eventRes.status === 'fulfilled') setEvents(eventRes.value || []);
      if (jobsRes.status === 'fulfilled') setJobs(jobsRes.value || []);
      if (locRes.status === 'fulfilled') setLocations(locRes.value || []);
      if (learnRes.status === 'fulfilled') setLearningCourses(learnRes.value || []);
      if (myLearnRes.status === 'fulfilled') setUserEnrollments(myLearnRes.value || []);
      if (commRes.status === 'fulfilled') setCommunities(commRes.value || []);
      if (notifRes.status === 'fulfilled') setNotifications(notifRes.value || []);
      if (unreadRes.status === 'fulfilled') setUnreadNotifCount(unreadRes.value?.unread_count || 0);
      if (annRes.status === 'fulfilled') setAnnouncements(annRes.value || []);
      if (mtgsRes.status === 'fulfilled') setMeetings(mtgsRes.value || []);
      if (convsRes.status === 'fulfilled') setConversations(convsRes.value || []);

      if (isAdmin) {
        const [vRes, sumRes, usersRes, repRes, statusRes] = await Promise.allSettled([
          api.getPendingVerifications(),
          api.getAdminSummary(),
          api.getAdminUsers(),
          api.getAdminReports(),
          api.getAdminStatus(),
        ]);
        if (vRes.status === 'fulfilled') setPendingVerifications(vRes.value || []);
        if (sumRes.status === 'fulfilled') setAdminSummary(sumRes.value || null);
        if (usersRes.status === 'fulfilled') setAdminUsers(usersRes.value || []);
        if (repRes.status === 'fulfilled') setAdminReports(repRes.value || []);
        if (statusRes.status === 'fulfilled') setAdminStatus(statusRes.value || null);
      }
    } catch (err: any) {
      setLoadError(err?.message || 'Unable to load dashboard data.');
    } finally {
      setLoadingData(false);
      setRefreshing(false);
    }
  }, [isAdmin]);

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
    setActionFeedback(null);
    try {
      await api.registerForEvent(eventId);
      setActionFeedback('Registration confirmed! Ticket code generated.');
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Registration failed.');
    } finally {
      setRegisteringEventId(null);
    }
  };

  const handleSubmitMentorRequest = async (mentorId: string, topic: string, goal: string) => {
    setActionFeedback(null);
    await api.submitMentorRequest({
      mentor_id: mentorId,
      topic,
      career_goal: goal,
    });
    setActionFeedback('Mentorship request submitted.');
    await loadDashboardData();
  };

  const handleRespondMentorRequest = async (
    requestId: string,
    status: 'accepted' | 'rejected' | 'clarification_requested' | 'cancelled',
    notes?: string
  ) => {
    setActionFeedback(null);
    try {
      await api.updateMentorRequest(requestId, status, notes);
      setActionFeedback(`Mentorship request updated (${status}).`);
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Failed to update mentorship request.');
    }
  };

  const handleEnrollCourse = async (resourceId: string) => {
    setActionFeedback(null);
    try {
      await api.enrollInCourse(resourceId);
      setActionFeedback('Successfully enrolled in course!');
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Enrollment failed.');
    }
  };

  const handleUpdateProgress = async (enrollmentId: string, currentProgress: number) => {
    setUpdatingEnrollmentId(enrollmentId);
    setActionFeedback(null);
    try {
      const nextProgress = Math.min(100, currentProgress + 25);
      await api.updateLearningProgress(enrollmentId, nextProgress);
      setActionFeedback(nextProgress === 100 ? 'Course completed!' : `Progress updated to ${nextProgress}%`);
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Progress update failed.');
    } finally {
      setUpdatingEnrollmentId(null);
    }
  };

  const handleJoinCommunity = async (communityId: string) => {
    setActionFeedback(null);
    try {
      const res = await api.joinCommunity(communityId);
      setActionFeedback(res.status === 'active' ? 'Joined community!' : 'Membership request submitted.');
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Failed to join community.');
    }
  };

  const handleMarkNotificationRead = async (notifId: string) => {
    try {
      await api.markNotificationAsRead(notifId);
      await loadDashboardData();
    } catch (err: any) {
      console.warn('Failed to mark read', err);
    }
  };

  const handleDecideVerification = async (requestId: string, decision: 'approved' | 'rejected') => {
    setActionFeedback(null);
    try {
      await api.decideVerification(requestId, decision);
      setActionFeedback(`Verification request ${decision}.`);
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Failed to decide verification.');
    }
  };

  const handleResolveReport = async (reportId: string, status: 'resolved' | 'dismissed') => {
    setActionFeedback(null);
    try {
      await api.decideAdminReport(reportId, status, `Marked ${status} by admin.`);
      setActionFeedback(`Report ${status}.`);
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Failed to update report.');
    }
  };

  const handleCreateAnnouncement = async (title: string, body: string) => {
    setActionFeedback(null);
    try {
      await api.createAnnouncement({ title, body, audience_role: 'all' });
      setActionFeedback('Institutional announcement published.');
      await loadDashboardData();
    } catch (err: any) {
      setActionFeedback(err.message || 'Failed to publish announcement.');
    }
  };

  return {
    refreshing,
    loadingData,
    loadError,
    actionFeedback,
    alumniMatches,
    mentors,
    mentorRequests,
    events,
    jobs,
    locations,
    learningCourses,
    userEnrollments,
    communities,
    notifications,
    unreadNotifCount,
    announcements,
    meetings,
    conversations,
    pendingVerifications,
    adminSummary,
    adminUsers,
    adminReports,
    adminStatus,
    registeringEventId,
    updatingEnrollmentId,
    onRefresh,
    loadDashboardData,
    handleRegisterEvent,
    handleSubmitMentorRequest,
    handleRespondMentorRequest,
    handleEnrollCourse,
    handleUpdateProgress,
    handleJoinCommunity,
    handleMarkNotificationRead,
    handleDecideVerification,
    handleResolveReport,
    handleCreateAnnouncement,
  };
}
