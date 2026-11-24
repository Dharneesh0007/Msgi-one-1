/**
 * MSGI One — Shared Authenticated API Client
 * Wraps all backend requests with Bearer JWT injection, MSGI standard envelope unwrapping,
 * timeout handling, and structured error propagation.
 */

import { Platform } from 'react-native';
import { supabase } from './supabase';
import {
  StandardEnvelope,
  UserProfileResponse,
  UserUpdateRequest,
  UserOnboardingRequest,
  PublicUserProfileResponse,
} from '../types/auth';

// Android emulator routes host machine loopback to 10.0.2.2; iOS and Web use localhost
const DEFAULT_API_BASE = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';
export const API_BASE_URL = process.env.EXPO_PUBLIC_API_URL || DEFAULT_API_BASE;

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown> | null;

  constructor(message: string, code: string = 'API_ERROR', status: number = 500, details?: Record<string, unknown> | null) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

interface RequestOptions extends RequestInit {
  timeoutMs?: number;
}

export async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { timeoutMs = 15000, ...fetchOptions } = options;

  // Retrieve current active Supabase session
  const { data: sessionData } = await supabase.auth.getSession();
  const token = sessionData.session?.access_token;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    const data: StandardEnvelope<T> = await response.json().catch(() => null);

    if (!response.ok) {
      const errorCode = data?.error?.code || `HTTP_${response.status}`;
      const errorMessage = data?.error?.message || response.statusText || 'Unknown server error occurred';
      throw new ApiError(errorMessage, errorCode, response.status, data?.error?.details);
    }

    if (data && data.status === 'error') {
      throw new ApiError(
        data.error?.message || 'Operation failed',
        data.error?.code || 'OPERATION_FAILED',
        response.status,
        data.error?.details
      );
    }

    return (data?.data ?? data) as T;
  } catch (error: any) {
    clearTimeout(timeoutId);

    if (error instanceof ApiError) {
      throw error;
    }

    if (error.name === 'AbortError') {
      throw new ApiError('Request timed out after 15 seconds', 'TIMEOUT_ERROR', 408);
    }

    throw new ApiError(
      error.message || 'Network communication error',
      'NETWORK_ERROR',
      0
    );
  }
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'GET' }),

  post: <T>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T>(endpoint: string, body?: any, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T>(endpoint: string, options?: RequestOptions) =>
    request<T>(endpoint, { ...options, method: 'DELETE' }),

  // User Profile Typed Methods
  getMyProfile: () => api.get<UserProfileResponse>('/api/v1/users/me'),
  updateMyProfile: (data: UserUpdateRequest) => api.patch<UserProfileResponse>('/api/v1/users/me', data),
  completeOnboarding: (data: UserOnboardingRequest) => api.post<UserProfileResponse>('/api/v1/users/me/onboard', data),
  getPublicProfile: (userId: string) => api.get<PublicUserProfileResponse>(`/api/v1/users/${userId}`),
  logoutSession: () => api.post<any>('/api/v1/auth/logout'),

  // Institutional Verification
  getMyVerificationStatus: () => api.get<any>('/api/v1/verifications/me'),
  submitVerificationRequest: (payload: {
    requested_role: 'alumni' | 'faculty' | 'recruiter';
    graduation_year?: number;
    degree?: string;
    department?: string;
    organization?: string;
    diploma_url?: string;
    notes?: string;
  }) => api.post<any>('/api/v1/verifications/me', payload),

  // Module 1: Alumni Network
  searchAlumni: (params: Record<string, any> = {}) => {
    const queryStr = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') queryStr.append(k, String(v));
    });
    const qs = queryStr.toString();
    return api.get<any>(`/api/v1/alumni${qs ? `?${qs}` : ''}`);
  },
  getAlumniDetails: (alumniId: string) => api.get<any>(`/api/v1/alumni/${alumniId}`),
  updateMyAlumniProfile: (payload: Record<string, any>) => api.patch<any>('/api/v1/alumni/me', payload),

  // Module 2: CareerBridge
  listJobs: (params: Record<string, any> = {}) => {
    const queryStr = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') queryStr.append(k, String(v));
    });
    const qs = queryStr.toString();
    return api.get<any[]>(`/api/v1/jobs${qs ? `?${qs}` : ''}`);
  },
  getJobDetails: (jobId: string) => api.get<any>(`/api/v1/jobs/${jobId}`),
  applyToJob: (jobId: string, payload: { resume_url?: string; cover_note?: string }) =>
    api.post<any>(`/api/v1/jobs/${jobId}/applications`, payload),
  getMyApplications: () => api.get<any[]>('/api/v1/me/applications'),

  // Module 3: MentorMatch
  listMentors: (params: Record<string, any> = {}) => {
    const queryStr = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') queryStr.append(k, String(v));
    });
    const qs = queryStr.toString();
    return api.get<any[]>(`/api/v1/mentors${qs ? `?${qs}` : ''}`);
  },
  submitMentorRequest: (payload: { mentor_id: string; topic: string; career_goal: string; message?: string }) =>
    api.post<any>('/api/v1/mentor-requests', payload),
  getMyMentorRequests: () => api.get<any[]>('/api/v1/me/mentor-requests'),
  updateMentorRequest: (requestId: string, status: string, notes?: string) =>
    api.patch<any>(`/api/v1/mentor-requests/${requestId}`, { status, mentor_notes: notes }),

  // Module 4: Events & Reunions
  listEvents: (params: Record<string, any> = {}) => {
    const queryStr = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') queryStr.append(k, String(v));
    });
    const qs = queryStr.toString();
    return api.get<any[]>(`/api/v1/events${qs ? `?${qs}` : ''}`);
  },
  registerForEvent: (eventId: string) => api.post<any>(`/api/v1/events/${eventId}/registrations`),
  getMyEventRegistrations: () => api.get<any[]>('/api/v1/me/event-registrations'),
  cancelEventRegistration: (eventId: string) => api.delete<any>(`/api/v1/events/${eventId}/registrations`),

  // Module 5: Global Alumni Connect (P1)
  getGlobalLocations: () => api.get<any[]>('/api/v1/global/locations'),
  getGlobalChapters: () => api.get<any[]>('/api/v1/global/chapters'),

  // Module 6: MSGI AI Command Centre (Phase 3)
  chatWithAI: (prompt: string, sessionId?: string) =>
    api.post<any>('/api/v1/ai/chat', { prompt, session_id: sessionId }),
  triggerAIWorkflow: (prompt: string, sessionId?: string) =>
    api.post<any>('/api/v1/ai/workflows', { prompt, session_id: sessionId }),
  getAIWorkflow: (sessionId: string) => api.get<any>(`/api/v1/ai/workflows/${sessionId}`),
  getPendingApprovals: () => api.get<any[]>('/api/v1/ai/approvals/pending'),
  decideApproval: (approvalId: string, decision: 'approved' | 'rejected', decisionNote?: string) =>
    api.post<any>(`/api/v1/ai/approvals/${approvalId}/decision`, { decision, decision_note: decisionNote }),

  // Module 9: Learning Academy (Phase 4)
  listLearningResources: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return api.get<any[]>(`/api/v1/learning/resources${qs ? `?${qs}` : ''}`);
  },
  getLearningResource: (resourceId: string) => api.get<any>(`/api/v1/learning/resources/${resourceId}`),
  enrollInCourse: (resourceId: string) => api.post<any>('/api/v1/learning/enrollments', { resource_id: resourceId }),
  getMyLearning: () => api.get<any[]>('/api/v1/learning/me'),
  updateLearningProgress: (enrollmentId: string, progressPercentage: number) =>
    api.patch<any>(`/api/v1/learning/progress/${enrollmentId}`, { progress_percentage: progressPercentage }),

  // Module 10: Communities & Groups (Phase 4)
  listCommunities: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return api.get<any[]>(`/api/v1/communities${qs ? `?${qs}` : ''}`);
  },
  getCommunity: (communityId: string) => api.get<any>(`/api/v1/communities/${communityId}`),
  joinCommunity: (communityId: string) => api.post<any>(`/api/v1/communities/${communityId}/join`),
  getMyCommunities: () => api.get<any[]>('/api/v1/communities/me'),
  moderateCommunityMembership: (communityId: string, membershipId: string, status: 'active' | 'rejected') =>
    api.patch<any>(`/api/v1/communities/${communityId}/memberships/${membershipId}`, { status }),

  // Module 12: Institutional Administration (Phase 4)
  getPendingVerifications: () => api.get<any[]>('/api/v1/admin/verifications'),
  decideVerification: (requestId: string, decision: 'approved' | 'rejected', reviewNotes?: string) =>
    api.post<any>(`/api/v1/admin/verifications/${requestId}/decision`, { decision, review_notes: reviewNotes }),
  getAdminSummary: () => api.get<any>('/api/v1/admin/summary'),
  getAdminAuditLogs: () => api.get<any[]>('/api/v1/admin/audit-logs'),
  getAdminUsers: () => api.get<any[]>('/api/v1/admin/users'),
  updateUserRoles: (userId: string, roles: string[], isVerified?: boolean) =>
    api.post<any>(`/api/v1/admin/users/${userId}/roles`, { roles, is_verified: isVerified }),
  getAdminReports: () => api.get<any[]>('/api/v1/admin/reports'),
  decideAdminReport: (reportId: string, status: 'under_review' | 'resolved' | 'dismissed', resolutionNotes?: string) =>
    api.patch<any>(`/api/v1/admin/reports/${reportId}`, { status, resolution_notes: resolutionNotes }),
  getAnnouncements: () => api.get<any[]>('/api/v1/admin/announcements'),
  createAnnouncement: (payload: { title: string; body: string; audience_role?: string }) =>
    api.post<any>('/api/v1/admin/announcements', payload),
  getAdminStatus: () => api.get<any>('/api/v1/admin/status'),

  // Realtime In-App Notifications (Phase 4)
  getNotifications: () => api.get<any[]>('/api/v1/notifications'),
  getUnreadNotificationCount: () => api.get<{ unread_count: number }>('/api/v1/notifications/unread-count'),
  markNotificationAsRead: (notificationId: string) => api.patch<any>(`/api/v1/notifications/${notificationId}/read`),
  markAllNotificationsAsRead: () => api.post<{ marked_read: number }>('/api/v1/notifications/read-all'),

  // Extended P1 Modules: Projects, Startups, Impact
  listProjects: (skill?: string) => api.get<any[]>(`/api/v1/projects${skill ? `?skill=${skill}` : ''}`),
  getProject: (projectId: string) => api.get<any>(`/api/v1/projects/${projectId}`),
  joinProject: (projectId: string) => api.post<any>(`/api/v1/projects/${projectId}/join-requests`),
  getMyProjects: () => api.get<any[]>('/api/v1/projects/me'),

  listStartups: (params: Record<string, any> = {}) => {
    const qs = new URLSearchParams(params).toString();
    return api.get<any[]>(`/api/v1/startups${qs ? `?${qs}` : ''}`);
  },
  getStartup: (startupId: string) => api.get<any>(`/api/v1/startups/${startupId}`),
  requestStartupIntro: (startupId: string, intent: string, message: string) =>
    api.post<any>(`/api/v1/startups/${startupId}/connection-requests`, { intent, message }),

  listImpactProgrammes: () => api.get<any[]>('/api/v1/impact/programmes'),
  getImpactProgramme: (programmeId: string) => api.get<any>(`/api/v1/impact/programmes/${programmeId}`),
  registerVolunteerInterest: (programmeId: string, interestNote: string) =>
    api.post<any>(`/api/v1/impact/programmes/${programmeId}/volunteer-interest`, { interest_note: interestNote }),
};
